import hashlib
from enum import Enum
from typing import List
from pydantic import BaseModel, Field

# --- Enums ---
class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

# --- Core Models ---
class Citation(BaseModel):
    doc_id: str
    page_number: int
    quote_snippet: str = Field(..., description="Exact substring from source text verifying the fact.")

class Fact(BaseModel):
    attribute: str       # e.g., "indication_primary"
    value: str           # The extracted information
    is_negation: bool    # True if the text says "Not effective" vs "Effective"
    citations: List[Citation]
    confidence: ConfidenceLevel
    reasoning: str       # Chain-of-thought justification from the LLM

class Section(BaseModel):
    title: str           # e.g., "Safety Profile"
    facts: List[Fact]
    missing_info: List[str] # Questions the LLM could not answer based on evidence

class MoleculeBrief(BaseModel):
    molecule_name: str
    sections: List[Section]
    overall_status: str
    generated_at: str

class DocumentChunk(BaseModel):
    """
    Represents a discrete segment of text extracted from a document.
    """
    chunk_id: str = Field(..., description="Unique hash of the text content")
    doc_name: str = Field(..., description="Filename of the source PDF")
    page_number: int = Field(..., description="1-based page number")
    text_content: str = Field(..., description="The actual extracted text")
    
    def compute_id(self):
        """Generates a reproducible hash ID based on content and location."""
        raw = f"{self.doc_name}-{self.page_number}-{self.text_content[:50]}"
        return hashlib.md5(raw.encode()).hexdigest()