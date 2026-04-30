"""This.

BatchProcessor: procesa múltiples PDFs en paralelo usando WorkerManager y pipeline, con logging y métricas por lote.
"""
from src.workers.worker_manager import WorkerManager
from src.logs.logger import LogManager
from typing import List, Dict, Any, Callable
import time


class BatchProcessor:
    """This."""
    def __init__(self, pipeline, max_workers: int = 4, mode: str = "thread", log_mgr: LogManager = None):
        """This."""
        self.pipeline = pipeline
        self.log_mgr = log_mgr or LogManager()
        self.worker_mgr = WorkerManager(max_workers=max_workers, mode=mode)

    def process_batch(self, jobs: List[Dict[str, Any]], fast_mode: bool = False) -> List[Dict]:
        """This.

        jobs: List[Dict] con keys: file_path, file_name, doc_id
        """
        start = time.time()

        def job_fn(job):
            """This."""
            t0 = time.time()
            result = self.pipeline.run(job["context"], fast_mode=fast_mode)
            t1 = time.time()
            self.log_mgr.log({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "file_id": job["context"].doc_id,
                "filename": job["context"].file_name,
                "step": "BATCH",
                "page_number": None,
                "pages_total": len(getattr(job["context"], "pages", [])),
                "worker_id": threading.get_ident(),
                "status": "completed",
                "duration_seconds": t1 - t0,
                "avg_sec_per_page": (t1 - t0) / max(1, len(getattr(job["context"], "pages", []))),
                "concurrency_count": self.worker_mgr.max_workers,
                "match_query": None,
                "context_snippet": None,
                "error_message": None
            })
            return result
        results = self.worker_mgr.map(job_fn, jobs)
        end = time.time()
        self.log_mgr.log({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "file_id": None,
            "filename": None,
            "step": "BATCH_SUMMARY",
            "page_number": None,
            "pages_total": None,
            "worker_id": None,
            "status": "completed",
            "duration_seconds": end - start,
            "avg_sec_per_page": None,
            "concurrency_count": self.worker_mgr.max_workers,
            "match_query": None,
            "context_snippet": f"Processed {len(jobs)} PDFs in {end - start:.2f}s",
            "error_message": None
        })

        # Exportar logs y métricas automáticamente
        import json
        batch_id = time.strftime("%Y%m%d_%H%M%S")
        log_path = self.log_mgr.export("BATCH", fmt="csv")
        summary_path = self.log_mgr.export("BATCH_SUMMARY", fmt="csv")

        # Resumen global JSON
        summary_json = {
            "batch_id": batch_id,
            "total_pdfs": len(jobs),
            "total_time": end - start,
            "throughput": len(jobs) / ( end - start) if end > start else 0,
            "max_workers": self.worker_mgr.max_workers,
            "log_path": log_path,
            "summary_path": summary_path,
            "recommendation": f"Consider increasing workers to {self.worker_mgr.max_workers + 2} for higher throughput.",
        }
        json_path = f"logs/{batch_id}_batch_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_json, f, indent=2)

        # Visualización avanzada con rich
        from rich.panel import Panel
        from rich.table import Table
        from rich.console import Console
        from rich import box
        console = Console()
        console.print(Panel(f"Batch completed — throughput {summary_json['throughput']:.2f} pages/s. {summary_json['recommendation']}", title="Batch Summary", expand=True))
        # Tabla de resultados
        table = Table(title="Resultados por PDF", show_lines=True, box=box.SIMPLE)
        table.add_column("file_id")
        table.add_column("filename")
        table.add_column("duration (s)")
        table.add_column("pages")
        for job, res in zip(jobs, results):
            ctx = getattr(res, '__dict__', res)
            table.add_row(
                str(job["context"].doc_id),
                str(job["context"].file_name),
                f"{getattr(job['context'], 'logs', {}).get('duration_seconds', '?')}",
                str(len(getattr(job["context"], "pages", [])))
            )
        console.print(table)
        console.print(f"Logs exportados a: {log_path}")
        console.print(f"Resumen exportado a: {summary_path}")
        console.print(f"Resumen global JSON: {json_path}")

        # Panel de errores/warnings
        error_rows = [e.data for e in self.log_mgr.events if e.data.get("status") in ("error", "warning")]
        if error_rows:
            err_table = Table(title="Errores/Warnings", show_lines=True, box=box.SIMPLE)
            for col in self.log_mgr.LOG_COLUMNS:
                err_table.add_column(col)
            for row in error_rows:
                err_table.add_row(*[str(row.get(col, "")) for col in self.log_mgr.LOG_COLUMNS])
            console.print(err_table)
        else:
            console.print(Panel("No errors or warnings detected.", title="Errores/Warnings", expand=False))
        return results

    def shutdown(self):
        """This."""
        self.worker_mgr.shutdown()
