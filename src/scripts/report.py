import sys
import argparse
import sqlite3
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.config import Config

console = Console()

def get_latest_run_id(db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT run_id, filename, created_at FROM runs ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row

def generate_report(db_path: Path, run_id: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch Run Info
    cursor.execute("SELECT filename, model_name, created_at FROM runs WHERE run_id = ?", (run_id,))
    run_meta = cursor.fetchone()
    
    if not run_meta:
        console.print(f"[red]Run ID {run_id} not found.[/red]")
        return

    filename, model, created_at = run_meta
    
    console.rule(f"[bold]Molecule Brief: {filename}[/bold]")
    console.print(f"[dim]Run ID: {run_id} | Model: {model} | Date: {created_at}[/dim]\n")

    # Fetch Facts grouped by Attribute (Question)
    cursor.execute("""
        SELECT attribute, value, citation_quote, chunk_page, confidence 
        FROM facts 
        WHERE run_id = ? 
        ORDER BY id ASC
    """, (run_id,))
    
    facts = cursor.fetchall()
    
    if not facts:
        console.print("[italic red]No verified facts found for this run.[/italic red]")
        return

    # Group by "Section" (Attribute)
    current_section = None
    for attribute, value, quote, page, confidence in facts:
        # Simple heuristic: The attribute usually maps to the section title
        if attribute != current_section:
            console.print(f"\n[bold underline]{attribute}[/bold underline]")
            current_section = attribute
        
        color = "green" if confidence == "high" else "yellow"
        console.print(f"• {value} [{color}]({confidence})[/{color}]")
        console.print(f"  [dim]Citation (p{page}): \"{quote}\"[/dim]")

    # Fetch Stats
    cursor.execute("SELECT section_name, duration_seconds FROM section_stats WHERE run_id = ?", (run_id,))
    stats = cursor.fetchall()
    
    if stats:
        console.print("\n")
        console.rule("[bold]Performance Stats[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Section")
        table.add_column("Duration (s)")
        
        total_time = 0
        for section, duration in stats:
            table.add_row(section, f"{duration:.2f}")
            total_time += duration
            
        console.print(table)
        console.print(f"[bold]Total Inference Time:[/bold] {total_time:.2f}s")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=Config.DB_PATH, help="Path to audit DB")
    parser.add_argument("--run-id", help="Specific Run ID (optional, defaults to latest)")
    args = parser.parse_args()
    
    db_path = Path(args.db)
    
    if args.run_id:
        run_id = args.run_id
    else:
        # Auto-detect latest
        latest = get_latest_run_id(db_path)
        if not latest:
            console.print("[red]No runs found in database.[/red]")
            sys.exit(1)
        run_id = latest[0]
    
    generate_report(db_path, run_id)