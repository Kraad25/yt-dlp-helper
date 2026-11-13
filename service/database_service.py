import sqlite3
from model.watcher_db_model import db_transaction

ITEM_STATUS_NEW = "new"
ITEM_STATUS_DOWNLOADED = "downloaded"
ITEM_STATUS_IGNORED = "ignored"
ITEM_STATUS_REMOVED_UPSTREAM = "removed_upstream"

# Public Methods
## Adders
def add_watch_with_items(section_info: dict, items: list[dict]):
    section_url = _clean_url(section_info["section_url"])
    rows = [
        (
            item["id"],
            item["title"],
            item["url"],
            item["status"],
            item.get("thumbnail_url"),
            section_url,
        )
        for item in items
    ]
    try:
        with db_transaction() as connection:
            connection.execute(
                """
                INSERT INTO watch_list
                    (section_url, section_name, destination_path, auto_download, is_active, poll_interval)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (section_url, section_info["section_name"], section_info["destination_path"],
                section_info["auto_download"], section_info["poll_interval"]),
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO items
                    (item_id, title, url, item_status, thumbnail_url, section_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return True
    except sqlite3.IntegrityError:
        return False

## Getters
def get_watch_list() -> list[dict]:
    with db_transaction() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM watch_list"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_active_or_paused_watch_list(is_active: bool) -> list[dict]:
    with db_transaction() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM watch_list WHERE is_active = ?", (is_active,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_poll_intervals() -> list[dict]:
    with db_transaction() as connection:
        rows = connection.execute(
            "SELECT section_url, poll_interval FROM watch_list WHERE is_active = TRUE"
        ).fetchall()
        return [dict(row) for row in rows]

def get_items_by_section(section_url: str) -> list[dict]:
    with db_transaction() as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM items WHERE section_url = ?", (section_url,)
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def is_watching(section_url: str) -> bool:
    with db_transaction() as connection:
        row = connection.execute(
            "SELECT 1 FROM watch_list WHERE section_url = ?",
            (_clean_url(section_url),),
        ).fetchone()
        return row is not None
    
## Setters
def set_watch_active(section_url: str, is_active: bool):
    with db_transaction() as connection:
        connection.execute(
            "UPDATE watch_list SET is_active = ? WHERE section_url = ?", (is_active, _clean_url(section_url)),
        )


def set_item_status(item_id: str, status: str):
    with db_transaction() as connection:
        connection.execute(
            "UPDATE items SET item_status = ? WHERE item_id = ?", (status, item_id),
        )

# Private Methods
def _clean_url(url: str) -> str:
    return url.strip().rstrip("/")
