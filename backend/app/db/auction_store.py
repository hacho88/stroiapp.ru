"""Хранилище результатов сканирования аукциона Яндекс Директ.

Схема:
- auction_scan: сессии сканирования (когда, сколько ключей, кампания-зонд).
- auction_item: строки — ключ → цена входа в топ → рекомендуемая ставка.
- auction_settings: флаги (auto_hold, target_campaign_id и т.п.).
"""
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
            CREATE TABLE IF NOT EXISTS auction_scan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                probe_campaign_id INTEGER,
                keywords_total INTEGER NOT NULL DEFAULT 0,
                keywords_with_data INTEGER NOT NULL DEFAULT 0,
                products_total INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ok',
                note TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS auction_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                keyword TEXT NOT NULL DEFAULT '',
                keyword_id INTEGER,
                product_name TEXT NOT NULL DEFAULT '',
                product_sku TEXT NOT NULL DEFAULT '',
                product_margin REAL NOT NULL DEFAULT 0,
                top_bid_rub REAL NOT NULL DEFAULT 0,
                top_price_rub REAL NOT NULL DEFAULT 0,
                recommended_rub REAL NOT NULL DEFAULT 0,
                competitors_count INTEGER NOT NULL DEFAULT 0,
                applied INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (scan_id) REFERENCES auction_scan(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS auction_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_auction_item_scan ON auction_item(scan_id)"
        )


# --- сканы ---

def create_scan(probe_campaign_id: int | None, keywords_total: int,
                products_total: int, status: str = "ok", note: str = "") -> int:
    init_db()
    with _db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO auction_scan
            (probe_campaign_id, keywords_total, products_total, status, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (probe_campaign_id, keywords_total, products_total, status, note),
        )
        return cursor.lastrowid


def update_scan_counts(scan_id: int, keywords_with_data: int) -> None:
    init_db()
    with _db() as connection:
        connection.execute(
            "UPDATE auction_scan SET keywords_with_data = ? WHERE id = ?",
            (keywords_with_data, scan_id),
        )


def save_items(scan_id: int, items: list[dict]) -> int:
    init_db()
    saved = 0
    with _db() as connection:
        for it in items:
            connection.execute(
                """
                INSERT INTO auction_item
                (scan_id, keyword, keyword_id, product_name, product_sku,
                 product_margin, top_bid_rub, top_price_rub, recommended_rub,
                 competitors_count, applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    scan_id,
                    it.get("keyword", "")[:400],
                    it.get("keyword_id"),
                    it.get("product_name", "")[:255],
                    it.get("product_sku", "")[:64],
                    float(it.get("product_margin") or 0),
                    float(it.get("top_bid_rub") or 0),
                    float(it.get("top_price_rub") or 0),
                    float(it.get("recommended_rub") or 0),
                    int(it.get("competitors_count") or 0),
                ),
            )
            saved += 1
    return saved


def latest_scan() -> dict | None:
    init_db()
    with _db() as connection:
        row = connection.execute(
            "SELECT * FROM auction_scan ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def latest_scan_items(limit: int = 500) -> list[dict]:
    scan = latest_scan()
    if not scan:
        return []
    with _db() as connection:
        rows = connection.execute(
            """
            SELECT * FROM auction_item
            WHERE scan_id = ?
            ORDER BY recommended_rub DESC
            LIMIT ?
            """,
            (scan["id"], limit),
        ).fetchall()
    return [dict(row) for row in rows]


def mark_applied(keyword: str) -> None:
    """Помечает все строки последнего скана с данным ключом как применённые."""
    scan = latest_scan()
    if not scan:
        return
    with _db() as connection:
        connection.execute(
            "UPDATE auction_item SET applied = 1 WHERE scan_id = ? AND keyword = ?",
            (scan["id"], keyword),
        )


# --- настройки ---

def get_setting(key: str, default: str = "") -> str:
    init_db()
    with _db() as connection:
        row = connection.execute(
            "SELECT value FROM auction_settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO auction_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
