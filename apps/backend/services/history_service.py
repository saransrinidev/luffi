import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "luffi_history.db"


class HistoryService:
    """Stores query history in local SQLite database."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL
                )
            """)
            conn.commit()
        logger.info(f"History DB ready: {DB_PATH}")

    def save(self, mode: str, input_text: str, response: str, model: str):
        """Save a query to history."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO history (timestamp, mode, input_text, response, model) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), mode, input_text, response, model),
            )
            conn.commit()
        logger.info(f"Saved to history: [{mode}] {input_text[:30]}...")

    def get_recent(self, limit: int = 20) -> list[dict]:
        """Get recent history entries."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search history by input text."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM history WHERE input_text LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def clear(self):
        """Clear all history."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM history")
            conn.commit()
        logger.info("History cleared")
