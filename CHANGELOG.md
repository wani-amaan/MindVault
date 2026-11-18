# Changelog

All notable changes to MindVault are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) |
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]
### In Progress
- Phase 8: Tauri + React frontend, Windows installer

---

## [v0.7.0-alpha] — 2026-11-18
### Added
- **Critical Thinking Engine** (`src/backend/critical_thinking.py`): heuristic fallacy scanner detecting correlation-causation confusion, unsupported logical leaps, weasel words, and circular dependency chains in the knowledge graph.
- **Belief Timeline Ledger** (`src/backend/timeline.py`): append-only audit log recording every belief state change with SHA-256 event fingerprints for tamper detection.
- **AI Research Assistant** (`src/backend/ai_assistant.py`): grounded RAG router supporting Gemini Flash (via `GEMINI_API_KEY`), Groq (via `GROQ_API_KEY`), and fully-offline fallback mode.
- `timeline_events` table added to SQLite schema in `database.py`.
- 7 new tests in `tests/test_phase7.py` — all passing.

---

## [v0.6.0-alpha] — 2026-11-15
### Added
- **Knowledge Graph Engine** (`src/backend/graph.py`): NetworkX epistemic directed graph with PageRank foundation scoring, impact cascade traversal, and Sigma.js-compatible frontend serialiser.
- 5 new tests in `tests/test_graph.py` — all passing.

---

## [v0.5.0-alpha] — 2026-11-15
### Added
- **Contradiction Detection Engine** (`src/backend/contradiction.py`): two-stage pipeline — opposing-predicate heuristic filter followed by numerical discrepancy detector, with persistent conflict registry.
- 3 new tests in `tests/test_contradiction.py` — all passing.

---

## [v0.4.0-alpha] — 2026-11-15
### Added
- **Hybrid Search Engine** (`src/backend/search.py`): ONNX-quantised FastEmbed embeddings (BGE-small-en-v1.5, 384 dims, ~85 MB RAM), cosine vector search, FTS5 keyword search, Reciprocal Rank Fusion (RRF), and evidence attachment.
- 3 new tests in `tests/test_search.py` — all passing.

---

## [v0.3.0-alpha] — 2026-11-15
### Added
- **Document Ingestion Engine** (`src/backend/ingestion.py`): PyMuPDF-based PDF/TXT parser extracting text blocks with bounding boxes and SHA-256 content fingerprints.
- 3 new tests in `tests/test_ingestion.py` — all passing.

---

## [v0.2.0-alpha] — 2026-11-15
### Added
- **Database Engine** (`src/backend/database.py`): async SQLite WAL mode, unified schema (nodes, claims, edges, evidence, contradictions, timeline_events), FTS5 full-text search index, and all CRUD operations.
- **Pydantic v2 Models** (`src/backend/models.py`): typed models for all entity types (Document, KnowledgeNode, Claim, Evidence, Contradiction, GraphEdge).
- 4 new tests in `tests/test_database.py` — all passing.

---

## [v0.1.0-alpha] — 2026-11-14
### Added
- Project foundation: MindVault repository initialised.
- System Architecture Document (`docs/SYSTEM_ARCHITECTURE_DOCUMENT.md`).
- Research & Competitive Landscape (`docs/RESEARCH_AND_COMPETITIVE_LANDSCAPE.md`).
- Architecture Decision Records (`docs/ARCHITECTURE_DECISIONS.md`): ADR-001 (Tauri), ADR-002 (SQLite WAL + FTS5), ADR-003 (ONNX embeddings).
- `README.md`, `LICENSE` (Apache 2.0), `.gitignore`, `pyproject.toml`.
- Python 3.14 virtual environment (`.venv`) with baseline packages.
- 2 foundation tests in `tests/test_foundation.py` — all passing.
