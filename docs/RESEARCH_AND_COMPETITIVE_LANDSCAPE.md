# MindVault: Problem Landscape, State of the Art, and Research Log

**Document Version:** 1.0.0  
**Status:** Living Research Document  
**Maintained by:** MindVault Core Team  

---

## 1. Problem Formulation

Knowledge workers, researchers, and students face a critical breakdown between **information accumulation** and **knowledge validation**:

1. **The Passive Hoarding Problem:** Modern tools allow frictionless collection of notes, papers, and web clippings. However, collected items remain isolated text files without formal validation of their underlying claims.
2. **The Unchecked Contradiction Problem:** As personal knowledge vaults expand, conflicting claims inevitably emerge across different sources or dates. Traditional note systems provide zero automated mechanisms to detect or explain these conflicts.
3. **The Epistemic Fragility Problem:** Users cannot systematically evaluate *why* they hold a belief or what downstream conclusions depend on an assumption. When a foundational premise is disproven, the affected conclusions remain unchanged because dependency links do not exist.
4. **The Hallucination & Black-Box Risk:** Modern conversational AI systems frequently fabricate citations or smooth over factual discrepancies rather than flagging evidential gaps.

**MindVault's Core Thesis:**  
A personal knowledge system should not merely store text; it must model knowledge as an **attributed, directed graph of falsifiable claims, supported or challenged by verifiable evidence**, with computable dependency impact.

---

## 2. Comparative Analysis (Existing Solutions vs. MindVault)

| Dimension | File-Based Note Tools (e.g., Obsidian, Logseq) | Document Databases (e.g., Notion) | Standard RAG / Chatbot Tools | **MindVault (Our System)** |
| :--- | :--- | :--- | :--- | :--- |
| **Atomic Unit** | Page, paragraph, or block of markdown text | Relational database row or page | Dynamic chunk of text in a vector database | **Atomic Typed Entity (Note, Claim, Assumption, Evidence)** |
| **Relationships** | Unidirectional or bidirectional hyperlinks | Manual relational link columns | Cosine distance in embedding space | **Attributed Causal & Epistemic Edges (e.g., `DEPENDS_ON`, `CONTRADICTS`)** |
| **Contradiction Handling** | None (manual human discovery) | None | Ignored or hallucinated over by LLM | **Automated 2-Stage Contradiction Detection & Explanation** |
| **Dependency Analysis** | Graph visualization (visual nodes only, no math) | Formula rollups | None | **Graph-Theoretic Impact Radar (Reverse-dependency cascade)** |
| **Claim Verification** | None | Manual checkboxes | Opaque retrieval scores | **Structured Evidence Grading (Reliability, Polarity, Source Bounds)** |
| **Hypothesis Testing** | Manual editing | None | None | **Simulation Lab (Isolated branch sandbox for assumptions)** |
| **Execution Architecture** | Local markdown files | Proprietary cloud server | Cloud API or heavy local models | **Hybrid Local-First (Deterministic graph + local/cloud AI routing)** |

---

## 3. Original Contributions

MindVault introduces three primary contributions suitable for peer-reviewed evaluation:

### A. Epistemic Dependency Graph Formulation
A formal mathematical graph $G = (V, E)$ where nodes $V$ represent claims and assumptions with a confidence metric $c(v) \in [0, 1]$, and edges $E$ represent epistemic support or derivation. If a premise $u$ is degraded or refuted, an impact cascade algorithm propagates the confidence degradation across all reachable conclusions $w \in \text{Descendants}(u)$.

### B. Hybrid Deterministic-NLI Contradiction Disambiguation
Rather than passing an entire note library to an expensive LLM, MindVault implements a high-efficiency two-stage filter:
1. *Stage 1 (Deterministic/Embedding Filter):* Finds semantically similar propositions asserting opposing polarities or predicates.
2. *Stage 2 (Natural Language Inference):* Evaluates the candidate pair under strict context bounds, categorizing the relationship as:
   - Direct mutual exclusion
   - Numerical/measurement discrepancy
   - Temporal drift (information changed over time)
   - Scope/definitional variation

### C. Resource-Bound Desktop AI Orchestration
An architecture engineered to run on consumer hardware (dual-core CPU, $\le 8\text{ GB}$ RAM) by pairing fast local ONNX vector extraction with an asynchronous multi-provider bridge (local SLM / free cloud API), ensuring no user data is transferred without explicit consent.

---

## 4. Formal Research Log & Literature Review Tracker

This section tracks existing academic literature, benchmarks, and reproducibility experiments.

### Tracked Literature & Benchmarks

| ID | Title / Resource | Domain | Key Finding / Limitation Addressed | Relevance to MindVault |
| :--- | :--- | :--- | :--- | :--- |
| **REF-01** | FEVER (Fact Extraction and VERification) | Fact Checking / NLI | Evaluates claim verification against Wikipedia text chunks. | Used as an evaluation benchmark for MindVault's evidence retrieval engine. |
| **REF-02** | VitaminC (Schuster et al.) | Contrastive NLI & Fact Revision | Demonstrates how small factual edits flip factual consistency. | Provides baseline test pairs for our contradiction detection module. |
| **REF-03** | Knowledge Graph Question Answering (KGQA) Surveys | Graph + NLP | Shows pure vector RAG fails on multi-hop reasoning where graph traversal succeeds. | Validates MindVault's combination of NetworkX graph paths with dense retrieval. |
| **REF-04** | Formal Argumentation Frameworks (Dung, 1995) | Symbolic Logic | Formalizes abstract argumentation frameworks and defeat relations. | Informs our underlying logic for evidence polarity (`SUPPORTS` vs `REFUTES`). |

---

## 5. Experimental Protocols & Reproducibility Standards

To maintain academic rigor throughout development:
1. **No Synthetic Claims Without Grounding:** Evaluation datasets must cite open-access source documents.
2. **Benchmark Artifacts:** All test scripts, input datasets, and validation code will reside in `/research/benchmarks`.
3. **Hardware Independence:** All reported latency and memory metrics will explicitly specify the test environment (CPU, RAM, OS, batch size).
