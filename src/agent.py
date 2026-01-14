import ollama
import json
from typing import Optional
from src.schema import DocumentChunk, Fact, ConfidenceLevel, Citation
from src.verifier import QuoteVerifier

class ExtractionAgent:
    # Change default from "mistral-nemo" to "llama3.1"
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        self.verifier = QuoteVerifier(threshold=85)

    def extract_fact(self, chunk: DocumentChunk, question: str) -> Optional[Fact]:
        """
        Asks the LLM to answer 'question' based *only* on 'chunk'.
        """
        prompt = f"""
        You are an expert FDA Regulatory Analyst.
        
        TASK: Extract the answer to the QUESTION below based ONLY on the provided TEXT context.
        
        RULES:
        1. If the answer is not clearly stated in the text, return JSON with value="NOT_FOUND".
        2. "quote_snippet" MUST be a single, contiguous string exactly as it appears in the text.
        3. DO NOT combine separate sentences into one quote. Pick the single best sentence.
        4. Output must be valid JSON only.
        
        TEXT CONTEXT (Page {chunk.page_number}):
        {chunk.text_content}
        
        QUESTION: {question}
        
        JSON SCHEMA:
        {{
            "value": "The extracted fact (string)",
            "quote_snippet": "exact substring from text (string)",
            "confidence": "high|medium|low"
        }}
        """

        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt},
            ], format='json')
            
            # Parse JSON
            content = response['message']['content']
            data = json.loads(content)
            
            # --- HARDENING FIXES ---
            
            # 1. Handle "NOT_FOUND" variations
            if isinstance(data.get('value'), str) and "NOT_FOUND" in data['value']:
                return None

            # 2. Auto-fix lists (The crash fix)
            # If LLM returns ["fact1", "fact2"], join them.
            if isinstance(data.get('value'), list):
                data['value'] = "; ".join([str(x) for x in data['value']])
            
            if isinstance(data.get('quote_snippet'), list):
                # We can't verify a list of quotes easily, so pick the longest one
                # or join them. Let's pick the longest for safety.
                data['quote_snippet'] = max(data['quote_snippet'], key=len)

            # 3. Ensure they are strings now
            if not isinstance(data.get('value'), str) or not isinstance(data.get('quote_snippet'), str):
                # If still not a string, skip to avoid crash
                return None

            # -----------------------

            # CRITICAL: Verify the quote immediately
            verification = self.verifier.verify(chunk.text_content, data['quote_snippet'])
            
            if not verification['is_verified']:
                # Optional: Log this to see what failed
                # print(f"⚠️  Hallucination: {data['quote_snippet'][:50]}...")
                return None

            return Fact(
                attribute=question,
                value=data['value'],
                is_negation=False,
                confidence=ConfidenceLevel(data.get('confidence', 'low')), # Default to low if missing
                reasoning="Extracted via Mistral-Nemo",
                citations=[
                    Citation(
                        doc_id=chunk.doc_name,
                        page_number=chunk.page_number,
                        quote_snippet=data['quote_snippet']
                    )
                ]
            )

        except json.JSONDecodeError:
            print(f"Error: LLM did not return valid JSON for chunk {chunk.page_number}")
            return None
        except Exception as e:
            # Catch Pydantic validation errors or other crashes nicely
            print(f"Error processing chunk {chunk.page_number}: {e}")
            return None