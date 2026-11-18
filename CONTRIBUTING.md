# Contributing to MindVault

Thank you for your interest in contributing! This document explains how to get involved.

---

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to be respectful and constructive.

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend engine |
| Git | 2.40+ | Version control |
| Node.js | 20 LTS | Frontend (Phase 8+) |
| Rust / Cargo | stable | Tauri bundler (Phase 8+) |

### Setup

```powershell
# Clone
git clone https://github.com/<your-org>/mindvault.git
cd mindvault

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dev dependencies
pip install pytest pytest-asyncio pydantic aiosqlite pymupdf fastembed fastapi "uvicorn[standard]"
```

### Run Tests

```powershell
.venv\Scripts\python.exe -m pytest -v
```

All 36 tests must pass before submitting a pull request.

---

## Branch & Commit Conventions

| Type | Branch naming | Example |
|---|---|---|
| Feature | `feat/phase{N}-{slug}` | `feat/phase8-frontend` |
| Bug fix | `fix/{slug}` | `fix/fts5-query-escape` |
| Docs | `docs/{slug}` | `docs/api-endpoints` |
| Refactor | `refactor/{slug}` | `refactor/search-engine` |

**Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(search): add BM25 fallback when embedding model unavailable
fix(database): handle concurrent WAL writes with retry backoff
docs(readme): add hardware requirements section
```

---

## Pull Request Process

1. Fork the repository and create your feature branch from `main`.
2. Write tests covering your change — coverage must not decrease.
3. Run the full test suite: `pytest -v` — all tests must pass.
4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Submit your PR against `main` with a clear description of what changed and why.
6. Address review feedback promptly.

---

## Architecture Overview

See [`docs/SYSTEM_ARCHITECTURE_DOCUMENT.md`](docs/SYSTEM_ARCHITECTURE_DOCUMENT.md) for the full design.

Key modules in `src/backend/`:

| Module | Responsibility |
|---|---|
| `database.py` | Async SQLite WAL + FTS5 |
| `ingestion.py` | PDF/TXT document parsing |
| `search.py` | ONNX vector search + RRF |
| `contradiction.py` | Contradiction detection |
| `graph.py` | Epistemic knowledge graph |
| `critical_thinking.py` | Fallacy & reasoning scanner |
| `timeline.py` | Belief audit ledger |
| `ai_assistant.py` | Grounded RAG Q&A |
| `simulation.py` | What-if scenario sandbox |
| `main.py` | FastAPI REST gateway |

---

## Reporting Issues

Use GitHub Issues. Include:
- OS and Python version
- Steps to reproduce
- Expected vs actual behaviour
- Full traceback if applicable

---

## Security Vulnerabilities

Do **not** open a public issue. See [SECURITY.md](SECURITY.md) for responsible disclosure.
