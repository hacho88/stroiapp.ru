import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def _db():
    """Yield a connection, commit on success, always close (frees the fd)."""
    connection = _connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_blocks() -> None:
    with _db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS page_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page TEXT NOT NULL DEFAULT 'home',
                type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL DEFAULT '{}',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def list_blocks(page: str = "home") -> list[dict]:
    init_blocks()
    with _db() as connection:
        rows = connection.execute(
            "SELECT * FROM page_blocks WHERE page = ? AND is_active = 1 ORDER BY sort_order ASC",
            (page,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "page": r["page"],
                "type": r["type"],
                "content": json.loads(r["content"]),
                "sort_order": r["sort_order"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]


def get_block(block_id: int) -> dict | None:
    init_blocks()
    with _db() as connection:
        row = connection.execute(
            "SELECT * FROM page_blocks WHERE id = ?", (block_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "page": row["page"],
            "type": row["type"],
            "content": json.loads(row["content"]),
            "sort_order": row["sort_order"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
        }


def create_block(page: str, type: str, content: dict, sort_order: int = 0) -> int:
    init_blocks()
    with _db() as connection:
        cursor = connection.execute(
            "INSERT INTO page_blocks (page, type, content, sort_order) VALUES (?, ?, ?, ?)",
            (page, type, json.dumps(content, ensure_ascii=False), sort_order),
        )
        connection.commit()
        return cursor.lastrowid


def update_block(block_id: int, page: str | None = None, type: str | None = None, content: dict | None = None, sort_order: int | None = None, is_active: bool | None = None) -> bool:
    init_blocks()
    fields = []
    values = []
    if page is not None:
        fields.append("page = ?")
        values.append(page)
    if type is not None:
        fields.append("type = ?")
        values.append(type)
    if content is not None:
        fields.append("content = ?")
        values.append(json.dumps(content, ensure_ascii=False))
    if sort_order is not None:
        fields.append("sort_order = ?")
        values.append(sort_order)
    if is_active is not None:
        fields.append("is_active = ?")
        values.append(1 if is_active else 0)
    if not fields:
        return False
    values.append(block_id)
    with _db() as connection:
        connection.execute(
            f"UPDATE page_blocks SET {', '.join(fields)} WHERE id = ?", values
        )
        connection.commit()
        return True


def delete_block(block_id: int) -> bool:
    init_blocks()
    with _db() as connection:
        cursor = connection.execute("DELETE FROM page_blocks WHERE id = ?", (block_id,))
        connection.commit()
        return cursor.rowcount > 0


def reorder_blocks(page: str, ordered_ids: list[int]) -> bool:
    init_blocks()
    with _db() as connection:
        for sort_order, block_id in enumerate(ordered_ids):
            connection.execute(
                "UPDATE page_blocks SET sort_order = ? WHERE id = ? AND page = ?",
                (sort_order, block_id, page),
            )
        connection.commit()
        return True
