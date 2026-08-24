import os
import subprocess
from pathlib import Path
from unittest import mock
import pytest
import json
import shutil

from jsonc_edit import _runtime
from jsonc_edit._errors import RuntimeBootstrapError
from jsonc_edit._runtime import _IS_WINDOWS

def test_version_constant():
    assert isinstance(_runtime.JSONC_PARSER_VERSION, str)
    assert _runtime.JSONC_PARSER_VERSION == "3.3.1"

def test_get_cache_dir():
    expected = Path.home() / ".jsonc-edit" / "versions" / "3.3.1"
    assert _runtime.get_cache_dir() == expected

@mock.patch("jsonc_edit._runtime.shutil.which")
def test_check_prerequisites_success(mock_which):
    mock_which.return_value = "/usr/bin/mock"
    # Should not raise
    _runtime.check_prerequisites()

@mock.patch("jsonc_edit._runtime.shutil.which")
def test_check_prerequisites_missing_node(mock_which):
    def which_side_effect(cmd):
        if cmd == "node":
            return None
        return "/usr/bin/npm"
    mock_which.side_effect = which_side_effect
    
    with pytest.raises(RuntimeBootstrapError, match="requires Node.js.*'node' executable was not found"):
        _runtime.check_prerequisites()

@mock.patch("jsonc_edit._runtime._find_npm")
def test_check_prerequisites_missing_npm(mock_find_npm):
    mock_find_npm.return_value = None
    
    with pytest.raises(RuntimeBootstrapError, match="requires npm.*'npm' executable was not found"):
        _runtime.check_prerequisites()

