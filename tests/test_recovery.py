import pytest
import os
import signal
from jsonc_edit import edit, _api
from jsonc_edit._errors import DaemonCrashError

pytestmark = pytest.mark.integration

def test_auto_recovery():
    """Ensure that a crashed daemon is automatically restarted and the request succeeds."""
    source = '{\n  "status": "initial"\n}'
    
    # First edit ensures daemon is running
    result1 = edit(source, ["status"], "running")
    assert '"running"' in result1
    
    # Grab the active daemon and kill it brutally
    daemon = _api._get_daemon()
    pid = daemon.process.pid
    
    # Kill the underlying node process directly via signal (to simulate crash)
    os.kill(pid, signal.SIGKILL)
    
    # Send another edit request. The auto-retry logic in _send_request_with_retry
    # should catch the DaemonCrashError, restart the daemon, and succeed!
    result2 = edit(source, ["status"], "recovered")
    assert '"recovered"' in result2
    
    # Verify the daemon instance actually changed
    new_daemon = _api._get_daemon()
    assert daemon is not new_daemon
    assert new_daemon.process.pid != pid
