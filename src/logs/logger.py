"""
Logging module with rich integration and export to Excel/CSV.
Senior style, typing, docstrings, and ready for extension.
"""
from typing import Optional, Dict, Any, List
import logging
from logging import Logger
from rich.logging import RichHandler
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn, TextColumn, SpinnerColumn
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import csv
import os
import threading
try:
    import pandas as pd
except ImportError:
    pd = None

class LogEvent:
    """
    Represents a single log event for export and reporting.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def to_row(self, columns: List[str]) -> List[Any]:
        return [self.data.get(col, "") for col in columns]

class LogManager:
    """
    Manages logging, rich console, and export to Excel/CSV.
    """
    LOG_COLUMNS = [
        "timestamp", "timestamp_start", "timestamp_end", "duration_seconds",
        "file_id", "filename", "step", "page_number", "pages_total",
        "worker_id", "status", "avg_sec_per_page", "concurrency_count",
        "match_query", "context_snippet", "error_message"
    ]

    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        self.console = Console()
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.logger = self._setup_logger(log_level)
        self.events: List[LogEvent] = []
        self.lock = threading.Lock()

    def _setup_logger(self, log_level: int) -> Logger:
        logger = logging.getLogger("pdf_analysis")
        logger.setLevel(log_level)
        handler = RichHandler(console=self.console, show_time=False, show_level=True, show_path=False)
        handler.setLevel(log_level)
        logger.handlers = [handler]
        return logger

    def log(self, event: Dict[str, Any], level: int = logging.INFO):
        """
        Log an event and store for export.
        """
        with self.lock:
            self.events.append(LogEvent(event))
        msg = f"[{event.get('step', 'STEP')}] {event.get('filename', '')} {event.get('status', '')} {event.get('error_message', '')}"
        self.logger.log(level, msg)

    def export(self, step: str, fmt: str = "csv") -> str:
        """
        Export logs for a given step to CSV or Excel. Returns the file path.
        """
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{now}_{step}_logs.{fmt}"
        path = os.path.join(self.log_dir, filename)
        rows = [e.to_row(self.LOG_COLUMNS) for e in self.events if e.data.get("step") == step]
        if fmt == "csv":
            with open(path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.LOG_COLUMNS)
                writer.writerows(rows)
        elif fmt == "xlsx" and pd:
            df = pd.DataFrame(rows, columns=self.LOG_COLUMNS)
            df.to_excel(path, index=False)
        return path

    def show_panel(self, title: str, content: str):
        self.console.print(Panel(content, title=title, expand=True))

    def show_table(self, rows: List[List[Any]], columns: List[str], title: str = ""):        
        table = Table(title=title, show_lines=True)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(x) for x in row])
        self.console.print(table)

    def show_progress(self, total: int, description: str = "Processing"):
        return Progress(
            SpinnerColumn(),
            TextColumn(description),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "{task.completed}/{task.total}",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=True
        )

# Example usage:
# log_mgr = LogManager(log_dir="logs")
# log_mgr.log({"timestamp": datetime.now().isoformat(), ...}, level=logging.INFO)
# log_mgr.export("OCR", fmt="csv")
