"""Хранилище покупателей витрины: списки «Избранное» и «Сравнение» по токену сессии.

SQLite (тот же app.db, что и product_costs). Токен выдаётся /storefront/auth/verify
и детерминирован на номер телефона — списки переживают перелогины и устройства.
"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS storefront_users (
                token TEXT PRIMARY KEY,
                phone TEXT NOT NULL DEFAULT '',
                wishlist TEXT NOT NULL DEFAULT '[]',
                compare TEXT NOT NULL DEFAULT '[]',
                name TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                inn TEXT NOT NULL DEFAULT '',
                kpp TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # миграция: таблица могла быть создана старой версией без профиля
        cols = {r[1] for r in conn.execute("PRAGMA table_info(storefront_users)")}
        for col in ("name", "email", "inn", "kpp", "company"):
            if col not in cols:
                conn.execute(
                    f"ALTER TABLE storefront_users ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS storefront_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                street TEXT NOT NULL DEFAULT '',
                contact_name TEXT NOT NULL DEFAULT '',
                contact_phone TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS storefront_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS storefront_calcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Заказы витрины moscow.stroiapp.ru (заявки наличными + безналичные счета)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS storefront_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL DEFAULT 'moscow.stroiapp.ru',
                name TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                inn TEXT NOT NULL DEFAULT '',
                payment TEXT NOT NULL DEFAULT '',
                total REAL NOT NULL DEFAULT 0,
                items TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Акции/скидки/комплекты витрин — site_owner привязывает к сайту
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_owner TEXT NOT NULL DEFAULT 'moscow',
                name TEXT NOT NULL DEFAULT '',
                type TEXT NOT NULL DEFAULT 'bundle',
                discount_pct REAL NOT NULL DEFAULT 0,
                items TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS promotion_kits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_owner TEXT NOT NULL DEFAULT 'moscow',
                title TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                items TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _loads(raw: str):
    try:
        v = json.loads(raw or "[]")
        return v if isinstance(v, list) else []
    except Exception:
        return []


def ensure_user(token: str, phone: str = "") -> None:
    if not token:
        return
    init_db()
    with _db() as conn:
        conn.execute(
            "INSERT INTO storefront_users (token, phone) VALUES (?, ?) "
            "ON CONFLICT(token) DO UPDATE SET phone = excluded.phone, "
            "updated_at = CURRENT_TIMESTAMP",
            (token, phone),
        )


def get_lists(token: str) -> dict:
    init_db()
    with _db() as conn:
        row = conn.execute(
            "SELECT wishlist, compare FROM storefront_users WHERE token = ?", (token,)
        ).fetchone()
    if not row:
        return {"wishlist": [], "compare": []}
    return {"wishlist": _loads(row["wishlist"]), "compare": _loads(row["compare"])}


def _merge(local: list, remote: list) -> list:
    """union по id товара; удалённые из local элементы не воскрешаем —
    merge только добавляет то, чего нет локально."""
    seen, out = set(), []
    for item in [*(local or []), *(remote or [])]:
        if not isinstance(item, dict):
            continue
        iid = item.get("id", item.get("product_id", item.get("sku")))
        if iid is None or iid in seen:
            continue
        seen.add(iid)
        out.append(item)
    return out


def sync_lists(token: str, wishlist: list, compare: list) -> dict:
    """Слияние: сервер = объединение серверного и присланного списков."""
    ensure_user(token)
    server = get_lists(token)
    merged = {
        "wishlist": _merge(wishlist, server["wishlist"]),
        "compare": _merge(compare, server["compare"]),
    }
    with _db() as conn:
        conn.execute(
            "UPDATE storefront_users SET wishlist = ?, compare = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE token = ?",
            (json.dumps(merged["wishlist"], ensure_ascii=False),
             json.dumps(merged["compare"], ensure_ascii=False), token),
        )
    return merged


# ---------- Профиль ----------

PROFILE_FIELDS = ("name", "email", "inn", "kpp", "company")


def get_profile(token: str) -> dict:
    init_db()
    with _db() as conn:
        row = conn.execute(
            "SELECT phone, name, email, inn, kpp, company FROM storefront_users WHERE token = ?",
            (token,),
        ).fetchone()
    if not row:
        return {}
    return {k: row[k] for k in ("phone", *PROFILE_FIELDS)}


def save_profile(token: str, data: dict) -> dict:
    ensure_user(token)
    sets = {k: str(data.get(k) or "")[:255] for k in PROFILE_FIELDS}
    with _db() as conn:
        conn.execute(
            "UPDATE storefront_users SET name = ?, email = ?, inn = ?, kpp = ?, "
            "company = ?, updated_at = CURRENT_TIMESTAMP WHERE token = ?",
            (sets["name"], sets["email"], sets["inn"], sets["kpp"], sets["company"], token),
        )
    return get_profile(token)


# ---------- Объекты доставки ----------

def list_addresses(token: str) -> list:
    init_db()
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, title, city, street, contact_name, contact_phone, created_at "
            "FROM storefront_addresses WHERE token = ? ORDER BY id DESC", (token,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_address(token: str, data: dict) -> dict:
    ensure_user(token)
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO storefront_addresses (token, title, city, street, contact_name, contact_phone) "
            "VALUES (?,?,?,?,?,?)",
            (token, str(data.get("title") or "")[:255], str(data.get("city") or "")[:255],
             str(data.get("street") or "")[:255], str(data.get("contact_name") or "")[:255],
             str(data.get("contact_phone") or "")[:64]),
        )
        aid = cur.lastrowid
    return {"id": aid}


def delete_address(token: str, address_id: int) -> bool:
    init_db()
    with _db() as conn:
        cur = conn.execute(
            "DELETE FROM storefront_addresses WHERE id = ? AND token = ?", (address_id, token),
        )
        return cur.rowcount > 0


# ---------- Документы (счета) и расчёты ИИ ----------

def _list_items(table: str, token: str) -> list:
    init_db()
    with _db() as conn:
        rows = conn.execute(
            f"SELECT id, title, created_at FROM {table} WHERE token = ? ORDER BY id DESC", (token,),
        ).fetchall()
    return [dict(r) for r in rows]


def _add_item(table: str, token: str, title: str, payload) -> int:
    ensure_user(token)
    with _db() as conn:
        cur = conn.execute(
            f"INSERT INTO {table} (token, title, payload) VALUES (?,?,?)",
            (token, str(title or "")[:255],
             json.dumps(payload if payload is not None else {}, ensure_ascii=False)),
        )
        return cur.lastrowid


def _get_item(table: str, token: str, item_id: int):
    init_db()
    with _db() as conn:
        row = conn.execute(
            f"SELECT id, title, payload, created_at FROM {table} WHERE id = ? AND token = ?",
            (item_id, token),
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    try:
        d["payload"] = json.loads(d["payload"])
    except Exception:
        d["payload"] = {}
    return d


def list_docs(token: str) -> list:
    return _list_items("storefront_docs", token)


def add_doc(token: str, title: str, payload) -> int:
    return _add_item("storefront_docs", token, title, payload)


def get_doc(token: str, doc_id: int):
    return _get_item("storefront_docs", token, doc_id)


def list_calcs(token: str) -> list:
    return _list_items("storefront_calcs", token)


def add_calc(token: str, title: str, payload) -> int:
    return _add_item("storefront_calcs", token, title, payload)


def get_calc(token: str, calc_id: int):
    return _get_item("storefront_calcs", token, calc_id)


# ---------- Заказы витрины (moscow.stroiapp.ru) ----------

def add_order(data: dict) -> int:
    """Заявка наличными или безналичный счёт с витрины."""
    init_db()
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO storefront_orders (source, name, phone, address, inn, payment, total, items, status) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (str(data.get("source") or "moscow.stroiapp.ru")[:64],
             str(data.get("name") or "")[:255], str(data.get("phone") or "")[:64],
             str(data.get("address") or "")[:512], str(data.get("inn") or "")[:32],
             str(data.get("payment") or "")[:64], float(data.get("total") or 0),
             json.dumps(data.get("items") or [], ensure_ascii=False),
             str(data.get("status") or "new")[:32]),
        )
        return cur.lastrowid


def list_orders(source: str = "", limit: int = 500) -> list:
    init_db()
    with _db() as conn:
        if source:
            rows = conn.execute(
                "SELECT * FROM storefront_orders WHERE source = ? ORDER BY id DESC LIMIT ?",
                (source, int(limit))).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM storefront_orders ORDER BY id DESC LIMIT ?",
                (int(limit),)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["items"] = json.loads(d["items"] or "[]")
        except Exception:
            d["items"] = []
        out.append(d)
    return out


def set_order_status(order_id: int, status: str) -> bool:
    init_db()
    with _db() as conn:
        cur = conn.execute(
            "UPDATE storefront_orders SET status = ? WHERE id = ?",
            (str(status)[:32], int(order_id)))
        return cur.rowcount > 0


# ---------- Акции и комплекты витрин (site_owner) ----------

def add_promotion(data: dict) -> int:
    init_db()
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO promotions (site_owner, name, type, discount_pct, items, status) VALUES (?,?,?,?,?,?)",
            (str(data.get("site_owner") or "moscow")[:32],
             str(data.get("name") or "")[:255], str(data.get("type") or "bundle")[:32],
             float(data.get("discount_pct") or 0),
             json.dumps(data.get("items") or [], ensure_ascii=False),
             str(data.get("status") or "active")[:32]),
        )
        return cur.lastrowid


def update_promotion(pid: int, data: dict) -> bool:
    init_db()
    fields, vals = [], []
    for k in ("name", "type", "status"):
        if k in data:
            fields.append(f"{k} = ?")
            vals.append(str(data[k])[:255])
    if "discount_pct" in data:
        fields.append("discount_pct = ?")
        vals.append(float(data["discount_pct"] or 0))
    if "items" in data:
        fields.append("items = ?")
        vals.append(json.dumps(data["items"] or [], ensure_ascii=False))
    if not fields:
        return False
    vals.append(int(pid))
    with _db() as conn:
        return conn.execute(
            f"UPDATE promotions SET {', '.join(fields)} WHERE id = ?", vals).rowcount > 0


def list_promotions(site_owner: str = "") -> list:
    init_db()
    with _db() as conn:
        if site_owner:
            rows = conn.execute(
                "SELECT * FROM promotions WHERE site_owner = ? ORDER BY id DESC",
                (site_owner,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM promotions ORDER BY id DESC").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["items"] = json.loads(d["items"] or "[]")
        except Exception:
            d["items"] = []
        out.append(d)
    return out


def delete_promotion(pid: int) -> bool:
    init_db()
    with _db() as conn:
        return conn.execute("DELETE FROM promotions WHERE id = ?", (int(pid),)).rowcount > 0


def add_kit(data: dict) -> int:
    init_db()
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO promotion_kits (site_owner, title, note, items, status) VALUES (?,?,?,?,?)",
            (str(data.get("site_owner") or "moscow")[:32],
             str(data.get("title") or "")[:255], str(data.get("note") or "")[:255],
             json.dumps(data.get("items") or [], ensure_ascii=False),
             str(data.get("status") or "active")[:32]),
        )
        return cur.lastrowid


def update_kit(kit_id: int, data: dict) -> bool:
    init_db()
    fields, vals = [], []
    for k in ("title", "note", "status"):
        if k in data:
            fields.append(f"{k} = ?")
            vals.append(str(data[k])[:255])
    if "items" in data:
        fields.append("items = ?")
        vals.append(json.dumps(data["items"] or [], ensure_ascii=False))
    if not fields:
        return False
    vals.append(int(kit_id))
    with _db() as conn:
        return conn.execute(
            f"UPDATE promotion_kits SET {', '.join(fields)} WHERE id = ?", vals).rowcount > 0


def list_kits(site_owner: str = "", active_only: bool = False) -> list:
    init_db()
    sql = "SELECT * FROM promotion_kits"
    cond, args = [], []
    if site_owner:
        cond.append("site_owner = ?")
        args.append(site_owner)
    if active_only:
        cond.append("status = 'active'")
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    sql += " ORDER BY id DESC"
    with _db() as conn:
        rows = conn.execute(sql, args).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["items"] = json.loads(d["items"] or "[]")
        except Exception:
            d["items"] = []
        out.append(d)
    return out


def delete_kit(kit_id: int) -> bool:
    init_db()
    with _db() as conn:
        return conn.execute("DELETE FROM promotion_kits WHERE id = ?", (int(kit_id),)).rowcount > 0
