"""Персистентная память каталог-ядра (self-learning).

Три таблицы в app.db:
- learned_alias: фраза из спецификации → sku (кто подтвердил/выбрал — hits растёт);
- rejected_match: фраза → sku, который НЕ подходит (пользователь удалил строку);
- not_found_obs: фразы, которым ядро не нашло товара (учебный спрос: что
  регулярно ищут, но чего нет в каталоге — материал для докупки ассортимента).
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"

# Ревизия learn-таблиц: catalog_core перестраивает индекс, когда она растёт.
_REV = 0


def _bump() -> None:
    global _REV
    _REV += 1


def learn_store_learn_rev() -> int:
    return _REV


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
            CREATE TABLE IF NOT EXISTS learned_alias (
                phrase TEXT NOT NULL,
                sku TEXT NOT NULL,
                hits INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'feedback',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (phrase, sku)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rejected_match (
                phrase TEXT NOT NULL,
                sku TEXT NOT NULL,
                hits INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (phrase, sku)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS not_found_obs (
                phrase TEXT PRIMARY KEY,
                hits INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'spec',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS match_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT,
                sku TEXT,
                verdict TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS domain_knowledge (
                domain TEXT NOT NULL,
                term TEXT NOT NULL,
                target TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL DEFAULT 'term',
                hits INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'core',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (domain, term, target)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_units (
                sku TEXT PRIMARY KEY,
                unit TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'ai',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_link (
                sku_a TEXT NOT NULL,
                sku_b TEXT NOT NULL,
                hits INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'spec',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (sku_a, sku_b)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_dims (
                sku TEXT PRIMARY KEY,
                weight_kg REAL NOT NULL DEFAULT 0,
                length_mm REAL NOT NULL DEFAULT 0,
                width_mm REAL NOT NULL DEFAULT 0,
                height_mm REAL NOT NULL DEFAULT 0,
                volume_l REAL NOT NULL DEFAULT 0,
                pack TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'core',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# ---------- learned_alias ----------

def learn_alias(phrase: str, sku: str, source: str = "feedback") -> None:
    phrase = " ".join((phrase or "").split())[:160].lower()
    sku = (sku or "").strip()
    if not phrase or not sku:
        return
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO learned_alias (phrase, sku, hits, source, updated_at)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(phrase, sku) DO UPDATE SET
                hits = hits + 1,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            (phrase, sku, source),
        )
        connection.execute(
            "INSERT INTO match_log (phrase, sku, verdict) VALUES (?, ?, 'accepted')",
            (phrase, sku),
        )
    _bump()


def get_learned_aliases() -> dict[str, dict[str, int]]:
    """{phrase: {sku: hits}}"""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT phrase, sku, hits FROM learned_alias"
        ).fetchall()
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["phrase"], {})[r["sku"]] = int(r["hits"])
    return out


# ---------- rejected_match ----------

def reject_match(phrase: str, sku: str) -> None:
    phrase = " ".join((phrase or "").split())[:160].lower()
    sku = (sku or "").strip()
    if not phrase or not sku:
        return
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO rejected_match (phrase, sku, hits, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(phrase, sku) DO UPDATE SET
                hits = hits + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (phrase, sku),
        )
        connection.execute(
            "INSERT INTO match_log (phrase, sku, verdict) VALUES (?, ?, 'rejected')",
            (phrase, sku),
        )
    _bump()


def get_rejected() -> dict[str, dict[str, int]]:
    """{phrase: {sku: hits}}"""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT phrase, sku, hits FROM rejected_match"
        ).fetchall()
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["phrase"], {})[r["sku"]] = int(r["hits"])
    return out


# ---------- not_found_obs ----------

def observe_not_found(phrase: str, source: str = "spec") -> None:
    phrase = " ".join((phrase or "").split())[:160].lower()
    if not phrase:
        return
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO not_found_obs (phrase, hits, source, updated_at)
            VALUES (?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(phrase) DO UPDATE SET
                hits = hits + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (phrase, source),
        )
    _bump()


def top_not_found(limit: int = 50) -> list[dict]:
    """Самые частые ненайденные фразы — спрос, которого нет в каталоге."""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT phrase, hits, source, updated_at FROM not_found_obs "
            "ORDER BY hits DESC, updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def learn_stats() -> dict:
    init_db()
    with _db() as connection:
        aliases = connection.execute("SELECT COUNT(*) c FROM learned_alias").fetchone()["c"]
        rejected = connection.execute("SELECT COUNT(*) c FROM rejected_match").fetchone()["c"]
        notfound = connection.execute("SELECT COUNT(*) c FROM not_found_obs").fetchone()["c"]
        log = connection.execute("SELECT COUNT(*) c FROM match_log").fetchone()["c"]
    return {"aliases": aliases, "rejected": rejected,
            "not_found": notfound, "log_rows": log}


# ---------- domain_knowledge: ядро знает все разделы ----------

def learn_domain(domain: str, term: str, target: str = "",
                 kind: str = "term", source: str = "feedback") -> None:
    """Выучить термин/факт раздела: ('tenders','нмцк','начальная цена','fact').
    target — к чему привязано (sku/город/действие), kind: term|alias|fact|rule."""
    domain = (domain or "").strip().lower()[:40]
    term = " ".join((term or "").split())[:160].lower()
    target = (target or "").strip()[:160]
    if not domain or not term:
        return
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO domain_knowledge (domain, term, target, kind, hits, source, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(domain, term, target) DO UPDATE SET
                hits = hits + 1,
                kind = excluded.kind,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            (domain, term, target, kind, source),
        )
        connection.execute(
            "INSERT INTO match_log (phrase, sku, verdict) VALUES (?, ?, ?)",
            (term, target, f"domain:{domain}"),
        )
    _bump()


def get_domain_terms(domain: str | None = None) -> dict[str, dict[str, int]]:
    """{domain: {term: hits}} — выученные термины разделов (все или одного)."""
    init_db()
    with _db() as connection:
        if domain:
            rows = connection.execute(
                "SELECT domain, term, hits FROM domain_knowledge WHERE domain = ?",
                (domain.strip().lower(),),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT domain, term, hits FROM domain_knowledge"
            ).fetchall()
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["domain"], {})[r["term"]] = int(r["hits"])
    return out


def domain_stats() -> dict[str, int]:
    """{domain: число выученных терминов}"""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT domain, COUNT(*) c FROM domain_knowledge GROUP BY domain"
        ).fetchall()
    return {r["domain"]: int(r["c"]) for r in rows}


# ---------- few-shot: топ выученных связей для промпта ----------

def top_aliases(limit: int = 15) -> list[dict]:
    """Топ выученных пар phrase→sku по hits — few-shot для DeepSeek."""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT phrase, sku, hits FROM learned_alias "
            "ORDER BY hits DESC, updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"phrase": r["phrase"], "sku": r["sku"], "hits": int(r["hits"])}
            for r in rows]


def get_alias_rows(sku: str) -> list[dict]:
    """Все выученные фразы конкретного sku с hits и source — досье товара."""
    init_db()
    with _db() as connection:
        rows = connection.execute(
            "SELECT phrase, hits, source, updated_at FROM learned_alias "
            "WHERE sku = ? ORDER BY hits DESC",
            (sku,),
        ).fetchall()
    return [{"phrase": r["phrase"], "hits": int(r["hits"]),
             "source": r["source"], "updated_at": r["updated_at"]}
            for r in rows]


# ---------- product_link: связанные товары по ко-упоминанию ----------

def observe_link(sku_a: str, sku_b: str, source: str = "spec") -> None:
    """Пара товаров встретилась в одной спецификации/заказе — растим связь.
    Хранится однонаправленно: пара нормализуется (sku_a < sku_b)."""
    a, b = (sku_a or "").strip(), (sku_b or "").strip()
    if not a or not b or a == b:
        return
    if a > b:
        a, b = b, a
    init_db()
    with _db() as connection:
        connection.execute(
            """
            INSERT INTO product_link (sku_a, sku_b, hits, source, updated_at)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sku_a, sku_b) DO UPDATE SET
                hits = hits + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (a, b, source),
        )
    _bump()


