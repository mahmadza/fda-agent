import chromadb
from chromadb.utils import embedding_functions
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def search_knowledge_base(query_text):
    client = chromadb.PersistentClient(path="./data/vector_store")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_collection(name="fda_facts", embedding_function=ef)

    console.print(Panel(f"[bold white]Query:[/bold white] [cyan]{query_text}[/cyan]", border_style="blue"))
    
    results = collection.query(query_texts=[query_text], n_results=3)

    # Create Rich Table for output
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Fact/Context", ratio=3)
    table.add_column("Confidence", justify="right")

    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        
        table.add_row(
            str(i+1),
            doc,
            f"[{'green' if meta['confidence']=='HIGH' else 'yellow'}]{meta['confidence']}[/]"
        )

    console.print(table)
    console.print("\n")

if __name__ == "__main__":
    console.rule("[bold green]FDA AI Agent Query Interface[/bold green]")
    search_knowledge_base("What are the weight loss indications?")
    search_knowledge_base("Find any mention of renal or kidney risks.")