"""Хранилище статей Журнала moscow.stroiapp.ru (контент-фабрика).

Статьи публикуются НЕ в OpenCart-блог, а в SQLite рядом с app.db —
витрина читает их через публичные GET /api/storefront/journal*.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"
_MSK = timezone(timedelta(hours=3))


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


def init_journal() -> None:
    with _db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Продукт',
                tone TEXT NOT NULL DEFAULT 'article-grey',
                intro TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                product_sku TEXT NOT NULL DEFAULT '',
                product_name TEXT NOT NULL DEFAULT '',
                read_time TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                published_at TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_journal_status ON journal_articles(status, published_at DESC)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                ip TEXT NOT NULL DEFAULT '',
                country TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                user_agent TEXT NOT NULL DEFAULT '',
                referrer TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_jv_article ON journal_views(article_id, created_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_jv_ip ON journal_views(article_id, ip, created_at)"
        )


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "slug": r["slug"],
        "title": r["title"],
        "category": r["category"],
        "tone": r["tone"],
        "intro": r["intro"],
        "content": r["content"],
        "product_sku": r["product_sku"],
        "product_name": r["product_name"],
        "read_time": r["read_time"],
        "status": r["status"],
        "created_at": r["created_at"],
        "published_at": r["published_at"],
    }


def add_article(slug: str, title: str, category: str, tone: str, intro: str,
                content: str, product_sku: str = "", product_name: str = "",
                read_time: str = "", status: str = "draft") -> int:
    init_journal()
    now = datetime.now(_MSK).isoformat()
    with _db() as connection:
        # уникализируем slug
        base, i, s = slug, 2, slug
        while connection.execute("SELECT 1 FROM journal_articles WHERE slug = ?", (s,)).fetchone():
            s = f"{base}-{i}"
            i += 1
        cur = connection.execute(
            """INSERT INTO journal_articles
               (slug, title, category, tone, intro, content, product_sku, product_name, read_time, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (s, title, category, tone, intro, content, product_sku, product_name, read_time, status, now),
        )
        return cur.lastrowid


def get_article(article_id: int) -> dict | None:
    init_journal()
    with _db() as connection:
        r = connection.execute("SELECT * FROM journal_articles WHERE id = ?", (article_id,)).fetchone()
        return _row(r) if r else None


def get_by_slug(slug: str, published_only: bool = True) -> dict | None:
    init_journal()
    with _db() as connection:
        q = "SELECT * FROM journal_articles WHERE slug = ?"
        if published_only:
            q += " AND status = 'published'"
        r = connection.execute(q, (slug,)).fetchone()
        return _row(r) if r else None


