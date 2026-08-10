import json
import subprocess
import os
import threading
from pathlib import Path

from ._runtime import ensure_runtime
from ._errors import DaemonError

class DaemonManager:
    def __init__(self):
        self.process = None
        self._lock = threading.RLock()

    def start(self):
        """Start the persistent Node daemon."""
        with self._lock:
            if self.process is not None and self.process.poll() is None:
                return # Already running

            try:
                parser_path = ensure_runtime()
            except Exception as e:
                raise DaemonError(f"Failed to bootstrap runtime: {e}") from e

            daemon_js = Path(__file__).parent / "_daemon.js"
            
            try:
                self.process = subprocess.Popen(
                    ["node", str(daemon_js), str(parser_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1 # Line buffered
                )
            except Exception as e:
                raise DaemonError(f"Failed to start Node process: {e}") from e
                
            # Check if the process died immediately
            try:
                self.process.wait(timeout=0.2)
                # If wait succeeds without TimeoutExpired, process died
                stderr = self.process.stderr.read()
                self.process = None
                raise DaemonError(f"Node process exited immediately: {stderr.strip()}")
            except subprocess.TimeoutExpired:
                # Process is running normally
                pass

    def stop(self):
        """Stop the daemon gracefully."""
        with self._lock:
            if self.process:
                if self.process.poll() is None:
                    try:
                        self.process.stdin.close()
                    except Exception:
                        pass
                    try:
                        self.process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                self.process = None

    def send_request(self, request: dict) -> dict:
        """Send a JSON request to the daemon and receive exactly one JSON response."""
        with self._lock:
            if self.process is None or self.process.poll() is not None:
                raise DaemonError("Daemon process is not running")

            try:
                request_str = json.dumps(request)
                self.process.stdin.write(request_str + "\n")
                self.process.stdin.flush()
            except Exception as e:
                raise DaemonError(f"Failed to write to daemon: {e}") from e

            try:
                line = self.process.stdout.readline()
            except Exception as e:
                raise DaemonError(f"Failed to read from daemon: {e}") from e

            if not line:
                # EOF
                stderr = self.process.stderr.read()
                raise DaemonError(f"Unexpected EOF from daemon. Stderr: {stderr.strip()}")

            try:
                response = json.loads(line)
            except json.JSONDecodeError as e:
                raise DaemonError(f"Malformed JSON response from daemon: {line.strip()}") from e

            return response
