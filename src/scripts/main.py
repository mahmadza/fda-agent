import sys
import time
import argparse
from pathlib import Path
from rich.console import Console
from src.infra.ingest import ingest_pdf
from src.infra.retriever import KeywordRetriever
from src.core.agent import ExtractionAgent
from src.core.schema import Section
from src.infra.store import AuditStore
import random

from src.config import Config


console = Console()

def main():

    parser = argparse.ArgumentParser(description="FDA Molecule Intelligence Agent")
    parser.add_argument("pdf_path", help="Path to the FDA label PDF")
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        console.print(f"[bold red]File not found: {pdf_path}[/bold red]")
        sys.exit(1)

    with console.status(f"[bold green]Ingesting {pdf_path.name}...[/bold green]"):
        chunks = ingest_pdf(pdf_path)
    console.print(f"✅ Ingested [bold]{len(chunks)}[/bold] text chunks.")

    store = AuditStore()
    
    # Use the fixed seed from Config
    run_seed = Config.SEED
    model_name = Config.DEFAULT_MODEL

    run_id = store.start_run(
        filename=pdf_path.name, 
        model_name=model_name, 
        seed=run_seed
    )
    
    console.print(f"💾 Log Init. ID: [cyan]{run_id}[/cyan] | Seed: [magenta]{run_seed}[/magenta]")

    retriever = KeywordRetriever(chunks)
    
    agent = ExtractionAgent(
        model_name=model_name, 
        store=store, 
        run_id=run_id, 
        seed=run_seed
    )
    
    sections = []

    console.print("\n[bold blue]Starting Extraction Pipeline...[/bold blue]")
    
    pipeline_start = time.perf_counter()

    for title, question in Config.TARGET_SECTIONS.items():
        console.print(f"  🔍 Analyzing: [cyan]{title}[/cyan]...")
        section_start = time.perf_counter()
        
        relevant_chunks = retriever.retrieve(title + " " + question, top_k=3)
        section_facts = []
        
        for chunk in relevant_chunks:
            fact = agent.extract_fact(chunk, question)
            if fact and fact.value != "NOT_FOUND":
                section_facts.append(fact)

        section_duration = time.perf_counter() - section_start
        store.log_section_stats(run_id, title, section_duration, len(relevant_chunks))
        console.print(f"     ⏱️  Finished in [yellow]{section_duration:.2f}s[/yellow]")

        section = Section(
            title=title,
            facts=section_facts,
            missing_info=[] if section_facts else ["No evidence found"]
        )
        sections.append(section)

    total_duration = time.perf_counter() - pipeline_start
    console.print(f"\n✅ Pipeline completed in [bold green]{total_duration:.2f}s[/bold green]")

    console.print("\n")
    console.rule(f"[bold]Molecule Brief: {pdf_path.stem}[/bold]")
    
    for sec in sections:
        console.print(f"\n[bold underline]{sec.title}[/bold underline]")
        if not sec.facts:
            console.print("[italic red]No facts extracted.[/italic red]")
            continue
            
        for fact in sec.facts:
            color = "green" if fact.confidence.value == "high" else "yellow"
            console.print(f"• {fact.value} [{color}]({fact.confidence.value})[/{color}]")
            for cit in fact.citations:
                console.print(f"  [dim]Citation (p{cit.page_number}): \"{cit.quote_snippet}\"[/dim]")

if __name__ == "__main__":
    main()