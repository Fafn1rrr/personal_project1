import sqlite3 as db
from pathlib import Path

DB_PATH = Path(__file__).with_name("mood.db")


def get_conn():
    """
    Единственный правильный способ подключаться к БД в проекте.
    Всегда включает foreign keys для текущего соединения.
    """
    con = db.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    return con, cur


def init_db():
    """
    Инициализация схемы (безопасно вызывать много раз).
    """
    con, cur = get_conn()
    try:
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            valence INTEGER NOT NULL CHECK (valence BETWEEN -5 AND 5),
            arousal INTEGER NOT NULL CHECK (arousal BETWEEN 0 AND 5),
            energy INTEGER NULL CHECK (energy BETWEEN 0 AND 5),
            social INTEGER NULL CHECK (social BETWEEN 0 AND 5),
            note TEXT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_entries_ts
        ON entries(ts);

        CREATE TABLE IF NOT EXISTS emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS entry_emotions (
            entry_id INTEGER NOT NULL,
            emotion_id INTEGER NOT NULL,
            PRIMARY KEY (entry_id, emotion_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (emotion_id) REFERENCES emotions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_entry_emotions_emotion
        ON entry_emotions(emotion_id);

        CREATE TABLE IF NOT EXISTS entry_factors (
            entry_id INTEGER NOT NULL,
            factor_id INTEGER NOT NULL,
            PRIMARY KEY (entry_id, factor_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (factor_id) REFERENCES factors(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_entry_factors_factor
        ON entry_factors(factor_id);
        """)
        con.commit()
    finally:
        con.close()


if __name__ == "__main__":
    init_db()
    print(f"DB initialized: {DB_PATH}")