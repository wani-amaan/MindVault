# MindVault — Your Personal Knowledge Debugger

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-v0.9.0--alpha-green.svg)](internal/PROJECT_STATUS.md)
[![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11_(64--bit)-lightgrey.svg)]()

MindVault is a local-first **Personal Knowledge Intelligence System** that transforms unstructured notes, research papers, and documents into a structured, verifiable, and evidence-supported knowledge graph.

It answers the core questions of personal epistemology:

- **What do I know, and why do I believe it?**
- **What empirical evidence supports or contradicts a claim?**
- **If a foundational assumption is challenged, what conclusions collapse?**
- **How has my understanding evolved over time?**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Knowledge Graph** | Automatically builds a NetworkX epistemic graph from your documents with PageRank-scored foundation nodes |
| **Hybrid Search** | Combines FastEmbed ONNX vectors (BGE-small) with SQLite FTS5 BM25 via Reciprocal Rank Fusion |
| **Contradiction Radar** | Two-stage detection — algorithmic antonym/numerical filters + NLI semantic cross-checking |
| **What-If Simulation** | Clone-and-modify sandbox that cascades assumption changes and reports downstream impact deltas |
| **Grounded AI Assistant** | Conversational Q&A strictly grounded in your vault context, with offline fallback |
| **Local-First & Private** | All data stays on your machine — zero telemetry, zero external data transfer without consent |
| **Resource-Conscious** | Runs on consumer hardware (8 GB RAM, Intel Core i3) with ≤ 1.4 GB total runtime footprint |

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| **Windows** | 10/11 (64-bit) | Target platform |
| **Python** | 3.12+ | Backend engine |
| **Node.js** | v20+ | Frontend build tooling |
| **Rust** | stable | Tauri native shell — install via [rustup](https://rustup.rs/) |

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/wani-amaan/MindVault.git
cd MindVault

# 2. Create & activate a Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -e .

# 4. Install frontend dependencies
cd mindvault-ui
npm ci
cd ..
```

### Running

Open **two terminals** (both from the repo root with the venv active):

**Terminal 1 — Backend**
```powershell
python -m src.backend.main
# FastAPI starts on http://127.0.0.1:8000
```

**Terminal 2 — Desktop UI**
```powershell
cd mindvault-ui
npm run tauri dev
# Opens the native MindVault window
```

> **Tip:** Keep the backend running while using the desktop client — the UI calls it over HTTP.

---

## 🖥 Using MindVault

1. **Add Knowledge** — Drop PDFs, Markdown, or plain-text files into the Knowledge Vault tab, or create premises manually with confidence sliders.
2. **Search** — Type natural-language queries in the Hybrid Search tab; results are ranked by combined vector + keyword relevance.
3. **Explore the Graph** — The Graph Topology tab shows centrality scores, node relationships, and evidence chains.
4. **Detect Contradictions** — The Contradiction Radar scans your vault for conflicting claims and shows severity ratings.
5. **Run Simulations** — In the What-If Sandbox, toggle an assumption's confidence and instantly see which downstream conclusions are affected.
6. **Ask the AI** — The Grounded AI Assistant answers questions using only evidence from your vault (with optional Gemini/Groq API for richer answers).

---

## 📂 Repository Structure

```
MindVault/
├── src/
│   └── backend/              # Python FastAPI engine
│       ├── main.py           #   19-route REST API gateway
│       ├── database.py       #   SQLite WAL + schema management
│       ├── ingestion.py      #   PDF/text ingestion & parsing
│       ├── search.py         #   Hybrid vector + FTS5 search
│       ├── graph.py          #   NetworkX epistemic graph
│       ├── contradiction.py  #   Conflict detection engine
│       ├── simulation.py     #   What-If sandbox
│       ├── ai_assistant.py   #   Grounded RAG assistant
│       └── ...
├── mindvault-ui/             # Tauri v2 + React 19 desktop app
│   ├── src/                  #   React components & API layer
│   └── src-tauri/            #   Rust native shell & config
├── tests/                    # 36 unit & integration tests (100% passing)
├── docs/                     # Architecture & research documentation
│   ├── SYSTEM_ARCHITECTURE_DOCUMENT.md
│   ├── ARCHITECTURE_DECISIONS.md
│   └── RESEARCH_AND_COMPETITIVE_LANDSCAPE.md
├── internal/                 # Developer-only tracking docs (not user-facing)
├── .env.example              # Template for API keys (copy to .env)
├── pyproject.toml            # Python package & dependency config
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── SECURITY.md               # Vulnerability reporting policy
└── LICENSE                   # Apache License 2.0
```

---

## 🔧 Configuration

Copy `.env.example` to `.env` and fill in any API keys you want:

```powershell
Copy-Item .env.example .env
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | No | Google Gemini Flash for AI assistant (free tier available) |
| `GROQ_API_KEY` | No | Groq LPU for faster AI inference |

> The app works **fully offline** without any API keys — the AI assistant falls back to local context-only mode.

---

## 🧪 Running Tests

```powershell
# From the repo root with the venv active
pytest tests/ -v
```

All 36 tests across 8 test suites should pass.

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `rustc` not found | Install the Rust toolchain: `rustup install stable && rustup default stable` |
| `npm` commands fail | Ensure Node.js v20+ is on PATH. Delete `node_modules/` and run `npm ci` again |
| Port 8000 already in use | Stop the other process, or change the port in `src/backend/main.py` |
| Missing `.env` variables | Copy `.env.example` → `.env` and add your keys |
| Tauri build errors | Run `rustup target add x86_64-pc-windows-msvc` |

---

## 📜 Documentation

- [System Architecture Document](docs/SYSTEM_ARCHITECTURE_DOCUMENT.md) — full technical specification
- [Architecture Decision Records](docs/ARCHITECTURE_DECISIONS.md) — design rationale log
- [Research & Competitive Landscape](docs/RESEARCH_AND_COMPETITIVE_LANDSCAPE.md) — literature review & benchmarks
- [Changelog](CHANGELOG.md) — version history
- [Contributing Guide](CONTRIBUTING.md) — how to get involved
- [Security Policy](SECURITY.md) — vulnerability reporting

---

## ⚖ License

Licensed under the [Apache License, Version 2.0](LICENSE).
