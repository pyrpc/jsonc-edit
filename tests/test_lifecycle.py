import pytest
import threading
import multiprocessing
import shutil
from concurrent.futures import ThreadPoolExecutor

from jsonc_edit import modify, apply_edits, edit_session
from jsonc_edit._runtime import get_cache_dir
import jsonc_edit._api as api

pytestmark = pytest.mark.integration

def test_thread_safety():
    """Verify multiple threads can call modify without interleaving issues."""
    text = "{}"
    
    def worker(i):
        # Insert a value uniquely identified by i
        edits = modify(text, [f"key_{i}"], i)
        return edits
        
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(10)))
        
    assert len(results) == 10
    for i, edits in enumerate(results):
        assert len(edits) > 0
        new_text = apply_edits(text, edits)
        assert f'"key_{i}": {i}' in new_text

def test_context_manager_lifecycle():
    """Verify that edit_session properly shuts down the daemon."""
    # Ensure daemon is stopped first
    api._cleanup_daemon()
    assert api._manager is None
    
    with edit_session():
        edits = modify("{}", ["a"], 1)
        assert len(edits) > 0
        assert api._manager is not None
        assert api._manager.process is not None
        
    # After session, manager should be None and daemon killed
    assert api._manager is None

def _multiprocess_worker(i):
    # This runs in a separate process
    from jsonc_edit import modify
    edits = modify("{}", [f"process_{i}"], i)
    assert len(edits) > 0

def test_multiprocessing_safety():
    """Verify multiple processes can initialize the runtime concurrently."""
    # Stop the current daemon so we don't interfere
    api._cleanup_daemon()
    
    cache = get_cache_dir()
    if cache.exists():
        shutil.rmtree(cache)
        
    processes = []
    for i in range(3):
        p = multiprocessing.Process(target=_multiprocess_worker, args=(i,))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        assert p.exitcode == 0
