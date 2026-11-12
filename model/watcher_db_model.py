import sqlite3
from contextlib import contextmanager

from core.paths import user_data_dir

WATCHER_DB_PATH = user_data_dir() / "database" / "watcher.db"
WATCHER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_database_connection():
    connection = sqlite3.connect(WATCHER_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection

def initilize_database():
    connection = get_database_connection()
    cursor = connection.cursor()

    connection.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watch_list(
            section_url TEXT PRIMARY KEY NOT NULL,
            section_name TEXT NOT NULL,
            destination_path TEXT NOT NULL,
            auto_download BOOLEAN NOT NULL DEFAULT FALSE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            poll_interval INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items(
            item_id TEXT PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            item_status TEXT NOT NULL,
            thumbnail_url TEXT,
            section_url TEXT NOT NULL,
            FOREIGN KEY (section_url) REFERENCES watch_list(section_url) ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

@contextmanager
def db_transaction():
    connection = get_database_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()