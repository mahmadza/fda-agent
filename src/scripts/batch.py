import time
import argparse
from pathlib import Path
from rich.console import Console

from src.infra.ingest import ingest_pdf
from src.infra.retriever import KeywordRetriever
from src.core.agent import ExtractionAgent
from src.infra.store import AuditStore

from src.config import Config

console = Console()

def process_one_file(
        pdf_path: Path,
        model_name: str,
        store: AuditStore
    ):
    """Process a single PDF file for fact extraction."""

    # Check if already done
    conn = store._get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT run_id FROM runs WHERE filename = ? AND model_name = ?", 
        (pdf_path.name, model_name)
    )
    existing = cursor.fetchone()
    conn.close()
    
    if existing:
        console.print(f"[dim]Skipping {pdf_path.name} (Already processed in run {existing[0]})[/dim]")
        return

    # Ingest
    console.print(f"[bold blue]Processing {pdf_path.name}...[/bold blue]")
    try:
        chunks = ingest_pdf(pdf_path)
    except Exception as e:
        console.print(f"[red]Failed to ingest {pdf_path.name}: {e}[/red]")
        return

    # Setup agent
    retriever = KeywordRetriever(chunks)
    run_id = store.start_run(filename=pdf_path.name, model_name=model_name)
    agent = ExtractionAgent(model_name=model_name, store=store, run_id=run_id)
    
    # Extract (Silent Mode - no huge printouts)
    start_time = time.perf_counter()
    
    for title, question in Config.TARGET_SECTIONS.items():
        section_start = time.perf_counter()
        relevant_chunks = retriever.retrieve(title + " " + question, top_k=3)
        
        for chunk in relevant_chunks:
            agent.extract_fact(chunk, question)
            
        duration = time.perf_counter() - section_start
        store.log_section_stats(run_id, title, duration, len(relevant_chunks))
        console.print(f"  - {title}: {duration:.1f}s")

    total_time = time.perf_counter() - start_time
    console.print(f"✅ Finished {pdf_path.name} in {total_time:.1f}s\n")

def batch_process(folder_path: Path, model_name: str):
    """Process all PDF files in a given folder."""
    store = AuditStore()
    files = list(folder_path.glob("*.pdf"))
    
    if not files:
        console.print(f"[red]No PDFs found in {folder_path}[/red]")
        return

    console.print(f"Found {len(files)} PDFs. Starting Batch Job...")
    
    for pdf_file in files:
        process_one_file(pdf_file, model_name, store)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="Folder containing PDFs")
    parser.add_argument("--model", default=Config.DEFAULT_MODEL, help="Model to use")
    args = parser.parse_args()
    
    batch_process(Path(args.folder), args.model)