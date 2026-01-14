
from pathlib import Path

class Config:

    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
    DB_PATH = DATA_DIR / "audit.db"

    # AI Settings
    DEFAULT_MODEL = "gemma2:2b"

    # Determinism Settings
    # Fix this to 42 for development. 
    # Change to None or random.randint() only when stress-testing.
    SEED = 42  
    TEMPERATURE = 0.0 # Greedy decoding for maximum factual consistency
    
    # Validation
    VERIFICATION_THRESHOLD = 85

    # The Target Questions
    TARGET_SECTIONS = {
        "Indications": "What diseases or conditions is this drug indicated to treat?",
        "Dosage": "What is the recommended dosage and schedule?",
        "Contraindications": "Who should NOT take this drug? List contraindications.",
        "Warnings": "What are the most serious warnings or boxed warnings?"
    }