import pytest
from src.verifier import QuoteVerifier

@pytest.fixture
def verifier():
    return QuoteVerifier(threshold=85)

def test_exact_match(verifier):
    source = "Keytruda is indicated for the treatment of patients."
    quote = "Keytruda is indicated for the treatment"
    result = verifier.verify(source, quote)
    assert result["is_verified"] is True
    assert result["score"] == 100

def test_fuzzy_match_punctuation(verifier):
    # Source has brackets, LLM removes them
    source = "Tumor Mutational Burden-High (TMB-H) cancer"
    quote = "Tumor Mutational Burden High TMB-H cancer" # removed hyphen and parens
    result = verifier.verify(source, quote)
    assert result["is_verified"] is True
    assert result["score"] > 85

def test_hallucination_rejection(verifier):
    source = "Keytruda is indicated for melanoma."
    # LLM hallucinates "lung cancer" which is not in the text
    quote = "Keytruda is indicated for lung cancer." 
    result = verifier.verify(source, quote)
    assert result["is_verified"] is False
    assert result["score"] < 85