def observe_bundle(skus: list[str], source: str = "spec") -> int:
    """Связать все товары одного документа попарно. Возвращает число связей."""
    uniq = []
    for s in skus:
        s = (s or "").strip()
        if s and s not in uniq:
            uniq.append(s)
    n = 0
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            observe_link(uniq[i], uniq[j], source)
            n += 1
    return n


def get_related(sku: str, limit: int = 10) -> list[dict]:
    """Связанные товары для sku: [{sku, hits}] по силе связи."""
    sku = (sku or "").strip()
    if not sku:
        return []
    init_db()
    with _db() as connection:
        rows = connection.execute(
            """
            SELECT CASE WHEN sku_a = ? THEN sku_b ELSE sku_a END AS rel,
                   hits, source, updated_at
            FROM product_link
            WHERE sku_a = ? OR sku_b = ?
            ORDER BY hits DESC LIMIT ?
            """,
            (sku, sku, sku, limit),
        ).fetchall()
    return [{"sku": r["rel"], "hits": int(r["hits"]),
             "source": r["source"], "updated_at": r["updated_at"]}
            for r in rows]


def link_stats() -> int:
    """Число связей товар-товар."""
    init_db()
    with _db() as connection:
        return int(connection.execute(
            "SELECT COUNT(*) c FROM product_link").fetchone()["c"])


