import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            input_data TEXT NOT NULL,
            output_data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_generation(source_type, input_data, output_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO generations (source_type, input_data, output_data, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            source_type,
            input_data,
            output_data,
            datetime.now(timezone.utc).isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_history(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, source_type, input_data, output_data, created_at
        FROM generations
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_history_by_type(source_type, limit=5):
    """
    Retrieves recent history entries filtered to one source type
    (e.g. 'news', 'pdf', 'youtube').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, source_type, input_data, output_data, created_at
        FROM generations
        WHERE source_type = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (source_type, limit)
    )

    rows = cursor.fetchall()
    conn.close()

    return rows