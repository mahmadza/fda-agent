import sqlite3
import uuid
from pathlib import Path
from src.core.schema import Fact
from src.config import Config

class AuditStore:
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = Path(db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                filename TEXT,
                model_name TEXT,
                seed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # section_stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS section_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                section_name TEXT,
                duration_seconds REAL,
                chunk_count INTEGER,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            )
        """)

        # interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                chunk_id TEXT,
                question TEXT,
                prompt_snapshot TEXT,
                raw_response TEXT,
                is_valid_json BOOLEAN,
                latency_seconds REAL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            )
        """)
        
        # facts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                chunk_page INTEGER,
                attribute TEXT,
                value TEXT,
                citation_quote TEXT,
                confidence TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            )
        """)
        
        conn.commit()
        conn.close()

    def start_run(self, filename: str, model_name: str, seed: int) -> str:
        run_id = str(uuid.uuid4())
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO runs (run_id, filename, model_name, seed) VALUES (?, ?, ?, ?)",
            (run_id, filename, model_name, seed)
        )
        conn.commit()
        conn.close()
        return run_id

    def log_section_stats(self, run_id: str, section_name: str, duration: float, chunk_count: int):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO section_stats (run_id, section_name, duration_seconds, chunk_count) VALUES (?, ?, ?, ?)",
            (run_id, section_name, duration, chunk_count)
        )
        conn.commit()
        conn.close()

    def log_interaction(self, run_id: str, chunk_id: str, question: str, prompt: str, response: str, is_valid_json: bool, latency: float = 0.0):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO interactions 
               (run_id, chunk_id, question, prompt_snapshot, raw_response, is_valid_json, latency_seconds) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (run_id, chunk_id, question, prompt, response, is_valid_json, latency)
        )
        conn.commit()
        conn.close()

    def save_fact(self, run_id: str, fact: Fact):
        conn = self._get_conn()
        citation_txt = fact.citations[0].quote_snippet if fact.citations else ""
        page_num = fact.citations[0].page_number if fact.citations else 0
        
        conn.execute(
            """INSERT INTO facts 
               (run_id, chunk_page, attribute, value, citation_quote, confidence) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, page_num, fact.attribute, fact.value, citation_txt, fact.confidence.value)
        )
        conn.commit()
        conn.close()