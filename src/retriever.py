from typing import List
from src.schema import DocumentChunk

class KeywordRetriever:
    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks

    def retrieve(self, query: str, top_k: int = 5) -> List[DocumentChunk]:
        """
        Returns chunks that contain words from the query, ranked by count.
        """
        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in self.chunks:
            text_lower = chunk.text_content.lower()
            score = 0
            for word in query_words:
                if word in text_lower:
                    score += 1
            
            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        return [item[1] for item in scored_chunks[:top_k]]
