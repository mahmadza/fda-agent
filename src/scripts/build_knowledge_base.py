import sqlite3
import chromadb
from chromadb.utils import embedding_functions
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from src.config import Config

console = Console()

def build_vector_index():
    console.rule("[bold cyan]Week 3: Vector Knowledge Base Builder[/bold cyan]")
    
    # 1. Connect to SQLite
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, attribute, value, citation_quote, confidence FROM facts WHERE confidence != 'LOW'")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        console.print("[yellow]⚠️ No high-confidence facts found in SQLite. Run extraction first.[/yellow]")
        return

    # 2. Setup Vector Store
    chroma_client = chromadb.PersistentClient(path="./data/vector_store")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection(name="fda_facts", embedding_function=ef)

    # 3. Vectorize with Rich Progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Indexing facts...", total=len(rows))
        
        for row in rows:
            fact_id, attr, val, quote, conf = row
            doc_text = f"Attribute: {attr}. Value: {val}. Context: {quote}"
            
            collection.add(
                documents=[doc_text],
                metadatas=[{"attribute": attr, "confidence": conf}],
                ids=[str(fact_id)]
            )
            progress.advance(task)

    console.print(f"\n[bold green]✅ Successfully indexed {len(rows)} facts into ChromaDB.[/bold green]")

if __name__ == "__main__":
    build_vector_index()