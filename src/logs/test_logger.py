"""
Basic tests for LogManager (logging + export).
"""
import os
from logs.logger import LogManager
from datetime import datetime

def test_log_and_export(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    mgr = LogManager(log_dir=str(log_dir))
    event = {
        "timestamp": datetime.now().isoformat(),
        "timestamp_start": datetime.now().isoformat(),
        "timestamp_end": datetime.now().isoformat(),
        "duration_seconds": 1.23,
        "file_id": "file1",
        "filename": "test.pdf",
        "step": "OCR",
        "page_number": 1,
        "pages_total": 10,
        "worker_id": "w1",
        "status": "completed",
        "avg_sec_per_page": 1.23,
        "concurrency_count": 1,
        "match_query": "",
        "context_snippet": "",
        "error_message": ""
    }
    mgr.log(event)
    csv_path = mgr.export("OCR", fmt="csv")
    assert os.path.exists(csv_path)
    with open(csv_path, encoding="utf-8") as f:
        lines = f.readlines()
    assert "test.pdf" in lines[1]
