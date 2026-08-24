import os
import shutil
import subprocess
import json
from pathlib import Path

_IS_WINDOWS = os.name == "nt"

JSONC_PARSER_VERSION = "3.3.1"
PACKAGE_NAME = "jsonc-parser"
CACHE_DIR_NAME = ".jsonc-edit"

from ._errors import RuntimeBootstrapError

def _find_npm() -> str | None:
    """Return the resolved npm command for subprocess use.

    On POSIX, bare ``"npm"`` works because the shell resolves shebang
    scripts. On Windows ``npm`` is ``npm.cmd`` and ``CreateProcess`` cannot
    execute ``.cmd`` files directly, so we locate the full path to
    ``npm.cmd`` via ``shutil.which``.
    """
    npm = shutil.which("npm.cmd" if _IS_WINDOWS else "npm")
    return npm


def check_prerequisites():
    """Verify that node and npm are installed."""
    if not shutil.which("node"):
        raise RuntimeBootstrapError("jsonc_edit requires Node.js to run the underlying jsonc-parser JavaScript library, but the 'node' executable was not found.\n\nInstall Node.js and try again.")
    if _find_npm() is None:
        raise RuntimeBootstrapError("jsonc_edit requires npm to install the underlying jsonc-parser JavaScript library, but the 'npm' executable was not found.\n\nInstall npm and try again.")

def get_cache_dir() -> Path:
    """Get the path to the version-specific cache directory."""
    home = Path.home()
    return home / CACHE_DIR_NAME / "versions" / JSONC_PARSER_VERSION

def is_installed() -> bool:
    """Check if the correct version of jsonc-parser is installed in the cache."""
    cache_dir = get_cache_dir()
    module_path = cache_dir / "node_modules" / PACKAGE_NAME
    return module_path.is_dir()

def install_dependency():
    """Install the pinned jsonc-parser version into the cache directory."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Write package.json to ensure deterministic local install
    package_json_path = cache_dir / "package.json"
    package_json = {
        "name": "jsonc-edit-runtime-cache",
        "version": "1.0.0",
        "private": True,
        "dependencies": {
            PACKAGE_NAME: JSONC_PARSER_VERSION
        }
    }
    
    with open(package_json_path, "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2)
    
    # Run npm install deterministically.
    # On Windows, bare ``npm`` resolves to ``npm.cmd`` which CreateProcess
    # cannot execute directly, so we route through cmd.exe.
    npm_cmd = _find_npm()
    if npm_cmd is None:
        raise RuntimeBootstrapError(
            f"Cannot locate npm to install {PACKAGE_NAME}@{JSONC_PARSER_VERSION}."
        )

    if _IS_WINDOWS:
        comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        cmd = [comspec, "/d", "/s", "/c", npm_cmd, "install", "--no-audit", "--no-fund"]
    else:
        cmd = [npm_cmd, "install", "--no-audit", "--no-fund"]

    try:
        subprocess.run(
            cmd,
            cwd=str(cache_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeBootstrapError(f"Failed to install {PACKAGE_NAME}@{JSONC_PARSER_VERSION}: {e.stderr}")

def ensure_runtime() -> Path:
    """Ensure the runtime dependency is installed and return its node_modules path."""
    cache_base = Path.home() / CACHE_DIR_NAME
    cache_base.mkdir(parents=True, exist_ok=True)
    lock_file = cache_base / ".install.lock"
    
    with open(lock_file, "w") as f:
        if os.name != "nt":
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            check_prerequisites()
            if not is_installed():
                install_dependency()
        finally:
            if os.name != "nt":
                import fcntl
                fcntl.flock(f, fcntl.LOCK_UN)
        
    return get_cache_dir() / "node_modules" / PACKAGE_NAME
