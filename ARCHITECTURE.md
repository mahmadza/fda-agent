# System Architecture: FDA Molecule Intelligence Agent

## Core Philosophy: "Trust but Verify"
Unlike standard RAG systems that rely on the LLM's internal weights, this agent uses a **Control-First** architecture. The LLM is an untrusted reasoning engine. Its outputs are only accepted if they pass a deterministic string-search verification against the source PDF.

---

## Data Flow Pipeline



### 1. Extraction Layer (Relational Storage)
- **Ingestion (`src/ingest.py`):** Converts PDF pages into clean text chunks using `pymupdf`, preserving page-level metadata.
- **Extraction & Reasoning (`src/agent.py`):** - LLM: `gemma2:2b` (Temp = 0.0) extracts facts into a JSON schema.
    - **Hallucination Guardrail:** The `QuoteVerifier` performs an exact substring match. Only verified facts enter the **Audit Store (SQLite)**.
- **Persistence (`src/store.py`):** Logs all `runs`, `interactions`, and verified `facts`.

### 2. Semantic Layer (Vector Storage) - *Week 3 Update*
- **Vectorization (`src/scripts/build_knowledge_base.py`):** - High-confidence facts are pulled from the SQLite `facts` table.
    - Text is transformed into 384-dimensional vectors using the `all-MiniLM-L6-v2` model.
- **Indexing (ChromaDB):** Stores embeddings in a persistent local store (`data/vector_store`).
    - **Traceability:** Each vector's metadata contains its original SQLite `fact_id` and `run_id`.

---

## Database Strategy: The Dual-Store Pattern

We maintain two distinct databases to balance reliability with searchability:

| Feature | Audit Store (SQLite) | Knowledge Base (ChromaDB) |
| :--- | :--- | :--- |
| **Role** | System of Record (Truth) | Semantic Search Accelerator |
| **Data Type** | Structured Rows & LLM Logs | High-Dimensional Vectors |
| **Primary Use** | Compliance, Debugging, Metrics | Conceptual Discovery (RAG) |
| **Integrity** | ACID Compliant | Approximate Nearest Neighbor |

### Schema Details
* **SQLite:** * `runs`: Extraction session metadata.
    * `facts`: Verified molecule data points + citations.
    * `interactions`: Raw prompt/response logs for audit trails.
* **ChromaDB (`fda_facts` collection):** * `document`: Combined Fact + Context string.
    * `metadata`: `{ "attribute": str, "confidence": str, "fact_id": int }`.

---

## Operational Workflow
1. **Fact Harvesting:** `python -m src.main` ⮕ Populates SQLite.
2. **Knowledge Sync:** `python -m src.scripts.build_knowledge_base` ⮕ Maps SQLite ⮕ ChromaDB.
3. **Intelligence Query:** `python -m src.scripts.query_agent` ⮕ Conceptual retrieval from ChromaDB.