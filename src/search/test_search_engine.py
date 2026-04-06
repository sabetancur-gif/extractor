"""
Basic tests for SearchEngine and InvertedIndex.
"""
from src.search.search_engine import SearchEngine

def test_search_word():
    engine = SearchEngine()
    engine.add_pdf("doc1", "file1.pdf", ["Hello world", "Another page with world"])
    results = engine.search("world")
    assert any(r["page_number"] == 1 for r in results)
    assert any(r["page_number"] == 2 for r in results)

def test_search_phrase():
    engine = SearchEngine()
    engine.add_pdf("doc2", "file2.pdf", ["The quick brown fox jumps"])
    results = engine.search("quick brown")
    assert results

def test_search_fuzzy():
    engine = SearchEngine()
    engine.add_pdf("doc3", "file3.pdf", ["fuzzy search test"])
    results = engine.search("fuzze", fuzzy=True)
    assert results
