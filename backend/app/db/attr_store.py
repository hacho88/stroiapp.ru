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
            CREATE TABLE IF NOT EXISTS product_attributes (
                product_id INTEGER PRIMARY KEY,
                attributes TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_all_attributes() -> dict[int, list[dict]]:
    """{product_id: [{name, text}, ...]}"""
    init_db()
    with _db() as connection:
        rows = connection.execute("SELECT product_id, attributes FROM product_attributes").fetchall()
    out: dict[int, list[dict]] = {}
    for row in rows:
        try:
            out[int(row["product_id"])] = json.loads(row["attributes"] or "[]")
        except (ValueError, TypeError):
            continue
    return out


def save_attributes(product_id: int, attributes: list[dict]) -> None:
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO product_attributes (product_id, attributes, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(product_id) DO UPDATE SET
                attributes = excluded.attributes,
                updated_at = CURRENT_TIMESTAMP
            """,
            (int(product_id), json.dumps(attributes, ensure_ascii=False)),
        )


def save_attributes_bulk(items: dict[int, list[dict]]) -> int:
    init_db()
    with _db() as connection:
        connection.executemany(
            """
            INSERT INTO product_attributes (product_id, attributes, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(product_id) DO UPDATE SET
                attributes = excluded.attributes,
                updated_at = CURRENT_TIMESTAMP
            """,
            [(int(pid), json.dumps(attrs, ensure_ascii=False)) for pid, attrs in items.items()],
        )
    return len(items)
