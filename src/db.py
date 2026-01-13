import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/fda_agent.db")

def init_db():
    """Initializes the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Runs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            filename TEXT,
            model_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Audit Log (Raw interactions)
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            interaction_id TEXT PRIMARY KEY,
            run_id TEXT,
            section_name TEXT,
            question TEXT,
            prompt_snapshot TEXT,
            raw_response TEXT,
            status TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        )
    ''')
    
    # 3. Verified Facts
    c.execute('''
        CREATE TABLE IF NOT EXISTS facts (
            fact_id TEXT PRIMARY KEY,
            interaction_id TEXT,
            run_id TEXT,
            attribute TEXT,
            value TEXT,
            confidence TEXT,
            citation_page INT,
            citation_snippet TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

class DBLogger:
    def __init__(self, filename: str, model_name: str):
        self.run_id = str(uuid.uuid4())
        self.filename = filename
        
        # Initialize run entry
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO runs (run_id, filename, model_name) VALUES (?, ?, ?)",
                  (self.run_id, filename, model_name))
        conn.commit()
        conn.close()

    def log_interaction(self, section: str, question: str, prompt: str, 
                       response: str, status: str) -> str:
        """Logs a raw LLM interaction. Returns the interaction_id."""
        interaction_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO audit_log 
            (interaction_id, run_id, section_name, question, prompt_snapshot, raw_response, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (interaction_id, self.run_id, section, question, prompt, response, status))
        conn.commit()
        conn.close()
        return interaction_id

    def save_fact(self, interaction_id: str, fact_obj):
        """Saves a verified Fact Pydantic object."""
        fact_id = str(uuid.uuid4())
        # We take the first citation for simplicity in the relational table
        # In a production Postgres setup, we might use a separate citations table.
        citation = fact_obj.citations[0] if fact_obj.citations else None
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO facts 
            (fact_id, interaction_id, run_id, attribute, value, confidence, citation_page, citation_snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fact_id, interaction_id, self.run_id, 
            fact_obj.attribute, fact_obj.value, fact_obj.confidence.value,
            citation.page_number if citation else 0,
            citation.quote_snippet if citation else ""
        ))
        conn.commit()
        conn.close()
