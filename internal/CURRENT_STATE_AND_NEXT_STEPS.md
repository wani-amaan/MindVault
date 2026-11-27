# CURRENT_STATE_AND_NEXT_STEPS.md
**MindVault Project Status & Implementation Continuity Plan**
*Generated: 2026-11-21 | Target Repository: <REPO_ROOT>*

---

## 1. Executive Summary & Continuity Mandate
MindVault is an established, working desktop intelligence system. Development continues directly from the verified working codebase on Git branch `feat/phase10-installer-packaging`. All 36 automated tests across 8 test suites pass with 100% success. No code is being restarted or rewritten from scratch. All enhancements build incrementally on existing tables, services, and frontend components.

---

## 2. Verified Current State Inventory

| Area | Previous State (Audit) | Current Verified State | Classification | Remaining Work | Recommended Action |
|---|---|---|---|---|---|
| **Database & Schema** | SQLite WAL mode, basic tables for nodes, claims, edges, source_docs, timeline. | Active SQLite WAL database in `data/mindvault.db`. Schema operational with foreign keys. 36/36 tests pass. | **Working and Verified** | Differentiate raw assertions from canonical claims; add review statuses and temporal fields. | Add non-destructive backward-compatible columns to `claims` and a `canonical_claims` entity. |
| **Ingestion Engine** | PyMuPDF extracts text blocks, bounding boxes, SHA-256 for PDF/TXT. | `src/backend/ingestion.py` operational. Handles single files via backend API. | **Working and Verified** | OCR for scanned PDFs, multi-file batch ingestion, frontend UI drag-and-drop dropzone. | Integrate OCR fallback and expose a clean file upload/drop endpoint for the desktop UI. |
| **Claim Extraction** | `ClaimModel` defined with SVO and modality; extraction from text not automated. | Models in `src/backend/models.py`. Only manual node insertion active in UI. | **Partially Implemented** | Automated SVO + modality + temporal scope extraction from ingested document passages. | Implement lightweight hybrid dependency parser in `src/backend/ingestion.py` with review queue. |
| **Hybrid Search** | FastEmbed ONNX BGE-small (384d) + SQLite FTS5 BM25 with Reciprocal Rank Fusion. | `src/backend/search.py` operational. Verified with multi-word queries in UI and backend. | **Working and Verified** | Search across claims table in addition to raw node passages. | Extend RRF to aggregate claim-level matches alongside document passage matches. |
| **Contradiction Detection** | Rule-based antonym and numerical difference checks in `src/backend/contradiction.py`. | Functional for explicit antonyms and numbers; fails on temporal evolution or contextual scope. | **Partially Implemented** | Temporal/contextual scoping, NLI semantic cross-checking, persistence of conflict records. | Upgrade with multi-stage filter (temporal check before conflict flag) and persist conflicts in DB. |
| **Knowledge Graph** | NetworkX DiGraph, PageRank centrality, BFS impact cascade, Sigma.js serialization. | `src/backend/graph.py` operational. Graph rebuilds dynamically on node mutations. | **Working and Verified** | Automatic relationship proposal, approval queue, and visual canvas in UI. | Add automated edge proposal on claim ingestion with PENDING_REVIEW state. |
| **Epistemic Simulation** | What-If sandbox clones DiGraph, toggles confidence, reports PageRank score deltas. | `src/backend/simulation.py` operational with 9 dedicated unit tests passing. | **Working and Verified** | Causal dependency propagation (PageRank measures centrality, not logical truth collapse). | Add epistemic truth-propagation mode alongside existing structural PageRank analysis. |
| **External Fact Verification** | Not implemented. | Only internal document context used. | **Missing** | Verify claims against Wikipedia, PTI, and credible sources; retrieve grounding citations. | Create `src/backend/external_verification.py` integrated directly into existing claim models. |
| **PDF Reading Workspace** | Backend PyMuPDF extracts bounding boxes; no UI reader or drag-and-drop. | UI has Knowledge Vault, Search, Graph, Contradiction, Sim, Chat. No PDF viewer. | **Partially Implemented** | "Add Content" dropdown, drag-and-drop zone, PDF viewer with highlight-to-claim creation. | Add PDF Dropzone & Library panel into `mindvault-ui` using existing FastAPI ingest route. |
| **Grounded AI Assistant** | Grounded prompt enforcing node citations, Gemini/Groq router, offline fallback. | `src/backend/ai_assistant.py` operational. Verified with strict offline fallback citing IDs. | **Working and Verified** | Grounding over claims and external verification reports in addition to raw nodes. | Extend context builder to incorporate claim verification badges and source links. |
| **Windows Desktop Packaging** | Tauri v2 React 19 UI running locally via dev mode; MSVC toolchain configured. | `mindvault-ui` runs as native Windows window connecting to FastAPI on 8765. | **Working and Verified** | Standalone installer (`.msi` / setup executable) bundling backend runtime. | Package application using `npm run tauri build` in Phase 10. |

---

## 3. Dependency Map of Remaining Enhancements

```
[1. Knowledge Architecture Evolution (Assertions vs Canonical Claims)]
                         │
                         ▼
[2. Automated Claim & Provenance Extraction (Ingestion Upgrade)]
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
[3. Internal Contradiction]     [4. External Factual Verification]
  (Temporal/Context Filter)       (Wikipedia / PTI / Grounded Sources)
         │                               │
         └───────────────┬───────────────┘
                         ▼
[5. Evidence Intelligence & Epistemic Truth Simulation]
  (Separate Centrality from Factual Truth Probability)
                         │
                         ▼
[6. PDF Reading Workspace & Drag-and-Drop Dropzone in UI]
                         │
                         ▼
[7. Final Polish, Testing & Windows Installer Packaging (.msi)]
```

---

## 4. Immediate Milestone: Milestone 1 — Knowledge Architecture Evolution & Automated Claim Extraction
- **Objective:** Extend schema non-destructively to support raw source assertions vs. canonical claims with review states (`PENDING_REVIEW`, `APPROVED`), temporal scope, and context qualifiers.
- **Safety Guarantee:** Existing `knowledge_nodes` and `data/mindvault.db` preserved completely; all 36 tests remain passing.