@mock.patch("jsonc_edit._runtime.get_cache_dir")
def test_is_installed(mock_get_cache_dir, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    
    # Not installed initially
    assert not _runtime.is_installed()
    
    # Create the directory structure
    module_path = tmp_path / "node_modules" / "jsonc-parser"
    module_path.mkdir(parents=True)
    
    assert _runtime.is_installed()

@mock.patch("jsonc_edit._runtime._find_npm")
@mock.patch("jsonc_edit._runtime.subprocess.run")
@mock.patch("jsonc_edit._runtime.get_cache_dir")
def test_install_dependency_posix(mock_get_cache_dir, mock_run, mock_find_npm, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    mock_find_npm.return_value = "/usr/bin/npm"
    
    with mock.patch("jsonc_edit._runtime._IS_WINDOWS", False):
        _runtime.install_dependency()
    
    # Verify package.json
    package_json_path = tmp_path / "package.json"
    assert package_json_path.exists()
    
    with open(package_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["dependencies"]["jsonc-parser"] == "3.3.1"
    
    # Verify subprocess.run uses bare npm on POSIX
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["/usr/bin/npm", "install", "--no-audit", "--no-fund"]
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["check"] is True
    assert kwargs["timeout"] == 180

@mock.patch("jsonc_edit._runtime.install_dependency")
@mock.patch("jsonc_edit._runtime.is_installed")
@mock.patch("jsonc_edit._runtime.check_prerequisites")
def test_ensure_runtime_already_installed(mock_check, mock_is_installed, mock_install):
    mock_is_installed.return_value = True
    
    result = _runtime.ensure_runtime()
    
    mock_check.assert_called_once()
    mock_install.assert_not_called()
    assert result == _runtime.get_cache_dir() / "node_modules" / "jsonc-parser"

@mock.patch("jsonc_edit._runtime.install_dependency")
@mock.patch("jsonc_edit._runtime.is_installed")
@mock.patch("jsonc_edit._runtime.check_prerequisites")
def test_ensure_runtime_not_installed(mock_check, mock_is_installed, mock_install):
    mock_is_installed.return_value = False
    
    result = _runtime.ensure_runtime()
    
    mock_check.assert_called_once()
    mock_install.assert_called_once()
    assert result == _runtime.get_cache_dir() / "node_modules" / "jsonc-parser"

def test_npm_install_failure():
    """Verify that an npm install failure is propagated correctly."""
    with mock.patch("jsonc_edit._runtime._find_npm", return_value="/usr/bin/npm"), \
         mock.patch("jsonc_edit._runtime._IS_WINDOWS", False), \
         mock.patch("jsonc_edit._runtime.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["npm", "install"],
            stderr="npm ERR! 404 Not Found"
        )
        with pytest.raises(RuntimeBootstrapError, match="Failed to install jsonc-parser@.*: npm ERR! 404 Not Found"):
            _runtime.install_dependency()

def test_cache_corruption(tmp_path):
    """Verify that if node_modules is missing or corrupted, it reinstalls."""
    with mock.patch("jsonc_edit._runtime.get_cache_dir", return_value=tmp_path):
        assert not _runtime.is_installed()
        
        # Fake install
        module_path = tmp_path / "node_modules" / _runtime.PACKAGE_NAME
        module_path.mkdir(parents=True)
        assert _runtime.is_installed()
        
        # Corrupt cache (remove it)
        shutil.rmtree(module_path)
        assert not _runtime.is_installed()


# ---------- Windows-specific tests ----------


@mock.patch("jsonc_edit._runtime.shutil.which")
def test_find_npm_posix(mock_which):
    """On POSIX, _find_npm looks for bare 'npm'."""
    mock_which.return_value = "/usr/bin/npm"
    with mock.patch("jsonc_edit._runtime._IS_WINDOWS", False):
        result = _runtime._find_npm()
    mock_which.assert_called_once_with("npm")
    assert result == "/usr/bin/npm"


@mock.patch("jsonc_edit._runtime.shutil.which")
def test_find_npm_windows(mock_which):
    """On Windows, _find_npm looks for 'npm.cmd'."""
    mock_which.return_value = r"C:\Program Files\nodejs\npm.cmd"
    with mock.patch("jsonc_edit._runtime._IS_WINDOWS", True):
        result = _runtime._find_npm()
    mock_which.assert_called_once_with("npm.cmd")
    assert result == r"C:\Program Files\nodejs\npm.cmd"


@mock.patch("jsonc_edit._runtime.shutil.which")
def test_find_npm_not_found(mock_which):
    """_find_npm returns None when npm is not on PATH."""
    mock_which.return_value = None
    assert _runtime._find_npm() is None


@mock.patch("jsonc_edit._runtime._find_npm")
@mock.patch("jsonc_edit._runtime.subprocess.run")
@mock.patch("jsonc_edit._runtime.get_cache_dir")
def test_install_dependency_windows(mock_get_cache_dir, mock_run, mock_find_npm, tmp_path):
    """On Windows, npm is invoked via cmd.exe to avoid CreateProcess failures."""
    mock_get_cache_dir.return_value = tmp_path
    npm_path = r"C:\Program Files\nodejs\npm.cmd"
    mock_find_npm.return_value = npm_path

    with mock.patch("jsonc_edit._runtime._IS_WINDOWS", True), \
         mock.patch.dict(os.environ, {"COMSPEC": r"C:\Windows\System32\cmd.exe"}):
        _runtime.install_dependency()

    # Verify subprocess.run was called through cmd.exe
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == [
        r"C:\Windows\System32\cmd.exe",
        "/d", "/s", "/c",
        npm_path,
        "install", "--no-audit", "--no-fund",
    ]
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["check"] is True
    assert kwargs["timeout"] == 180


def test_install_dependency_npm_not_found():
    """install_dependency raises when npm cannot be located."""
    with mock.patch("jsonc_edit._runtime._find_npm", return_value=None):
        with pytest.raises(RuntimeBootstrapError, match="Cannot locate npm"):
            _runtime.install_dependency()


@mock.patch("jsonc_edit._runtime.shutil.which")
def test_check_prerequisites_windows(mock_which):
    """check_prerequisites succeeds on Windows when npm.cmd is present."""
    def which_side_effect(cmd):
        if cmd == "node":
            return r"C:\Program Files\nodejs\node.exe"
        if cmd == "npm.cmd":
            return r"C:\Program Files\nodejs\npm.cmd"
        return None
    mock_which.side_effect = which_side_effect

    with mock.patch("jsonc_edit._runtime._IS_WINDOWS", True):
        _runtime.check_prerequisites()  # should not raise
