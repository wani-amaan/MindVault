# MindVault — Project Status & Live Execution Tracker

**Current Version:** `v0.7.0-alpha`  
**Active Phase:** `Phase 8: Simulation Lab, FastAPI Gateway & Windows Packaging`  
**Active Branch:** `feat/phase8-simulation-api`  
**Last Verified:** 2026-11-18  

---

## 1. Overall Phase Roadmap & Progress

| Phase | Description | Status | Progress | Key Deliverables |
| :---: | :--- | :---: | :---: | :--- |
| **01** | **Project Foundation & Architecture** | 🟢 **Completed** | 100% | SAD, Research Log, Git Branching, Clean `.venv`, Baseline Specs |
| **02** | **Database & Knowledge Vault Core** | 🟢 **Completed** | 100% | SQLite WAL, Unified Schema, CRUD Engine, FTS5 Search Index |
| **03** | **Ingestion & Reading Studio** | 🟢 **Completed** | 100% | PyMuPDF Ingestor, Bounding-Box Layout Parser, SHA-256 Provenance |
| **04** | **Hybrid Search & Evidence Engine** | 🟢 **Completed** | 100% | ONNX FastEmbed (BGE-small), Dense Cosine + RRF, Evidence Linker |
| **05** | **Contradiction & Logic Engine** | 🟢 **Completed** | 100% | Opposing-Predicate Filter, Numerical Discrepancy Detector, Conflict Registry |
| **06** | **Knowledge Graph & Impact Radar** | 🟢 **Completed** | 100% | NetworkX Epistemic Graph, PageRank Foundation Scores, Impact Cascade |
| **07** | **Critical Thinking, Timeline & AI Assistant** | 🟢 **Completed** | 100% | Fallacy Scanner, Belief Audit Ledger, Grounded RAG Router (Gemini/Groq/Offline) |
| **08** | **Simulation Lab, FastAPI Gateway & Packaging** | 🔵 **In Progress** | 0% | What-If Sandbox, REST API, Tauri+React UI, Windows Installer |

---

## 2. Test Suite Summary (27 tests — ALL PASSING)

| Test File | Tests | Status | Tag |
| :--- | :---: | :---: | :--- |
| `tests/test_foundation.py` | 2 | ✅ Pass | `v0.1.0-alpha` |
| `tests/test_database.py` | 4 | ✅ Pass | `v0.2.0-alpha` |
| `tests/test_ingestion.py` | 3 | ✅ Pass | `v0.3.0-alpha` |
| `tests/test_search.py` | 3 | ✅ Pass | `v0.4.0-alpha` |
| `tests/test_contradiction.py` | 3 | ✅ Pass | `v0.5.0-alpha` |
| `tests/test_graph.py` | 5 | ✅ Pass | `v0.6.0-alpha` |
| `tests/test_phase7.py` | 7 | ✅ Pass | `v0.7.0-alpha` |
| **TOTAL** | **27** | ✅ **27/27** | — |

Last full run: `27 passed in 28.77s` on 2026-11-18

---

## 3. Git Tags & Release History

| Tag | Phase | Description |
| :--- | :--- | :--- |
| `v0.1.0-alpha` | Phase 1 | Foundation & Architecture |
| `v0.2.0-alpha` | Phase 2 | Database & Knowledge Vault Core |
| `v0.3.0-alpha` | Phase 3 | Document Ingestion & Provenance |
| `v0.4.0-alpha` | Phase 4 | Hybrid Search & Evidence Engine |
| `v0.5.0-alpha` | Phase 5 | Contradiction Detection Engine |
| `v0.6.0-alpha` | Phase 6 | Knowledge Graph & Impact Radar |
| `v0.7.0-alpha` | Phase 7 | Critical Thinking, Timeline & AI Assistant |

---

## 4. Installed Python Packages (`.venv`)

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `pytest` | latest | Test runner |
| `pytest-asyncio` | latest | Async test support |
| `pydantic` | v2 | Data validation & models |
| `aiosqlite` | latest | Async SQLite |
| `pymupdf` | 2.1+ | PDF/text ingestion |
| `fastembed` | latest | ONNX quantized embeddings (BGE-small-en-v1.5) |
| `networkx` | latest | Epistemic knowledge graph |
| `numpy` | latest | Numerical operations |
| `onnxruntime` | latest | ONNX model inference |

---

## 5. Phase 8 Acceptance Checklist

- [ ] `src/backend/simulation.py` — What-If sandbox (clone graph, toggle assumption, cascade delta)
- [ ] `tests/test_simulation.py` — Simulation tests passing
- [ ] `src/backend/main.py` — FastAPI gateway with all 9 route groups
- [ ] `src/backend/__init__.py` — Package init
- [ ] `fastapi` + `uvicorn[standard]` installed
- [ ] Rust toolchain installed (`rustup` + `cargo`)
- [ ] Tauri + React + TypeScript frontend scaffolded
- [ ] 6 UI panels wired: Knowledge Vault, Graph Canvas, Search, Contradiction, Timeline, AI Chat
- [ ] Windows `.msi` installer produced via `npm run tauri build`
- [ ] `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md` authored
- [ ] Phase 8 branch merged to `main` with tag `v0.8.0-alpha`
