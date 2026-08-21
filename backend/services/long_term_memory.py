import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "memory.db"


def _get_connection():
    """Return a connection to the SQLite memory database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return conn
    except Exception as exc:
        raise RuntimeError(f"Failed to open memory database: {exc}")


def store_fact(fact: str) -> None:
    """Save a new user fact."""
    try:
        conn = _get_connection()
        conn.execute("INSERT INTO facts (fact) VALUES (?)", (fact.strip(),))
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"Error storing fact: {exc}")


def get_facts() -> list[str]:
    """Return all saved user facts."""
    try:
        conn = _get_connection()
        rows = conn.execute(
            "SELECT fact FROM facts ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as exc:
        print(f"Error getting facts: {exc}")
        return []


def clear_facts() -> None:
    """Delete all saved user facts."""
    try:
        conn = _get_connection()
        conn.execute("DELETE FROM facts")
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"Error clearing facts: {exc}")
