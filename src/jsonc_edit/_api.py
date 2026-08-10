import atexit
from typing import List, Optional, Iterator
from contextlib import contextmanager

from ._daemon import DaemonManager
from ._models import Edit
from ._errors import DaemonError, JsoncParseError
from ._typing import JsonPath, JsonValue, ModificationOptions

_manager = None

def _get_daemon() -> DaemonManager:
    global _manager
    if _manager is None:
        _manager = DaemonManager()
        _manager.start()
    return _manager

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
    """
    daemon = _get_daemon()
    req = {
        "op": "modify",
        "args": {
            "text": text,
            "path": path,
            "value": value,
            "options": options or {"formattingOptions": {"insertSpaces": True, "tabSize": 2}}
        }
    }
    res = daemon.send_request(req)
    if not res["success"]:
        if res.get("type") == "ParseError":
            raise JsoncParseError(res["error"])
        raise DaemonError(res["error"])
    
    return [Edit(**e) for e in res["data"]]

def apply_edits(text: str, edits: List[Edit]) -> str:
    """
    Apply a list of edits to a JSONC text.
    """
    daemon = _get_daemon()
    req = {
        "op": "apply_edits",
        "args": {
            "text": text,
            "edits": [{"offset": e.offset, "length": e.length, "content": e.content} for e in edits]
        }
    }
    res = daemon.send_request(req)
    if not res["success"]:
        if res.get("type") == "ParseError":
            raise JsoncParseError(res["error"])
        raise DaemonError(res["error"])
        
    return res["data"]
