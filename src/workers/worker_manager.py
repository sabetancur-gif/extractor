"""
WorkerManager: gestiona procesamiento concurrente de PDFs (ThreadPool/ProcessPool/asyncio configurable).
"""
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Callable, List, Dict, Any, Optional
import threading
import yaml
import os

class WorkerManager:
    def __init__(self, max_workers: Optional[int] = None, mode: str = "thread", config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.max_workers = max_workers or self.config.get("max_workers", 4)
        self.mode = mode or self.config.get("worker_mode", "thread")
        self.executor = self._get_executor()

    def _load_config(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _get_executor(self):
        if self.mode == "process":
            return ProcessPoolExecutor(max_workers=self.max_workers)
        return ThreadPoolExecutor(max_workers=self.max_workers)

    def map(self, func: Callable, jobs: List[Dict[str, Any]]) -> List[Any]:
        """
        Ejecuta func(job) para cada job en jobs, concurrentemente.
        Devuelve lista de resultados en orden de finalización.
        """
        futures = [self.executor.submit(func, job) for job in jobs]
        results = []
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({"error": str(e)})
        return results

    def shutdown(self):
        self.executor.shutdown()
