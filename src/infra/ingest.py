import fitz
from pathlib import Path
from typing import List
from src.core.schema import DocumentChunk

def ingest_pdf(file_path: Path) -> List[DocumentChunk]:
    doc = fitz.open(file_path)
    chunks = []
    
    print(f"Ingesting {file_path.name}...")

    for page_index, page in enumerate(doc):
        text_blocks = page.get_text("blocks")
        
        valid_text = []
        for b in text_blocks:
            # b[6] is block_type (0=text). b[4] is the text content.
            if b[6] == 0:
                clean_line = b[4].strip()
                if clean_line:
                    valid_text.append(clean_line)
        
        # Join with double newline to separate paragraphs clearly
        text_content = "\n\n".join(valid_text)
        
        if not text_content:
            continue

        chunk = DocumentChunk(
            chunk_id="",
            doc_name=file_path.name,
            page_number=page_index + 1,
            text_content=text_content
        )
        chunk.chunk_id = chunk.compute_id()
        chunks.append(chunk)

    return chunks

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest <path_to_pdf>")
        sys.exit(1)
        
    path = Path(sys.argv[1])
    result_chunks = ingest_pdf(path)
    
    print(f"Extracted {len(result_chunks)} chunks.")
    
    # Preview: Show Page 2 (often denser text) instead of Page 1
    # and only show the first 500 characters
    if len(result_chunks) > 1:
        sample_chunk = result_chunks[1] 
        print(f"\n--- Sample (Page {sample_chunk.page_number}) ---")
        print(sample_chunk.text_content[:500])
        print("--- End Sample ---")