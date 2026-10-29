import json
import sqlite3
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
    connection = _connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with _db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_analogs (
                product_id INTEGER PRIMARY KEY,
                analogs TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_analogs(product_id: int) -> list[dict]:
    """[{pid, score}] — подобранные аналоги по характеристикам."""
    init_db()
    with _db() as connection:
        row = connection.execute(
            "SELECT analogs FROM product_analogs WHERE product_id = ?",
            (int(product_id),)).fetchone()
    if not row:
        return []
    try:
        return json.loads(row["analogs"] or "[]")
    except (ValueError, TypeError):
        return []


def save_analogs_bulk(items: dict[int, list[dict]]) -> int:
    init_db()
    with _db() as connection:
        connection.executemany(
            """
            INSERT INTO product_analogs (product_id, analogs, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(product_id) DO UPDATE SET
                analogs = excluded.analogs,
                updated_at = CURRENT_TIMESTAMP
            """,
            [(int(pid), json.dumps(analogs, ensure_ascii=False))
             for pid, analogs in items.items()],
        )
    return len(items)
