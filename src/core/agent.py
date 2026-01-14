import time
import ollama
import json
from typing import Optional
from src.core.schema import DocumentChunk, Fact, ConfidenceLevel, Citation
from src.core.verifier import QuoteVerifier
from src.infra.store import AuditStore 

from src.config import Config

class ExtractionAgent:
    def __init__(self,
                 model_name: str = Config.DEFAULT_MODEL,
                 store: Optional[AuditStore] = None,
                 run_id: str = None,
                 seed: int = Config.SEED
    ):
        self.model_name = model_name
        self.store = store
        self.run_id = run_id
        self.seed = seed
        self.verifier = QuoteVerifier(threshold=Config.VERIFICATION_THRESHOLD)

    def extract_fact(self, chunk: DocumentChunk, question: str) -> Optional[Fact]:
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

        raw_response = ""
        start_time = time.perf_counter()

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    },
                ],
                format='json',
                options={
                    "seed": self.seed,
                    "temperature": Config.TEMPERATURE
                }
            )
            
            latency = time.perf_counter() - start_time
            
            raw_response = response['message']['content']
            data = json.loads(raw_response)
            
            if self.store and self.run_id:
                self.store.log_interaction(
                    run_id=self.run_id,
                    chunk_id=chunk.chunk_id,
                    question=question,
                    prompt=prompt,
                    response=raw_response,
                    is_valid_json=True,
                    latency=latency
                )

            # Hardening logic
            if isinstance(data.get('value'), str) and "NOT_FOUND" in data['value']:
                return None
            if isinstance(data.get('value'), list):
                data['value'] = "; ".join([str(x) for x in data['value']])
            if isinstance(data.get('quote_snippet'), list):
                data['quote_snippet'] = max(data['quote_snippet'], key=len)

            verification = self.verifier.verify(chunk.text_content, data.get('quote_snippet', ''))
            
            if not verification['is_verified']:
                return None

            fact = Fact(
                attribute=question,
                value=data['value'],
                is_negation=False,
                confidence=ConfidenceLevel(data.get('confidence', 'low')),
                reasoning=f"Extracted via {self.model_name} in {latency:.2f}s",
                citations=[Citation(
                    doc_id=chunk.doc_name,
                    page_number=chunk.page_number,
                    quote_snippet=data['quote_snippet']
                )]
            )

            if self.store and self.run_id:
                self.store.save_fact(self.run_id, fact)

            return fact

        # Exception handling:
        # Simply store the interaction and return None
        except Exception as e:
            latency = time.perf_counter() - start_time
            if self.store and self.run_id:
                self.store.log_interaction(
                    run_id=self.run_id,
                    chunk_id=chunk.chunk_id,
                    question=question,
                    prompt=prompt,
                    response=raw_response or str(e),
                    is_valid_json=False,
                    latency=latency
                )
            return None