import atexit
import os
from pathlib import Path
from typing import List, Optional, Iterator, Union, Tuple
from contextlib import contextmanager

from ._daemon import DaemonManager
from ._models import Edit
from ._errors import DaemonError, JsoncParseError, DaemonCrashError
from ._typing import JsonPath, JsonValue, ModificationOptions

class _MissingType:
    def __repr__(self) -> str:
        return "<MISSING>"

MISSING = _MissingType()

_manager = None

def _get_daemon() -> DaemonManager:
    global _manager
    if _manager is None:
        _manager = DaemonManager()
        _manager.start()
    return _manager

def _send_request_with_retry(req: dict) -> dict:
    global _manager
    daemon = _get_daemon()
    try:
        return daemon.send_request(req)
    except DaemonCrashError:
        if _manager is not None:
            _manager.stop()
            _manager = None
        daemon = _get_daemon()
        return daemon.send_request(req)

@atexit.register
def _cleanup_daemon() -> None:
    global _manager
    if _manager is not None:
        _manager.stop()
        _manager = None

@contextmanager
def edit_session() -> Iterator[None]:
    """
    A context manager to ensure the daemon is cleanly shut down when finished.
    Useful for scripts that want deterministic cleanup rather than relying on atexit.
    """
    try:
        yield
    finally:
        _cleanup_daemon()

def modify(text: str, path: JsonPath, value: JsonValue, options: Optional[ModificationOptions] = None) -> List[Edit]:
    """
    Generate edits for modifying a value in a JSONC text at the given path.
    
    Path segments are interpreted literally. For example, `["foo.bar"]` targets the literal 
    property `"foo.bar"`, not a nested object `foo` with property `bar`. Array indexes can be
    targeted with integers, e.g., `["items", 0]`. Special characters like `@` or `/` are supported
    without any special escaping.
    without any special escaping.
    """
    current_value = get_value(text, path)
    if current_value is not MISSING and current_value == value:
        return []

    req = {
        "op": "modify",
        "args": {
            "text": text,
            "path": path,
            "value": value,
            "options": options or {"formattingOptions": {"insertSpaces": True, "tabSize": 2}}
        }
    }
    res = _send_request_with_retry(req)
    if not res["success"]:
        if res.get("type") == "ParseError":
            raise JsoncParseError(res["error"])
        raise DaemonError(res["error"])
    
    return [Edit(**e) for e in res["data"]]

def apply_edits(text: str, edits: List[Edit]) -> str:
    """
    Apply a list of edits to a JSONC text.
    """
    req = {
        "op": "apply_edits",
        "args": {
            "text": text,
            "edits": [{"offset": e.offset, "length": e.length, "content": e.content} for e in edits]
        }
    }
    res = _send_request_with_retry(req)
    if not res["success"]:
        if res.get("type") == "ParseError":
            raise JsoncParseError(res["error"])
        raise DaemonError(res["error"])
        
    return res["data"]

def get_value(text: str, path: JsonPath) -> Union[JsonValue, _MissingType]:
    """
    Retrieve a parsed value from the JSONC text at the given path.
    
    Returns the Python representation of the value (dict, list, str, etc.).
    If the path does not exist, returns the `MISSING` sentinel to explicitly distinguish
    from an existing `null` value.
    """
    req = {
        "op": "get_value",
        "args": {
            "text": text,
            "path": path
        }
    }
    res = _send_request_with_retry(req)
    if not res["success"]:
        if res.get("type") == "ParseError":
            raise JsoncParseError(res["error"])
        raise DaemonError(res["error"])
        
    data = res["data"]
    if not data["found"]:
        return MISSING
    return data["value"]

def edit(text: str, path: JsonPath, value: JsonValue, options: Optional[ModificationOptions] = None) -> str:
    """
    Modify a value in a JSONC text at the given path and apply the edits, returning the modified text.
    
    This is a high-level wrapper around `modify` and `apply_edits`.
    Path segments are interpreted literally. For example, `["foo.bar"]` targets the literal 
    property `"foo.bar"`. Array indexes can be targeted with integers, e.g., `["items", 0]`.
    """
    edits = modify(text, path, value, options)
    if not edits:
        return text
    return apply_edits(text, edits)

def edit_file(filepath: Union[str, Path], path: JsonPath, value: JsonValue, options: Optional[ModificationOptions] = None) -> None:
    """
    Modify a value in a JSONC file at the given path.
    
    Reads the file, applies the modification using `edit()`, and writes the changes back
    only if the content actually changed. Writing is done atomically to avoid partial writes.
    Path segments are interpreted literally (e.g., `["foo.bar"]` targets the literal property `"foo.bar"`).
    """
    filepath_obj = Path(filepath)
    text = filepath_obj.read_text(encoding="utf-8")
    
    modified_text = edit(text, path, value, options)
    
    if modified_text != text:
        tmp_filepath = filepath_obj.with_suffix(filepath_obj.suffix + ".tmp")
        try:
            tmp_filepath.write_text(modified_text, encoding="utf-8")
            os.replace(tmp_filepath, filepath_obj)
        except Exception:
            if tmp_filepath.exists():
                tmp_filepath.unlink()
            raise

def edit_many(text: str, operations: List[Tuple[JsonPath, JsonValue]], options: Optional[ModificationOptions] = None) -> str:
    """
    Apply multiple edit operations sequentially to a JSONC text.
    
    Each operation in `operations` should be a tuple of `(path, value)`.
    Operations are applied iteratively, guaranteeing that internal string offsets
    do not drift or corrupt when multiple modifications occur.
    """
    for path, value in operations:
        text = edit(text, path, value, options)
    return text
