# MindVault — Architecture Decision Records (ADR)

This document records the key architectural and technical decisions made for MindVault, their context, rationale, and consequences.

---

## ADR-001: Desktop Framework Selection — Tauri (Rust + Webview2)

* **Date:** 2026-11-15
* **Status:** Accepted
* **Context:**
  The development machine and target baseline specification is Windows 11 with 8 GB RAM and an Intel Core i3 dual-core processor. An Electron shell typically consumes 180–300 MB of RAM at idle due to bundled Chromium.
* **Decision:**
  Adopt **Tauri** as the desktop application wrapper.
* **Consequences:**
  - *Positive:* Runtime idle memory drops from ~200 MB to ~35–50 MB using native Windows Webview2.
  - *Positive:* Leaves maximum free memory for local ONNX embeddings, SQLite FTS5 caching, and deterministic graph calculations.
  - *Trade-off:* Requires the Rust toolchain for final packaging, which will be installed when we assemble the native UI shell.

---

## ADR-002: Deterministic-First Hybrid Knowledge Architecture

* **Date:** 2026-11-15
* **Status:** Accepted
* **Context:**
  Relying solely on LLMs for graph traversal, contradiction verification, and dependency analysis introduces hallucinations, high latency, and cloud dependency.
* **Decision:**
  Split responsibilities strictly between deterministic code and AI:
  1. *Graph analysis, impact cascades, search indexing, and contradiction candidate pairing* are executed via **deterministic Python (NetworkX, SQLite FTS5, math algorithms)**.
  2. *AI (Local SLMs + Free-tier APIs)* is reserved strictly for non-deterministic language extraction, textual summarization, and semantic inference.
* **Consequences:**
  - *Positive:* 100% offline functionality for core vault navigation, graph queries, and impact analysis.
  - *Positive:* Zero hallucination on relationship paths and mathematical graph metrics.
  - *Positive:* Instant sub-millisecond graph traversals.

---

## ADR-003: On-Demand Just-In-Time Package Installation Strategy

* **Date:** 2026-11-15
* **Status:** Accepted
* **Context:**
  Installing monolithic AI/ML libraries (e.g., standard PyTorch ~2.5 GB, CUDA binaries, full Hugging Face suite) immediately would consume disk space, clutter the virtual environment, and risk memory overconsumption.
* **Decision:**
  Install dependencies strictly **on-demand per module**:
  - *Phase 1:* Lightweight foundation & testing tools (`pytest`).
  - *Phase 2:* SQLite & schema validation (`pydantic`, `aiosqlite`).
  - *Phase 3:* Document layout extraction (`pymupdf`).
  - *Phase 4:* Embeddings via lightweight ONNX (`fastembed`, $\le 90$ MB RAM).
* **Consequences:**
  - *Positive:* Keeps `.venv` lean and auditable.
  - *Positive:* Avoids premature optimization or installing unused dependencies.
