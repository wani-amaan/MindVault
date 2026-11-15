"""
Phase 3 Document Ingestion Unit Tests
Verifies cryptographic hashing, layout extraction, text blocks, and PDF/TXT parsing.
"""
import pytest
import os
import pymupdf
from src.backend.ingestion import DocumentIngestionEngine, compute_sha256

TEST_DOC_DIR = "storage/test_docs"

@pytest.fixture
def sample_pdf():
    os.makedirs(TEST_DOC_DIR, exist_ok=True)
    pdf_path = os.path.join(TEST_DOC_DIR, "sample_paper.pdf")
    
    # Generate a lightweight PDF programmatically using pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4
    page.insert_text((50, 72), "MindVault Epistemic Framework", fontsize=18)
    page.insert_text((50, 110), "Claim 1: Beliefs require traceable empirical evidence.", fontsize=12)
    page.insert_text((50, 140), "Claim 2: Contradictions indicate an incomplete or faulty premise.", fontsize=12)
    doc.save(pdf_path)
    doc.close()
    
    yield pdf_path
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except PermissionError:
            pass

@pytest.fixture
def sample_txt():
    os.makedirs(TEST_DOC_DIR, exist_ok=True)
    txt_path = os.path.join(TEST_DOC_DIR, "sample_notes.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Section A: Quantum Mechanics Principles.\n\nSection B: Superposition and Measurement.")
    yield txt_path
    if os.path.exists(txt_path):
        try:
            os.remove(txt_path)
        except PermissionError:
            pass

def test_sha256_computation(sample_txt):
    """Test cryptographic SHA-256 calculation for deduplication."""
    hash1 = compute_sha256(sample_txt)
    hash2 = compute_sha256(sample_txt)
    assert hash1 == hash2
    assert len(hash1) == 64

def test_pdf_ingestion_and_bounding_boxes(sample_pdf):
    """Ensure PDF layout parser extracts text, page numbers, and bounding boxes."""
    engine = DocumentIngestionEngine(storage_dir=TEST_DOC_DIR)
    doc_model, blocks = engine.process_file(sample_pdf, title="Epistemic Framework Paper")

    assert doc_model.title == "Epistemic Framework Paper"
    assert doc_model.page_count == 1
    assert len(blocks) >= 2

    # Check first block contents and coordinates
    first_block = blocks[0]
    assert "MindVault" in first_block.text
    assert first_block.page_number == 1
    assert len(first_block.bbox) == 4
    assert first_block.bbox[0] >= 0

def test_txt_ingestion(sample_txt):
    """Ensure plain text files are parsed into semantic paragraph blocks."""
    engine = DocumentIngestionEngine(storage_dir=TEST_DOC_DIR)
    doc_model, blocks = engine.process_file(sample_txt)

    assert doc_model.mime_type == "text/plain"
    assert len(blocks) == 2
    assert "Section A" in blocks[0].text
    assert "Section B" in blocks[1].text
