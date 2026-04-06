"""
Test básico para WorkerManager (procesamiento concurrente).
"""
from src.workers.worker_manager import WorkerManager
import time

def dummy_job(job):
    time.sleep(0.1)
    return {"input": job["x"], "output": job["x"] ** 2}

def test_thread_pool():
    wm = WorkerManager(max_workers=2, mode="thread")
    jobs = [{"x": i} for i in range(4)]
    results = wm.map(dummy_job, jobs)
    assert all("output" in r for r in results)
    wm.shutdown()

def test_process_pool():
    wm = WorkerManager(max_workers=2, mode="process")
    jobs = [{"x": i} for i in range(4)]
    results = wm.map(dummy_job, jobs)
    assert all("output" in r for r in results)
    wm.shutdown()
