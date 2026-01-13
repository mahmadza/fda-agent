from rapidfuzz import fuzz, utils

class QuoteVerifier:
    def __init__(self, threshold: int = 90):
        self.threshold = threshold

    def verify(self, source_text: str, quote: str) -> dict:
        if not quote or not source_text:
            return {
                "is_verified": False,
                "score": 0,
                "matched_substring": ""
            }

        quote_clean = quote.strip()
        source_clean = source_text.strip()
        
        q_len = len(quote_clean)
        s_len = len(source_clean)

        # 1. STRICT Physical Constraint
        # A quote cannot be strictly longer than the source.
        if q_len > s_len:
            return {
                "is_verified": False,
                "score": 0,
                "matched_substring": "Quote longer than source"
            }

        # 2. Fast check: Exact match
        if quote_clean in source_clean:
             return {
                "is_verified": True, 
                "score": 100, 
                "matched_substring": quote_clean
            }

        # 3. Smart Fuzzy Matching
        # If the quote is nearly the entire text (e.g. >70% of source),
        # we must match the *whole* string structure (fuzz.ratio).
        # Otherwise, we look for the quote *inside* the text (fuzz.partial_ratio).
        
        if q_len > s_len * 0.7:
            # Strict mode: penalizes "melanoma" vs "lung cancer" mismatch
            score = fuzz.ratio(
                quote_clean.lower(), 
                source_clean.lower(), 
                processor=utils.default_process
            )
        else:
            # Substring mode: finds "dosage is 10mg" inside a long paragraph
            score = fuzz.partial_ratio(
                quote_clean.lower(), 
                source_clean.lower(), 
                processor=utils.default_process
            )
        
        is_verified = score >= self.threshold

        return {
            "is_verified": is_verified,
            "score": round(score, 2),
            "matched_substring": "Fuzzy Match" 
        }