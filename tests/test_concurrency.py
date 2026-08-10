import pytest
import concurrent.futures
from jsonc_edit import edit

pytestmark = pytest.mark.integration

def single_thread_task(thread_id: int, iterations: int):
    # A simple TSConfig string
    source = '{\n  "compilerOptions": {\n    "strict": false\n  }\n}'
    
    for i in range(iterations):
        result = edit(source, ["compilerOptions", "strict"], True)
        assert '"strict": true' in result, f"Thread {thread_id} failed on iteration {i}: output was {result}"
        
        # Verify get_value concurrently
        from jsonc_edit import get_value
        val = get_value(result, ["compilerOptions", "strict"])
        assert val is True, f"Thread {thread_id} failed get_value on iteration {i}: output was {val}"

def test_daemon_concurrency():
    """Prove that multiple threads calling the daemon simultaneously do not interleave IPC payloads."""
    num_threads = 20
    iterations_per_thread = 50
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            futures.append(executor.submit(single_thread_task, i, iterations_per_thread))
            
        for future in concurrent.futures.as_completed(futures):
            # Will raise an exception if the thread failed
            future.result()
