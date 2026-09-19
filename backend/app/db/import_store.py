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
    """Yield a connection, commit on success, always close (frees the fd)."""
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
            CREATE TABLE IF NOT EXISTS imported_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                xml_id TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                image TEXT DEFAULT '',
                image_path TEXT DEFAULT '',
                cat0 TEXT DEFAULT '',
                cat1 TEXT DEFAULT '',
                cat2 TEXT DEFAULT '',
                weight REAL DEFAULT 0,
                width REAL DEFAULT 0,
                height REAL DEFAULT 0,
                length REAL DEFAULT 0,
                price REAL DEFAULT 0,
                prop_type TEXT DEFAULT '',
                prop_app TEXT DEFAULT '',
                prop_216 TEXT DEFAULT '',
                sku TEXT DEFAULT '',
                pushed INTEGER NOT NULL DEFAULT 0,
                product_id INTEGER,
                date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_imported_name ON imported_products(name)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_imported_cat ON imported_products(cat0, cat1, cat2)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_imported_pushed ON imported_products(pushed)")


def bulk_insert(products: list[dict]) -> dict:
    """Insert products, skipping duplicates by xml_id. Returns counts."""
    init_db()
    inserted = 0
    skipped = 0
    with _db() as connection:
        for p in products:
            try:
                connection.execute(
                    """
                    INSERT INTO imported_products
                        (xml_id, name, description, image, image_path, cat0, cat1, cat2,
                         weight, width, height, length, price, prop_type, prop_app, prop_216, sku)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(p.get("xml_id") or ""),
                        p.get("name") or "",
                        p.get("description") or "",
                        p.get("image") or "",
                        p.get("image_path") or "",
                        p.get("cat0") or "",
                        p.get("cat1") or "",
                        p.get("cat2") or "",
                        float(p.get("weight") or 0),
                        float(p.get("width") or 0),
                        float(p.get("height") or 0),
                        float(p.get("length") or 0),
                        float(p.get("price") or 0),
                        p.get("prop_type") or "",
                        p.get("prop_app") or "",
                        str(p.get("prop_216") or ""),
                        p.get("sku") or "",
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
    return {"inserted": inserted, "skipped": skipped}


def list_products(limit: int = 50, page: int = 1, search: str = "", cat0: str = "", cat1: str = "", cat2: str = "", pushed: int | None = None) -> dict:
    init_db()
    where = []
    params: list = []
    if search:
        where.append("(name LIKE ? OR sku LIKE ? OR xml_id LIKE ?)")
        like = f"%{search}%"
        params += [like, like, like]
    if cat0:
        where.append("cat0 = ?")
        params.append(cat0)
    if cat1:
        where.append("cat1 = ?")
        params.append(cat1)
    if cat2:
        where.append("cat2 = ?")
        params.append(cat2)
    if pushed is not None:
        where.append("pushed = ?")
        params.append(pushed)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    offset = max(0, (page - 1) * limit)
    with _db() as connection:
        total = connection.execute(f"SELECT COUNT(*) AS c FROM imported_products{where_sql}", params).fetchone()["c"]
        rows = connection.execute(
            f"SELECT * FROM imported_products{where_sql} ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return {"total": total, "page": page, "limit": limit, "products": [dict(r) for r in rows]}


def category_tree() -> list[dict]:
    """Nested category tree cat0 -> cat1 -> cat2 with product counts."""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT cat0, cat1, cat2, COUNT(*) AS c FROM imported_products GROUP BY cat0, cat1, cat2 ORDER BY cat0, cat1, cat2"
        ).fetchall()
    tree: dict = {}
    order: list = []
    for r in rows:
        c0 = r["cat0"] or "Без категории"
        c1 = r["cat1"] or ""
        c2 = r["cat2"] or ""
        if c0 not in tree:
            tree[c0] = {"name": c0, "count": 0, "children": {}, "_order": []}
            order.append(c0)
        node0 = tree[c0]
        node0["count"] += r["c"]
        if not c1:
            continue
        if c1 not in node0["children"]:
            node0["children"][c1] = {"name": c1, "count": 0, "children": {}}
            node0["_order"].append(c1)
        node1 = node0["children"][c1]
        node1["count"] += r["c"]
        if not c2:
            continue
        if c2 not in node1["children"]:
            node1["children"][c2] = {"name": c2, "count": 0, "children": {}}
        node1["children"][c2]["count"] += r["c"]

    def finalize(node):
        kids = node.get("children", {})
        node["children"] = [finalize(kids[k]) for k in sorted(kids.keys())]
        node.pop("_order", None)
        return node

    return [finalize(tree[k]) for k in sorted(tree.keys())]


def get_product(item_id: int) -> dict | None:
    init_db()
    with _db() as connection:
        row = connection.execute("SELECT * FROM imported_products WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def mark_pushed(item_id: int, product_id: int) -> None:
    init_db()
    with _db() as connection:
        connection.execute("UPDATE imported_products SET pushed = 1, product_id = ? WHERE id = ?", (product_id, item_id))


def delete_product(item_id: int) -> None:
    init_db()
    with _db() as connection:
        connection.execute("DELETE FROM imported_products WHERE id = ?", (item_id,))


def clear_all() -> int:
    init_db()
    with _db() as connection:
        cur = connection.execute("DELETE FROM imported_products")
        return cur.rowcount


def stats() -> dict:
    init_db()
    with _db() as connection:
        total = connection.execute("SELECT COUNT(*) AS c FROM imported_products").fetchone()["c"]
        pushed = connection.execute("SELECT COUNT(*) AS c FROM imported_products WHERE pushed = 1").fetchone()["c"]
        cats = connection.execute("SELECT cat0, COUNT(*) AS c FROM imported_products GROUP BY cat0 ORDER BY c DESC").fetchall()
    return {"total": total, "pushed": pushed, "categories": [{"name": r["cat0"], "count": r["c"]} for r in cats]}


def set_image(item_id: int, image_path: str) -> None:
    init_db()
    with _db() as connection:
        connection.execute("UPDATE imported_products SET image = ? WHERE id = ?", (image_path, item_id))


def count_needing_images() -> int:
    """Products that have a source image_path but no uploaded OpenCart image yet."""
    init_db()
    with _db() as connection:
        return connection.execute(
            "SELECT COUNT(*) AS c FROM imported_products WHERE (image_path != '' OR (image != '' AND image IS NOT NULL)) AND image NOT LIKE 'catalog/%' AND image != 'NOIMAGE'"
        ).fetchone()["c"]


def get_needing_images(limit: int = 100, offset: int = 0) -> list[dict]:
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT id, name, image, image_path FROM imported_products WHERE (image_path != '' OR (image != '' AND image IS NOT NULL)) AND image NOT LIKE 'catalog/%' AND image != 'NOIMAGE' ORDER BY id ASC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]
