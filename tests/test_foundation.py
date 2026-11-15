"""
Phase 1 Foundation Sanity Tests
Verifies Python version, virtual environment integrity, and architectural constraints.
"""
import sys
import os

def test_python_version():
    """Ensure runtime is Python 3.12 or newer."""
    assert sys.version_info >= (3, 12), f"Expected Python >= 3.12, got {sys.version}"

def test_docs_exist():
    """Ensure core architectural and research documentation exist."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sad_path = os.path.join(base_dir, "docs", "SYSTEM_ARCHITECTURE_DOCUMENT.md")
    research_path = os.path.join(base_dir, "docs", "RESEARCH_AND_COMPETITIVE_LANDSCAPE.md")
    adr_path = os.path.join(base_dir, "docs", "ARCHITECTURE_DECISIONS.md")
    status_path = os.path.join(base_dir, "PROJECT_STATUS.md")
    
    assert os.path.isfile(sad_path), "System Architecture Document missing"
    assert os.path.isfile(research_path), "Research Landscape document missing"
    assert os.path.isfile(adr_path), "Architecture Decisions document missing"
    assert os.path.isfile(status_path), "Project Status document missing"
