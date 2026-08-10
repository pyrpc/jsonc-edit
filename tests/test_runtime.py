import os
import subprocess
from pathlib import Path
from unittest import mock
import pytest
import json
import shutil

from jsonc_edit import _runtime
from jsonc_edit._errors import RuntimeBootstrapError

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

@mock.patch("jsonc_edit._runtime.shutil.which")
def test_check_prerequisites_missing_npm(mock_which):
    def which_side_effect(cmd):
        if cmd == "npm":
            return None
        return "/usr/bin/node"
    mock_which.side_effect = which_side_effect
    
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

@mock.patch("jsonc_edit._runtime.subprocess.run")
@mock.patch("jsonc_edit._runtime.get_cache_dir")
def test_install_dependency(mock_get_cache_dir, mock_run, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    
    _runtime.install_dependency()
    
    # Verify package.json
    package_json_path = tmp_path / "package.json"
    assert package_json_path.exists()
    
    with open(package_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["dependencies"]["jsonc-parser"] == "3.3.1"
    
    # Verify subprocess.run
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["npm", "install", "--no-audit", "--no-fund"]
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["check"] is True

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
    with mock.patch("jsonc_edit._runtime.subprocess.run") as mock_run:
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
