# Changelog

All notable changes to MindVault are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) |
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [v0.9.0-alpha] — 2026-11-19
### Added
- **Tauri v2 + React 19 + TypeScript Native Windows Desktop App** (`mindvault-ui`):
  - Modern, responsive dark-mode dashboard with sidebar navigation.
  - **Knowledge Vault View:** Interactive premise node creator with confidence sliders and live SQLite list.
  - **Hybrid Search View:** FastEmbed vector + SQLite BM25 natural language search with relevance badges.
  - **Graph Topology View:** Centrality status and NetworkX graph metrics.
  - **Contradiction Radar View:** Conflict scanner and severity rating display.
  - **What-If Simulation Sandbox:** Interactive node picker with downstream cascade delta reporting.
  - **Grounded AI Assistant:** Conversational chat interface grounded strictly in vault context with offline support.
- Configured MSVC C++ Build Tools toolchain for Windows compilation and native packaging.
- Upgraded SQLite FTS5 search to support natural-language tokenization and multi-keyword queries.

---

## [v0.8.0-alpha] — 2026-11-18
### Added
- **What-If Simulation Sandbox** (`src/backend/simulation.py`): In-memory deep-copy graph simulation engine that cascades assumption modifications and computes delta impact reports without mutating the live graph.
- **FastAPI REST Gateway** (`src/backend/main.py`): 19 endpoints exposing node CRUD, ingestion, hybrid search, contradiction scanning, graph serialization, impact cascades, timeline auditing, grounded AI Q&A, and what-if simulation.
- 9 new tests in `tests/test_simulation.py` — all passing (36/36 tests passing total).

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
- **Database & Knowledge Vault Core** (`src/backend/database.py`): SQLite in Write-Ahead-Log (WAL) mode with unified schema (`knowledge_nodes`, `claims`, `graph_edges`, `source_documents`), async connection pooling via `aiosqlite`, and full CRUD operations.
- 4 new tests in `tests/test_database.py` — all passing.

---

## [v0.1.0-alpha] — 2026-11-15
### Added
- Project structure, documentation suite (SAD, System Architecture Document, Specs), and baseline environment configurations.
- 2 baseline tests in `tests/test_foundation.py` — all passing.
