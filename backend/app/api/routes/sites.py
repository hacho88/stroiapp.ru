import asyncio
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
from fastapi import APIRouter, Body

router = APIRouter(prefix="/sites", tags=["sites"])

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"

# Дефолтный список — зеркало app/lib/cities.js из moscow.stroiapp.ru
DEFAULT_CITIES = [
    ("moscow", "Москва", "Москва", 2, 300),
    ("khimki", "Химки", "Московская область", 24, 500),
    ("balashikha", "Балашиха", "Московская область", 24, 500),
    ("podolsk", "Подольск", "Московская область", 24, 500),
    ("mytishchi", "Мытищи", "Московская область", 24, 500),
    ("korolyov", "Королёв", "Московская область", 24, 500),
    ("lyubertsy", "Люберцы", "Московская область", 24, 500),
    ("krasnogorsk", "Красногорск", "Московская область", 24, 500),
    ("odintsovo", "Одинцово", "Московская область", 24, 500),
    ("domodedovo", "Домодедово", "Московская область", 24, 500),
    ("elektrostal", "Электросталь", "Московская область", 24, 600),
    ("kolomna", "Коломна", "Московская область", 24, 600),
    ("serpukhov", "Серпухов", "Московская область", 24, 600),
    ("zelenograd", "Зеленоград", "Москва", 24, 500),
    ("dmitrov", "Дмитров", "Московская область", 24, 500),
    ("tver", "Тверь", "Тверская область", 24, 800),
    ("yaroslavl", "Ярославль", "Ярославская область", 24, 800),
    ("vladimir", "Владимир", "Владимирская область", 18, 700),
    ("vologda", "Вологда", "Вологодская область", 48, 1500),
    ("cherepovets", "Череповец", "Вологодская область", 48, 1500),
]

FIXED_SITES: list[dict] = []


@contextmanager
def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init():
    with _db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS geo_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                region TEXT DEFAULT '',
                hours INTEGER DEFAULT 24,
                cost INTEGER DEFAULT 500,
                enabled INTEGER NOT NULL DEFAULT 1,
                deployed INTEGER NOT NULL DEFAULT 0
            )"""
        )
        count = conn.execute("SELECT COUNT(*) AS c FROM geo_sites").fetchone()["c"]
        if count == 0:
            conn.executemany(
                "INSERT INTO geo_sites (slug, name, region, hours, cost) VALUES (?, ?, ?, ?, ?)",
                DEFAULT_CITIES,
            )


def _geo_sites() -> list[dict]:
    _init()
    with _db() as conn:
        rows = conn.execute("SELECT * FROM geo_sites ORDER BY id ASC").fetchall()
    return [
        {
            "id": f"geo-{r['slug']}",
            "db_id": r["id"],
            "type": "geo",
            "name": f"Гео-сайт — {r['name']}",
            "domain": f"{r['slug']}.stroiapp.ru",
            "url": f"https://{r['slug']}.stroiapp.ru",
            "slug": r["slug"],
            "city": r["name"],
            "region": r["region"],
            "hours": r["hours"],
            "cost": r["cost"],
            "enabled": bool(r["enabled"]),
            "deployed": bool(r["deployed"]),
        }
        for r in rows
    ]


async def _check(url: str) -> dict:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(verify=False, timeout=8, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "AI-StroiApp-Monitor/1.0"})
            ms = int((time.monotonic() - start) * 1000)
            return {"online": resp.status_code < 400, "http_code": resp.status_code, "response_ms": ms}
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return {"online": False, "http_code": 0, "response_ms": ms, "error": type(exc).__name__}


@router.get("/list")
async def sites_list(check: bool = True):
    """All sites: OpenCart main + admin + geo subdomains from DB, with availability check."""
    sites = [dict(s) for s in FIXED_SITES] + _geo_sites()
    if check:
        results = await asyncio.gather(*(_check(s["url"]) for s in sites))
        for s, r in zip(sites, results):
            s.update(r)
            if s["type"] == "geo" and r.get("online") and not s.get("deployed"):
                s["deployed"] = True
    online = sum(1 for s in sites if s.get("online"))
    return {"status": "ok", "total": len(sites), "online": online, "sites": sites}


def _clean_slug(slug: str) -> str:
    import re
    return re.sub(r"[^a-z0-9-]+", "", (slug or "").strip().lower())


@router.post("/add")
async def sites_add(payload: dict = Body(...)):
    """Add a geo subdomain."""
    try:
        _init()
        slug = _clean_slug(payload.get("slug"))
        name = (payload.get("name") or "").strip()
        if not slug or not name:
            return {"status": "error", "detail": "slug и name обязательны"}
        with _db() as conn:
            exists = conn.execute("SELECT id FROM geo_sites WHERE slug = ?", (slug,)).fetchone()
            if exists:
                return {"status": "error", "detail": f"Поддомен {slug} уже есть"}
            conn.execute(
                "INSERT INTO geo_sites (slug, name, region, hours, cost) VALUES (?, ?, ?, ?, ?)",
                (slug, name, (payload.get("region") or "").strip(), int(payload.get("hours") or 24), int(payload.get("cost") or 500)),
            )
        return {"status": "ok", "slug": slug}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/update")
async def sites_update(payload: dict = Body(...)):
    """Update a geo subdomain (name, region, hours, cost, enabled, deployed)."""
    try:
        _init()
        db_id = int(payload.get("id") or 0)
        if not db_id:
            return {"status": "error", "detail": "id is required"}
        fields, params = [], []
        for col in ("name", "region"):
            if payload.get(col) is not None:
                fields.append(f"{col} = ?")
                params.append(str(payload[col]).strip())
        for col in ("hours", "cost"):
            if payload.get(col) is not None:
                fields.append(f"{col} = ?")
                params.append(int(payload[col]))
        for col in ("enabled", "deployed"):
            if payload.get(col) is not None:
                fields.append(f"{col} = ?")
                params.append(1 if payload[col] else 0)
        if payload.get("slug"):
            fields.append("slug = ?")
            params.append(_clean_slug(payload["slug"]))
        if not fields:
            return {"status": "error", "detail": "nothing to update"}
        params.append(db_id)
        with _db() as conn:
            conn.execute(f"UPDATE geo_sites SET {', '.join(fields)} WHERE id = ?", params)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/delete")
async def sites_delete(payload: dict = Body(...)):
    """Delete a geo subdomain from the list."""
    try:
        _init()
        db_id = int(payload.get("id") or 0)
        if not db_id:
            return {"status": "error", "detail": "id is required"}
        with _db() as conn:
            conn.execute("DELETE FROM geo_sites WHERE id = ?", (db_id,))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
