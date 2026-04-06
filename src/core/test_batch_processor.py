"""
Test básico para BatchProcessor (procesamiento concurrente de PDFs).
"""
from src.core.batch_processor import BatchProcessor
from src.core.pipeline import Pipeline
from src.core.context import DocumentContext
import threading

def dummy_pipeline_run(ctx, fast_mode=False):
    ctx.pages = [{"page_number": 1, "text": "hello world"}]
    return ctx

def test_batch():
    pipeline = Pipeline.__new__(Pipeline)
    pipeline.run = dummy_pipeline_run
    batch = BatchProcessor(pipeline, max_workers=2, mode="thread")
    jobs = [{"context": DocumentContext(doc_id=f"doc{i}", file_path="f.pdf", file_name=f"f{i}.pdf")} for i in range(4)]
    results = batch.process_batch(jobs)
    assert len(results) == 4
    batch.shutdown()