# ---------- product_dims: габариты/вес/фасовка, которые ядро вычислило ----------

def upsert_product_dims(rows: list[dict]) -> int:
    """Массовая запись габаритов, добытых ядром при пересборке индекса.
    row: {sku, weight_kg, length_mm, width_mm, height_mm, volume_l, pack}."""
    rows = [r for r in rows if str(r.get("sku") or "").strip()]
    if not rows:
        return 0
    init_db()
    with _db() as connection:
        connection.executemany(
            """
            INSERT INTO product_dims
                (sku, weight_kg, length_mm, width_mm, height_mm, volume_l, pack, source, updated_at)
            VALUES (?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(sku) DO UPDATE SET
                weight_kg = excluded.weight_kg,
                length_mm = excluded.length_mm,
                width_mm  = excluded.width_mm,
                height_mm = excluded.height_mm,
                volume_l  = excluded.volume_l,
                pack      = excluded.pack,
                source    = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            [(
                str(r["sku"]).strip(),
                float(r.get("weight_kg") or 0),
                float(r.get("length_mm") or 0),
                float(r.get("width_mm") or 0),
                float(r.get("height_mm") or 0),
                float(r.get("volume_l") or 0),
                str(r.get("pack") or "")[:255],
                str(r.get("source") or "core")[:32],
            ) for r in rows],
        )
    return len(rows)


def get_dims(sku: str) -> dict | None:
    """Габариты одного товара из памяти ядра."""
    sku = (sku or "").strip()
    if not sku:
        return None
    init_db()
    with _db() as connection:
        row = connection.execute(
            "SELECT * FROM product_dims WHERE sku = ?", (sku,)
        ).fetchone()
    return dict(row) if row else None


def get_dims_many(skus: list) -> dict:
    """{sku: dims} для набора SKU — логистика/накладные."""
    sk = [str(s).strip() for s in skus if str(s or "").strip()]
    if not sk:
        return {}
    init_db()
    ph = ",".join("?" * len(sk))
    with _db() as connection:
        rows = connection.execute(
            f"SELECT * FROM product_dims WHERE sku IN ({ph})", sk
        ).fetchall()
    return {r["sku"]: dict(r) for r in rows}


# ---------- Единицы продажи, добитые AI (по «интернету» / знанию рынка) ----------

def set_unit(sku: str, unit: str, source: str = "ai") -> None:
    """Записать единицу продажи товара (шт/упак./м/кг/мешок…)."""
    sku, unit = (sku or "").strip(), (unit or "").strip()
    if not sku or not unit:
        return
    init_db()
    with _db() as connection:
        connection.execute(
            "INSERT INTO product_units (sku, unit, source) VALUES (?, ?, ?) "
            "ON CONFLICT(sku) DO UPDATE SET unit=excluded.unit, "
            "source=excluded.source, updated_at=CURRENT_TIMESTAMP",
            (sku, unit, source),
        )
    _bump()


def get_units_map() -> dict:
    """{sku: unit} — все выученные единицы продажи.
    init_db может не пройти от сервисного юзера (read-only app.db) — читаем всё равно."""
    try:
        init_db()
    except Exception:
        pass
    try:
        with _db() as connection:
            rows = connection.execute(
                "SELECT sku, unit FROM product_units").fetchall()
        return {r["sku"]: r["unit"] for r in rows}
    except sqlite3.Error:
        return {}

