import pytest
from pathlib import Path
from src.ingest import ingest_pdf

# Mock a simple PDF or use a small real one from your 'data/raw_pdfs'
# For the CI/CD pipeline, we would create a tiny synthetic PDF here.
# For now, we assume you will drop a file named 'test_label.pdf' in data/raw_pdfs

def test_ingest_structure():
    """Checks if the ingest function returns a valid list of chunks."""
    # Create a dummy file if needed or mock fitz (omitted for brevity)
    # This is a placeholder for your first real test run.
    pass

def test_chunk_hashing():
    from src.schema import DocumentChunk
    c1 = DocumentChunk(chunk_id="", doc_name="test.pdf", page_number=1, text_content="Hello")
    c1.chunk_id = c1.compute_id()
    
    c2 = DocumentChunk(chunk_id="", doc_name="test.pdf", page_number=1, text_content="Hello")
    c2.chunk_id = c2.compute_id()
    
    assert c1.chunk_id == c2.chunk_id

