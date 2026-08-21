import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "memory.db"


def _get_connection():
    """Return a connection to the SQLite memory database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return conn
    except Exception as exc:
        raise RuntimeError(f"Failed to open memory database: {exc}")


def store_preference(key: str, value: str) -> None:
    """Save or overwrite a user preference."""
    try:
        conn = _get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"Error storing preference: {exc}")


def get_preferences() -> dict[str, str]:
    """Return all user preferences as a key-value dictionary."""
    try:
        conn = _get_connection()
        rows = conn.execute(
            "SELECT key, value FROM preferences ORDER BY key"
        ).fetchall()
        conn.close()
        return {key: value for key, value in rows}
    except Exception as exc:
        print(f"Error getting preferences: {exc}")
        return {}


def clear_preferences() -> None:
    """Delete all stored user preferences."""
    try:
        conn = _get_connection()
        conn.execute("DELETE FROM preferences")
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"Error clearing preferences: {exc}")
