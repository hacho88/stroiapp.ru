import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER NOT NULL,
                sku TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                price REAL NOT NULL DEFAULT 0,
                scraped_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competitor_id) REFERENCES competitors(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS competitor_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER NOT NULL,
                product_name TEXT NOT NULL DEFAULT '',
                product_url TEXT,
                price REAL,
                category TEXT,
                description TEXT,
                image_url TEXT,
                keywords TEXT,
                last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competitor_id) REFERENCES competitors(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS competitor_ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER,
                keyword TEXT NOT NULL DEFAULT '',
                ad_title TEXT NOT NULL DEFAULT '',
                ad_text TEXT NOT NULL DEFAULT '',
                ad_url TEXT,
                ad_position TEXT DEFAULT '',
                ad_type TEXT DEFAULT '',
                found_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competitor_id) REFERENCES competitors(id)
            )
            """
        )


def add_competitor(name: str, url: str = "") -> int:
    init_db()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO competitors (name, url) VALUES (?, ?)",
            (name, url),
        )
        return cursor.lastrowid


def list_competitors() -> list[dict]:
    init_db()
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM competitors ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def add_price(competitor_id: int, sku: str, name: str, price: float) -> None:
    init_db()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO competitor_prices (competitor_id, sku, name, price, scraped_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT DO UPDATE SET price = excluded.price, scraped_at = CURRENT_TIMESTAMP
            """,
            (competitor_id, sku, name, price),
        )


def get_prices(competitor_id: int) -> list[dict]:
    init_db()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM competitor_prices WHERE competitor_id = ? ORDER BY scraped_at DESC",
            (competitor_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_comparison() -> list[dict]:
    init_db()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT cp.sku, cp.name, cp.price AS competitor_price, c.name AS competitor_name,
                   cp.competitor_id
            FROM competitor_prices cp
            JOIN competitors c ON cp.competitor_id = c.id
            ORDER BY cp.scraped_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def clear_competitor_products(competitor_id: int) -> None:
    init_db()
    with _connect() as connection:
        connection.execute("DELETE FROM competitor_products WHERE competitor_id = ?", (competitor_id,))


def save_competitor_products(competitor_id: int, products: list[dict]) -> int:
    init_db()
    clear_competitor_products(competitor_id)
    imported = 0
    with _connect() as connection:
        for p in products:
            connection.execute(
                """
                INSERT INTO competitor_products
                (competitor_id, product_name, product_url, price, category, description, image_url, keywords, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    competitor_id,
                    p.get("product_name", "")[:255],
                    p.get("product_url", "")[:500],
                    p.get("price") if p.get("price") is not None else None,
                    p.get("category", "")[:255],
                    p.get("description", "")[:500],
                    p.get("image_url", "")[:500],
                    p.get("keywords", ""),
                ),
            )
            imported += 1
    return imported


def get_competitor_products(competitor_id: int, limit: int = 100, offset: int = 0) -> list[dict]:
    init_db()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM competitor_products
            WHERE competitor_id = ?
            ORDER BY price ASC
            LIMIT ? OFFSET ?
            """,
            (competitor_id, limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def get_competitor_product_stats(competitor_id: int) -> dict:
    init_db()
    with _connect() as connection:
        total = connection.execute(
            "SELECT COUNT(*) as cnt FROM competitor_products WHERE competitor_id = ?", (competitor_id,)
        ).fetchone()["cnt"]
        avg_price = connection.execute(
            "SELECT AVG(price) as avg_p FROM competitor_products WHERE competitor_id = ? AND price > 0", (competitor_id,)
        ).fetchone()["avg_p"] or 0
        categories = connection.execute(
            "SELECT category, COUNT(*) as cnt FROM competitor_products WHERE competitor_id = ? AND category != '' GROUP BY category ORDER BY cnt DESC",
            (competitor_id,),
        ).fetchall()
    return {
        "total_products": total,
        "avg_price": round(avg_price, 2),
        "categories": [dict(row) for row in categories],
    }


def get_all_competitor_products_for_ai(limit: int = 500) -> list[dict]:
    """Все товары конкурентов для AI-анализа."""
    init_db()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT cp.*, c.name as competitor_name, c.url as competitor_url
            FROM competitor_products cp
            JOIN competitors c ON cp.competitor_id = c.id
            ORDER BY cp.price ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_competitor_ads(competitor_id: int = None) -> None:
    init_db()
    with _connect() as connection:
        if competitor_id:
            connection.execute("DELETE FROM competitor_ads WHERE competitor_id = ?", (competitor_id,))
        else:
            connection.execute("DELETE FROM competitor_ads")


def save_competitor_ads(competitor_id: int, ads: list[dict]) -> int:
    init_db()
    clear_competitor_ads(competitor_id)
    imported = 0
    with _connect() as connection:
        for ad in ads:
            connection.execute(
                """
                INSERT INTO competitor_ads
                (competitor_id, keyword, ad_title, ad_text, ad_url, ad_position, ad_type, found_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    competitor_id,
                    ad.get("keyword", "")[:255],
                    ad.get("ad_title", "")[:255],
                    ad.get("ad_text", "")[:500],
                    ad.get("ad_url", "")[:500],
                    ad.get("ad_position", "")[:50],
                    ad.get("ad_type", "")[:50],
                ),
            )
            imported += 1
    return imported


def get_competitor_ads(competitor_id: int = None, limit: int = 200) -> list[dict]:
    init_db()
    with _connect() as connection:
        if competitor_id:
            rows = connection.execute(
                """
                SELECT ca.*, c.name as competitor_name, c.url as competitor_url
                FROM competitor_ads ca
                LEFT JOIN competitors c ON ca.competitor_id = c.id
                WHERE ca.competitor_id = ?
                ORDER BY ca.found_at DESC
                LIMIT ?
                """,
                (competitor_id, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT ca.*, c.name as competitor_name, c.url as competitor_url
                FROM competitor_ads ca
                LEFT JOIN competitors c ON ca.competitor_id = c.id
                ORDER BY ca.found_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]


def get_ads_stats() -> dict:
    init_db()
    with _connect() as connection:
        total = connection.execute("SELECT COUNT(*) as cnt FROM competitor_ads").fetchone()["cnt"]
        top_keywords = connection.execute(
            """
            SELECT keyword, COUNT(*) as cnt FROM competitor_ads
            WHERE keyword != '' GROUP BY keyword ORDER BY cnt DESC LIMIT 10
            """
        ).fetchall()
        top_competitors = connection.execute(
            """
            SELECT c.name, COUNT(*) as cnt FROM competitor_ads ca
            JOIN competitors c ON ca.competitor_id = c.id
            GROUP BY ca.competitor_id ORDER BY cnt DESC LIMIT 10
            """
        ).fetchall()
    return {
        "total_ads": total,
        "top_keywords": [dict(row) for row in top_keywords],
        "top_competitors": [dict(row) for row in top_competitors],
    }
