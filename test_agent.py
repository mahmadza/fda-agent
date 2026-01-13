# test_agent.py (Quick manual check)
from src.ingest import ingest_pdf
from src.agent import ExtractionAgent
from pathlib import Path

# Load chunks
chunks = ingest_pdf(Path("data/raw_pdfs/keytruda.pdf"))
# Pick a chunk we know has info (e.g., chunk 1 or 2 usually has Indications)
target_chunk = chunks[1] 

agent = ExtractionAgent()
fact = agent.extract_fact(target_chunk, "What is the indication for Melanoma?")

if fact:
    print(f"\n✅ FOUND FACT: {fact.value}")
    print(f"   Citation: \"{fact.citations[0].quote_snippet}\"")
else:
    print("\n❌ No fact found in this chunk.")
