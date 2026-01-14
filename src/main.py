import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.status import Status

from src.ingest import ingest_pdf
from src.retriever import KeywordRetriever
from src.agent import ExtractionAgent
from src.schema import Section

console = Console()

# Configuration: What we want to know
TARGET_SECTIONS = {
    "Indications": "What diseases or conditions is this drug indicated to treat?",
    "Dosage": "What is the recommended dosage and schedule?",
    "Contraindications": "Who should NOT take this drug? List contraindications.",
    "Warnings": "What are the most serious warnings or boxed warnings?"
}

def main():
    parser = argparse.ArgumentParser(description="FDA Molecule Intelligence Agent")
    parser.add_argument("pdf_path", help="Path to the FDA label PDF")
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        console.print(f"[bold red]File not found: {pdf_path}[/bold red]")
        sys.exit(1)

    # Ingest PDF
    with console.status(f"[bold green]Ingesting {pdf_path.name}...[/bold green]"):
        chunks = ingest_pdf(pdf_path)
    console.print(f"✅ Ingested [bold]{len(chunks)}[/bold] text chunks.")

    # Set up retriever
    retriever = KeywordRetriever(chunks)
    agent = ExtractionAgent(model_name="qwen2:1.5b") # Loads model (might take a second)
    
    sections = []

    #Extraction loop
    console.print("\n[bold blue]Starting Extraction Pipeline...[/bold blue]")
    
    for title, question in TARGET_SECTIONS.items():
        console.print(f"  🔍 Analyzing: [cyan]{title}[/cyan]...")
        
        # Retrieve relevant chunks
        relevant_chunks = retriever.retrieve(title + " " + question, top_k=3)
        
        section_facts = []
        
        # Extract from each chunk
        for chunk in relevant_chunks:
            fact = agent.extract_fact(chunk, question)
            if fact and fact.value != "NOT_FOUND":
                section_facts.append(fact)
                # Optimization: If we found a high confidence fact, maybe stop? 
                # For now, we collect all and let the user see them.

        # C. Create Section Object
        # In a real app, we would deduplicate facts here.
        section = Section(
            title=title,
            facts=section_facts,
            missing_info=[] if section_facts else ["No evidence found"]
        )
        sections.append(section)

    # 4. Final Report
    console.print("\n")
    console.rule(f"[bold]Molecule Brief: {pdf_path.stem}[/bold]")
    
    for sec in sections:
        console.print(f"\n[bold underline]{sec.title}[/bold underline]")
        if not sec.facts:
            console.print("[italic red]No facts extracted.[/italic red]")
            continue
            
        for fact in sec.facts:
            # Color code confidence
            color = "green" if fact.confidence.value == "high" else "yellow"
            console.print(f"• {fact.value} [{color}]({fact.confidence.value})[/{color}]")
            for cit in fact.citations:
                console.print(f"  [dim]Citation (p{cit.page_number}): \"{cit.quote_snippet}\"[/dim]")

if __name__ == "__main__":
    main()
