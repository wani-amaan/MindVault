# MindVault — Your Personal Knowledge Debugger

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-v0.1.0--alpha-green.svg)](PROJECT_STATUS.md)
[![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11_(64--bit)-lightgrey.svg)]()

MindVault is an independently installable, local-first **Personal Knowledge Intelligence System** that transforms unstructured notes, research papers, and documents into a structured, verifiable, and evidence-supported knowledge graph.

It answers the core questions of personal epistemology:
* **What do I know, and why do I believe it?**
* **What empirical evidence supports or contradicts a claim?**
* **If a foundational assumption is challenged, what conclusions collapse?**
* **How has my understanding evolved over time?**

---

## 🏛 Key Architectural Features

- **Hybrid Deterministic Architecture:** Core graph algorithms, impact tracking, and full-text search are computed deterministically (zero hallucinations); AI is reserved for semantic extraction and language synthesis.
- **Epistemic Dependency Mapping:** Quantifies how downstream conclusions rely on foundational assumptions.
- **Two-Stage Contradiction Detection:** Algorithmic filtering paired with Natural Language Inference (NLI) to flag and explain conflicting claims.
- **Resource-Conscious:** Engineered specifically for consumer hardware (Windows 10/11, 8 GB RAM, Intel Core i3) with a total runtime footprint $\le 1.4\text{ GB}$.
- **Local-First & Private:** Core knowledge storage, graph traversal, and search operate 100% offline. Zero telemetry or external data transfer without explicit consent.

---

## 📂 Repository Structure

```
MindVault/
├── docs/                                  # Architectural & scientific documentation
│   ├── SYSTEM_ARCHITECTURE_DOCUMENT.md   # Complete system architecture specification
│   ├── RESEARCH_AND_COMPETITIVE_LANDSCAPE.md # Literature review & research log
│   └── ARCHITECTURE_DECISIONS.md         # ADR registry
├── src/                                   # Application source code
│   ├── backend/                           # Python FastAPI asynchronous engine
│   └── frontend/                          # Tauri + React + Tailwind UI
├── tests/                                 # Unit, integration, and performance benchmarks
├── research/                              # Academic datasets & evaluation scripts
├── .gitignore                             # Clean repository filters
├── LICENSE                                # Apache License 2.0
├── PROJECT_STATUS.md                      # Live phase execution tracker
└── pyproject.toml                         # Python package and dependency configuration
```

---

## 🚀 Quickstart (Development Mode)

### Prerequisites
* Windows 10/11 (64-bit)
* Python 3.12+ (Installed: Python 3.14)
* Node.js v20+ (Installed: Node.js v24)

### Setup
```powershell
# Clone the repository
git clone https://github.com/your-username/MindVault.git
Set-Location MindVault

# Activate the isolated virtual environment
.\.venv\Scripts\Activate.ps1
```

---

## 📜 Documentation & Roadmap
* [System Architecture Document (SAD)](docs/SYSTEM_ARCHITECTURE_DOCUMENT.md)
* [Research, State of the Art & Benchmarks](docs/RESEARCH_AND_COMPETITIVE_LANDSCAPE.md)
* [Architecture Decision Records](docs/ARCHITECTURE_DECISIONS.md)
* [Live Phase Status & Milestones](PROJECT_STATUS.md)

---

## ⚖ License
Licensed under the [Apache License, Version 2.0](LICENSE).
