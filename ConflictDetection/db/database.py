import sqlite3
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_path: str):
        """Initializes the Database instance with the specified database path."""
        self.db_path = db_path

    def init_db(self):
        """Initializes the SQLite database with the required schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    text_extracted TEXT,
                    conflictive BOOLEAN,
                    agent_id INTEGER,
                    agent_name TEXT,
                    date TEXT
                )
                """
            )

    def add_file(self, file_path: str, agent_id: int, agent_name: str, date: str):
        """Adds a file record to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO processed_files (file_path, agent_id, agent_name, date) VALUES (?, ?, ?, ?)",
                (file_path, agent_id, agent_name, date)
            )

    def get_unprocessed_files(self) -> List[Tuple[int, str, Optional[str]]]:
        """Fetches files where text_extracted or conflictive is NULL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, file_path, text_extracted FROM processed_files WHERE text_extracted IS NULL OR conflictive IS NULL"
            )
            return cursor.fetchall()

    def get_processed_files(self) -> List[Tuple[int, str, str, bool, int, str, str]]:
        """Fetches files where text_extracted and conflictive are NOT NULL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, file_path, text_extracted, conflictive, agent_id, agent_name, date 
                FROM processed_files 
                WHERE text_extracted IS NOT NULL AND conflictive IS NOT NULL
                """
            )
            return cursor.fetchall()

    def update_file(self, file_id: int, text_extracted: str, conflictive: bool):
        """Updates the database with the extracted text and conflictive status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE processed_files
                SET text_extracted = ?, conflictive = ?
                WHERE id = ?
                """,
                (text_extracted, conflictive, file_id)
            )
