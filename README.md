# FDA Molecule Intelligence Agent

A local-first AI pipeline that extracts verified medical facts from FDA drug labels (PDFs) and indexes them into a searchable semantic knowledge base. It uses small, efficient LLMs (Gemma-2 2B) running on CPU to parse complex unstructured data into structured, cited intelligence.

## 🚀 Key Features
* **Local Privacy:** Runs entirely offline using `ollama`. No data leaves your machine.
* **Dual-Engine Storage:**
    * **Relational (SQLite):** Stores high-fidelity facts, audit trails, and performance metrics.
    * **Semantic (ChromaDB):** Enables conceptual search (e.g., "Find drugs with renal risks") using vector embeddings.
* **Hallucination Guardrails:** A deterministic `QuoteVerifier` ensures every extracted fact is backed by an exact substring match in the source text.
* **Audit Trail:** Every LLM thought, prompt, and latency metric is logged for full reproducibility.

## 🏗️ Architecture
The system follows a two-stage RAG (Retrieval-Augmented Generation) pipeline:
1. **Extraction Layer:** PDFs ⮕ LLM ⮕ SQLite (Facts + Quotes)
2. **Semantic Layer:** SQLite ⮕ Embedding Model (`all-MiniLM-L6-v2`) ⮕ ChromaDB



## 🛠️ Setup

1. **Prerequisites**
    * Python 3.10+
    * [Ollama](https://ollama.com/) installed and running.
    * Poetry (Python dependency manager).

2. **Installation**
    ```bash
    # Install dependencies via Poetry
    poetry install

    # Pull the LLM
    ollama pull gemma2:2b
    ```

3. **Usage Flow**

    **Step 1: Extract Facts**

    Process your PDFs to populate the SQLite audit store.
    ```bash
    poetry run python -m src.main data/raw_pdfs/keytruda.pdf
    ```

    **Step 2: Build Knowledge Base (New)**

    Convert extracted facts into semantic vectors for searching.
    ```bash
    poetry run python -m src.scripts.build_knowledge_base
    ```

    **Step 3: Semantic Query**

    Ask the agent conceptual questions.
    ```bash
    poetry run python -m src.scripts.query_agent
    ```

## 🛠️ Tech Stack
* **Orchestration:** Python 3.10 + Poetry
* **LLM:** Gemma-2 2B (via Ollama)
* **Databases:** SQLite (Audit/Facts), ChromaDB (Vector Store)
* **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
* **UI:** Rich (Terminal formatting)