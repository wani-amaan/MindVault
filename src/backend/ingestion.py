"""
MindVault Document Ingestion & Layout Parsing Engine
Extracts structured text, page locations, and bounding boxes while preserving provenance.
"""
import os
import hashlib
import json
from typing import List, Dict, Any, Optional
import pymupdf  # PyMuPDF FitZ
from src.backend.models import DocumentModel, generate_uuid, utc_now

def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file for identity and deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class IngestedBlock:
    """Represents a coherent extracted text block with visual and positional bounds."""
    def __init__(self, document_id: str, page_number: int, text: str, bbox: List[float]):
        self.document_id = document_id
        self.page_number = page_number
        self.text = text.strip()
        self.bbox = bbox  # [x0, y0, x1, y1] coordinates on page

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "page": self.page_number,
            "text": self.text,
            "bbox": self.bbox
        }

class DocumentIngestionEngine:
    def __init__(self, storage_dir: str = "storage/documents"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def process_file(self, file_path: str, title: Optional[str] = None) -> (DocumentModel, List[IngestedBlock]):
        """
        Parses a document (PDF/TXT), computes its cryptographic hash, 
        and extracts layout-aware text blocks with exact page coordinates.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_hash = compute_sha256(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        doc_title = title or os.path.splitext(os.path.basename(file_path))[0]
        doc_id = generate_uuid()

        blocks: List[IngestedBlock] = []

        if file_ext == ".pdf":
            doc = pymupdf.open(file_path)
            page_count = len(doc)
            for page_idx in range(page_count):
                page = doc[page_idx]
                page_num = page_idx + 1
                # Extract text blocks with layout coordinates [x0, y0, x1, y1, text, block_no, block_type]
                text_blocks = page.get_text("blocks")
                for b in text_blocks:
                    # b[4] is text, b[0:4] is bounding box, b[6] is block type (0=text, 1=image)
                    if b[6] == 0:
                        raw_text = b[4].strip()
                        if raw_text:
                            bbox = [round(coord, 2) for coord in b[:4]]
                            blocks.append(IngestedBlock(
                                document_id=doc_id,
                                page_number=page_num,
                                text=raw_text,
                                bbox=bbox
                            ))
            doc.close()
        elif file_ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            page_count = 1
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for p in paragraphs:
                blocks.append(IngestedBlock(
                    document_id=doc_id,
                    page_number=1,
                    text=p,
                    bbox=[0.0, 0.0, 0.0, 0.0]
                ))
        else:
            raise ValueError(f"Unsupported document format: {file_ext}")

        doc_model = DocumentModel(
            id=doc_id,
            title=doc_title,
            file_path=os.path.abspath(file_path),
            file_hash_sha256=file_hash,
            mime_type="application/pdf" if file_ext == ".pdf" else "text/plain",
            page_count=page_count,
            metadata_json=json.dumps({"block_count": len(blocks)})
        )

        return doc_model, blocks
