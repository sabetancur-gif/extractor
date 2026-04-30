"""
src/logs/logger.py
-------------------
Logging con fallback: usa rich si está disponible, stdlib logging si no.
Exporta logs a CSV o Excel. Thread-safe.
"""
from __future__ import annotations
import csv, logging, os, threading
from datetime import datetime
from typing import Any, Dict, List

try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
    _RICH = True
except ImportError:
    _RICH = False

try:
    import pandas as pd
except ImportError:
    pd = None


class LogEvent:
    def __init__(self, data): self.data = data
    def to_row(self, cols): return [self.data.get(c, "") for c in cols]


class LogManager:
    LOG_COLUMNS = [
        "timestamp","timestamp_start","timestamp_end","duration_seconds",
        "file_id","filename","step","page_number","pages_total","worker_id",
        "status","avg_sec_per_page","concurrency_count","match_query",
        "context_snippet","error_message",
    ]

    def __init__(self, log_dir="logs", log_level=logging.INFO):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.console = Console() if _RICH else None
        self.logger  = self._setup(log_level)
        self.events: List[LogEvent] = []
        self.lock = threading.Lock()

    def _setup(self, lvl):
        lg = logging.getLogger("pdf_analysis")
        lg.setLevel(lvl)
        if not lg.handlers:
            h = (RichHandler(console=self.console, show_time=False, show_path=False)
                 if _RICH else logging.StreamHandler())
            if not _RICH:
                h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            lg.addHandler(h)
        return lg

    def log(self, event: Dict[str, Any], level=logging.INFO):
        with self.lock:
            self.events.append(LogEvent(event))
        msg = f"[{event.get('step','STEP')}] {event.get('filename','')} {event.get('status','')} {event.get('error_message','')}"
        try: self.logger.log(level, msg)
        except Exception: print(f"LOG: {msg}")

    def export(self, step, fmt="csv"):
        now  = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.log_dir, f"{now}_{step}_logs.{fmt}")
        rows = [e.to_row(self.LOG_COLUMNS) for e in self.events if e.data.get("step") == step]
        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows([self.LOG_COLUMNS] + rows)
        elif fmt == "xlsx" and pd:
            pd.DataFrame(rows, columns=self.LOG_COLUMNS).to_excel(path, index=False)
        return path

    def show_panel(self, title, content):
        if _RICH and self.console: self.console.print(__import__('rich.panel', fromlist=['Panel']).Panel(content, title=title))
        else: print(f"\n=== {title} ===\n{content}")

    def show_progress(self, total, description="Processing"):
        if _RICH and self.console:
            return Progress(SpinnerColumn(), TextColumn(description), BarColumn(), TimeElapsedColumn(), console=self.console, transient=True)
        return None
