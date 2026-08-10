import pytest
import time
from jsonc_edit._daemon import DaemonManager
from jsonc_edit._errors import DaemonError

pytestmark = pytest.mark.integration

@pytest.fixture
def daemon():
    manager = DaemonManager()
    manager.start()
    yield manager
    manager.stop()

def test_ping_pong(daemon):
    res = daemon.send_request({"op": "ping"})
    assert res == {"success": True, "data": "pong"}

def test_multiple_pings_same_process(daemon):
    for _ in range(3):
        res = daemon.send_request({"op": "ping"})
        assert res == {"success": True, "data": "pong"}

def test_unknown_operation(daemon):
    res = daemon.send_request({"op": "unknown"})
    assert res == {"success": False, "error": "Unknown operation: unknown"}

def test_process_death_detection(daemon):
    # Kill the process externally
    daemon.process.kill()
    time.sleep(0.2) # Give it a moment to die
    
    with pytest.raises(DaemonError, match="Daemon process is not running"):
        daemon.send_request({"op": "ping"})

def test_startup_failure():
    manager = DaemonManager()
    # Temporarily corrupt the runtime logic to test startup failure
    from unittest.mock import patch
    with patch("jsonc_edit._daemon.ensure_runtime", return_value="/invalid/path/that/does/not/exist"):
        with pytest.raises(DaemonError, match="Node process exited immediately.*Cannot find jsonc-parser"):
            manager.start()

def test_malformed_json_request(daemon):
    # Send a string that isn't JSON directly to stdin
    daemon.process.stdin.write("INVALID JSON\n")
    daemon.process.stdin.flush()
    
    # We should get a malformed JSON error response from the daemon
    line = daemon.process.stdout.readline()
    import json
    res = json.loads(line)
    assert res == {"success": False, "error": "Malformed JSON"}
