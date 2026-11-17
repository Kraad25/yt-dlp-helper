import sqlite3
from contextlib import contextmanager

from core.paths import user_data_dir

WATCHER_DB_PATH = user_data_dir() / "database" / "watcher.db"
SCHEMA_VERSION = 1

def get_database_connection():
    connection = sqlite3.connect(WATCHER_DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection

def initialize_database():
    WATCHER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = get_database_connection()
    try:
        connection.execute("PRAGMA journal_mode=WAL;")
    finally:
        connection.close()

    with db_transaction() as connection:
        connection.execute("BEGIN")

        version = connection.execute("PRAGMA user_version").fetchone()[0]

        if version < 1:
            connection.execute("""
                CREATE TABLE watch_list(
                    section_url TEXT PRIMARY KEY NOT NULL,
                    section_name TEXT NOT NULL,
                    destination_path TEXT NOT NULL,
                    auto_download BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    poll_interval_min INTEGER NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE items(
                    item_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    item_status TEXT NOT NULL
                        CHECK (item_status IN ('new','queued','downloaded','ignored','removed_upstream')),
                    thumbnail_url TEXT,
                    section_url TEXT NOT NULL,
                    PRIMARY KEY (section_url, item_id),
                    FOREIGN KEY (section_url) REFERENCES watch_list(section_url) ON DELETE CASCADE
                )
            """)
            connection.execute("PRAGMA user_version = 1")

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