def list_articles(status: str | None = None, limit: int = 200) -> list[dict]:
    init_journal()
    with _db() as connection:
        if status:
            rows = connection.execute(
                "SELECT * FROM journal_articles WHERE status = ? ORDER BY COALESCE(published_at, created_at) DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM journal_articles ORDER BY COALESCE(published_at, created_at) DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row(r) for r in rows]


def mark_published(article_id: int) -> dict | None:
    init_journal()
    now = datetime.now(_MSK).isoformat()
    with _db() as connection:
        connection.execute(
            "UPDATE journal_articles SET status = 'published', published_at = ? WHERE id = ?",
            (now, article_id),
        )
    return get_article(article_id)


def delete_article(article_id: int) -> bool:
    init_journal()
    with _db() as connection:
        connection.execute("DELETE FROM journal_views WHERE article_id = ?", (article_id,))
        cur = connection.execute("DELETE FROM journal_articles WHERE id = ?", (article_id,))
        return cur.rowcount > 0


def update_article(article_id: int, title: str | None = None, category: str | None = None,
                   intro: str | None = None, content: str | None = None,
                   slug: str | None = None, tone: str | None = None,
                   read_time: str | None = None, status: str | None = None) -> dict | None:
    """Редактирование статьи из админки: обновляет только переданные поля."""
    init_journal()
    fields = {"title": title, "category": category, "intro": intro, "content": content,
              "slug": slug, "tone": tone, "read_time": read_time, "status": status}
    sets, params = [], []
    for key, val in fields.items():
        if val is not None:
            sets.append(f"{key} = ?")
            params.append(val)
    if not sets:
        return get_article(article_id)
    with _db() as connection:
        if slug:
            r = connection.execute(
                "SELECT id FROM journal_articles WHERE slug = ? AND id != ?",
                (slug, article_id),
            ).fetchone()
            if r:
                raise ValueError(f"Slug '{slug}' уже занят другой статьёй")
        params.append(article_id)
        connection.execute(
            f"UPDATE journal_articles SET {', '.join(sets)} WHERE id = ?", params
        )
    return get_article(article_id)


def used_skus() -> set[str]:
    """SKU товаров, по которым уже есть статьи (draft или published) — чтобы не дублировать темы."""
    init_journal()
    with _db() as connection:
        rows = connection.execute(
            "SELECT DISTINCT product_sku FROM journal_articles WHERE product_sku != ''"
        ).fetchall()
        return {r["product_sku"] for r in rows}


def published_today_count() -> int:
    init_journal()
    today = datetime.now(_MSK).strftime("%Y-%m-%d")
    with _db() as connection:
        r = connection.execute(
            "SELECT COUNT(*) c FROM journal_articles WHERE status = 'published' AND published_at LIKE ?",
            (f"{today}%",),
        ).fetchone()
        return r["c"]


# ---------- Просмотры статей (аналитика: кто читал, откуда) ----------

_DEDUP_MINUTES = 30  # повторный хит с того же IP за 30 мин — не новый просмотр


def recent_view_exists(article_id: int, ip: str) -> bool:
    """Проверка дедупликации ДО геолокации — чтобы не дёргать ip-api лишний раз."""
    init_journal()
    if not ip:
        return False
    since = (datetime.now(_MSK) - timedelta(minutes=_DEDUP_MINUTES)).isoformat()
    with _db() as connection:
        r = connection.execute(
            "SELECT 1 FROM journal_views WHERE article_id = ? AND ip = ? AND created_at > ? LIMIT 1",
            (article_id, ip, since),
        ).fetchone()
        return r is not None


def record_view(article_id: int, ip: str = "", country: str = "", city: str = "",
                user_agent: str = "", referrer: str = "") -> int:
    init_journal()
    now = datetime.now(_MSK).isoformat()
    with _db() as connection:
        cur = connection.execute(
            """INSERT INTO journal_views
               (article_id, ip, country, city, user_agent, referrer, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (article_id, ip, country, city, user_agent, referrer, now),
        )
        return cur.lastrowid


def view_counts() -> dict[int, int]:
    """Карта article_id -> число просмотров (для списков в админке)."""
    init_journal()
    with _db() as connection:
        rows = connection.execute(
            "SELECT article_id, COUNT(*) c FROM journal_views GROUP BY article_id"
        ).fetchall()
        return {r["article_id"]: r["c"] for r in rows}


def article_stats(article_id: int) -> dict:
    """Статистика по статье: всего, уникальные IP, страны, последние визиты."""
    init_journal()
    with _db() as connection:
        total = connection.execute(
            "SELECT COUNT(*) c FROM journal_views WHERE article_id = ?", (article_id,)
        ).fetchone()["c"]
        unique = connection.execute(
            "SELECT COUNT(DISTINCT ip) c FROM journal_views WHERE article_id = ?", (article_id,)
        ).fetchone()["c"]
        countries = connection.execute(
            """SELECT country, COUNT(*) c FROM journal_views
               WHERE article_id = ? GROUP BY country ORDER BY c DESC LIMIT 15""",
            (article_id,),
        ).fetchall()
        recent = connection.execute(
            """SELECT ip, country, city, user_agent, referrer, created_at
               FROM journal_views WHERE article_id = ?
               ORDER BY created_at DESC LIMIT 20""",
            (article_id,),
        ).fetchall()
    return {
        "total": total,
        "unique_ips": unique,
        "countries": [{"country": r["country"] or "Неизвестно", "count": r["c"]} for r in countries],
        "recent": [dict(r) for r in recent],
    }
