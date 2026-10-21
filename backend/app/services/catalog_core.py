"""Ядро каталога «Товары на сайте».

Единый слой над ProductDB для всех потребителей (OCR-матчинг, ИИ-калькулятор,
Директ, гео-витрины, SEO, статьи):

- нормализация рус/латин брендов и кириллических опечаток OCR;
- инвертированный токен-индекс по именам/SKU → быстрый поиск по смыслу;
- разбор фасовки из названия (кг/л/мм/м/м²) — «Ротбанд 30кг» найдёт мешок 30 кг;
- relevant_for_spec() — подмножество каталога, релевантное строкам спецификации:
  DeepSeek получает ~80 точных кандидатов вместо слепых первых 400 записей.

Ядро строится лениво и пересобирается после sync/reload каталога.
"""
from __future__ import annotations

import re
import threading
import unicodedata

from app.models.product import Product
from app.db import learn_store
from app.services.product_db import product_db

# --- Бренд-синонимы: кириллица/латиница/опечатки OCR ---------------------------
_BRAND_ALIASES = {
    "rotband": ["ротбанд", "rotband", "ротбонд", "ротбант"],
    "knauf": ["кнауф", "knauf", "кнaуф", "кнаф", "kнауф"],
    "ceresit": ["церезит", "ceresit", "церезитн", "cerezit", "церисит"],
    "vetonit": ["ветонит", "vetonit", "weber", "вебер", "ветонитт"],
    "volma": ["волма", "volma", "волма-слой", "volma-layer", "волмаслой"],
    "starateli": ["старатели", "starateli", "старателли"],
    "bolars": ["боларс", "bolars"],
    "pereplet": ["перфекта", "perfekta", "перфекта"],
    "unis": ["юнис", "unis"],
    "shumanet": ["шуманет", "shumanet"],
    "techno": ["технониколь", "техноникол", "tehnonikol", "technonicol"],
    "stayer": ["стайер", "stayer", "штayer"],
    "lenta": ["лента", "lenta"],
    "gkl": ["гкл", "gkl", "гипсокартон", "лист гипсокартон"],
    "pgp": ["пгп", "pgp", "пазогребнев", "пазо-гребнев"],
}

# Единичные исправления частых OCR/опечаток слово-в-слово (после lower)
_TOKEN_FIX = {
    "штукатуркa": "штукатурка", "штукатурк": "штукатурка", "штуткатурка": "штукатурка",
    "шпаклевка": "шпатлевка", "шпатлёвка": "шпатлевка", "шпаклёвка": "шпатлевка",
    "саморезы": "саморез", "саморёзы": "саморез", "саморезами": "саморез",
    "грунтовкой": "грунтовка", "грунт": "грунтовка", "грунтовкa": "грунтовка",
    "пеноплекс": "пеноплэкс", "ппс": "пенопласт", "маяки": "маячковый",
    "маяк": "маячковый", "маячок": "маячковый",
    "mesh": "меш", "меш": "мешков", "мешков": "мешков", "мещков": "мешков",
    "kanist": "канистра", "кан": "канистра", "канистру": "канистра",
    "shtukaturka": "штукатурка", "shpaklevka": "шпатлевка", "gruntovka": "грунтовка",
}

# Фасовка: "30 кг" / "10 л" / "3000 мм" / "0.8 м" — вырезаем из названия
_SPEC_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(кг|г|л|мл|мм|см|м²|м2|м3|м\b)", re.IGNORECASE)

# ---------- Онтология единиц измерения ----------
# Каждая группа: каноническая форма + все синонимы/склонения/латиница.
# dim: измерение (mass/volume/length/area/count) для конвертаций.
_UNIT_GROUPS: list[tuple[str, str, list[str]]] = [
    ("шт", "count", ["шт", "шт.", "штук", "штука", "штуки", "pc", "pcs", "piece", "sht"]),
    ("упак", "count", ["упак", "упак.", "упаковка", "упаковок", "упаковки", "pack", "упаkовка"]),
    ("мешок", "count", ["мешок", "мешка", "мешков", "меш", "меш.", "bag", "bags"]),
    ("банка", "count", ["банка", "банки", "банок", "can", "jar"]),
    ("ведро", "count", ["ведро", "ведра", "ведёр", "bucket"]),
    ("канистра", "count", ["канистра", "канистры", "канистр", "jerrycan"]),
    ("рулон", "count", ["рулон", "рулона", "рулонов", "рул", "roll"]),
    ("лист", "count", ["лист", "листа", "листов", "sheet"]),
    ("поддон", "count", ["поддон", "поддона", "поддонов", "палета", "паллета", "паллет", "палеты", "паллетов", "pallet"]),
    ("компл", "count", ["компл", "компл.", "комплект", "комплекта", "комплектов", "kit", "set"]),
    ("пачка", "count", ["пачка", "пачки", "пачек"]),
    ("коробка", "count", ["коробка", "коробки", "коробок", "короб", "box"]),
    ("пог.м", "length", ["пог.м", "погм", "п/м", "м.п.", "м.пог.", "mp", "погонный метр"]),
    ("м", "length", ["метр", "метра", "метров", "m"]),
    ("мм", "length", ["мм", "мм.", "миллиметр", "миллиметра", "миллиметров", "mm"]),
    ("см", "length", ["см", "см.", "сантиметр", "сантиметра", "сантиметров", "cm"]),
    ("м2", "area", ["м2", "м²", "кв.м", "кв м", "кв. м", "квадратный метр", "квадратных метров", "m2", "sqm"]),
    ("м3", "volume", ["м3", "м³", "куб", "куб.", "куб.м", "куб м", "куб. м", "кубометр", "кубометра", "кубометров", "m3", "cbm"]),
    ("кг", "mass", ["кг", "кг.", "килограмм", "килограмма", "килограммов", "kg", "kilo"]),
    ("г", "mass", ["г", "г.", "гр", "гр.", "грамм", "грамма", "граммов", "g", "gram"]),
    ("т", "mass", ["т", "т.", "тонна", "тонны", "тонн", "t", "ton", "tonne"]),
    ("л", "volume", ["л", "л.", "литр", "литра", "литров", "l", "liter", "litre"]),
    ("мл", "volume", ["мл", "мл.", "миллилитр", "миллилитра", "миллилитров", "ml"]),
]

# token -> canonical unit; canonical -> dim
_TOKEN2UNIT: dict[str, str] = {}
_UNIT2DIM: dict[str, str] = {}
for _canon, _dim, _syns in _UNIT_GROUPS:
    _UNIT2DIM[_canon] = _dim
    for _s in _syns:
        _TOKEN2UNIT[_s] = _canon

# конвертация в базовую единицу измерения внутри dim
_UNIT_BASE: dict[str, tuple[str, float]] = {  # canon -> (base, factor)
    "г": ("кг", 0.001), "т": ("кг", 1000.0), "кг": ("кг", 1.0),
    "мл": ("л", 0.001), "л": ("л", 1.0), "м3": ("л", 1000.0),
    "мм": ("м", 0.001), "см": ("м", 0.01), "м": ("м", 1.0), "пог.м": ("м", 1.0),
}

# «12 меш» / «2,5 т» / «10 м2» — количество + единица в строке спецификации
_QTY_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*"
    r"(шт\.?|штук\w*|упак\w*|меш\w*|мешок\w*|банк\w*|ведро\w*|ведёр\w*|ведер\w*|"
    r"канистр\w*|рулон\w*|рул\.?|лист\w*|поддон\w*|палет\w*|паллет\w*|компл\w*|"
    r"пачк\w*|короб\w*|пог\.?\s*м\w*|м\.\s*пог\w*|"
    r"кг\.?|килограмм\w*|г\.?|гр\.?|грамм\w*|т\.?|тонн\w*|"
    r"л\.?|литр\w*|мл\.?|миллилитр\w*|"
    r"мм\.?|см\.?|м²|м2|м³|м3|кв\.?\s*м\w*|куб\w*|метр\w*|миллиметр\w*|"
    r"pcs?|bag|pack|roll|sheet|pallet|kg|gram|ton|liter|ml|m2|m3|cbm)",
    re.IGNORECASE)


def canonical_unit(token: str) -> str | None:
    """Токен → каноническая единица ('меш.'→'мешок', 'палета'→'поддон', 'кв.м'→'м2')."""
    return _TOKEN2UNIT.get(_norm(token).replace(" ", ""))


def parse_qty(text: str) -> list[dict]:
    """Из строки достаёт пары {value, unit, dim, base_value} — '2,5 т' →
    {'value':2.5,'unit':'т','dim':'mass','base_value':2500.0}."""
    out = []
    for m in _QTY_RE.finditer(_norm(text)):
        try:
            val = float(m.group(1).replace(",", "."))
        except ValueError:
            continue
        u_raw = re.sub(r"\s+", "", m.group(2).lower().rstrip("."))
        u = _TOKEN2UNIT.get(u_raw) or _TOKEN2UNIT.get(m.group(2).lower())
        if not u:
            # длинные формы с точкой уже попали; пробуем усечь окончание
            for syn, canon in _TOKEN2UNIT.items():
                if u_raw.startswith(syn.rstrip(".")) and len(syn) >= 2:
                    u = canon
                    break
        if not u:
            continue
        base, factor = _UNIT_BASE.get(u, (u, 1.0))
        out.append({"value": val, "unit": u, "dim": _UNIT2DIM[u],
                    "base": base, "base_value": round(val * factor, 4)})
    return out


# ---------- Реквизиты счетов/накладных — НЕ товарные строки ----------
_DOC_FIELD_WORDS = {
    "счет", "счёт", "оплате", "оплату", "оплата", "накладная", "накладной",
    "поставщик", "покупатель", "заказчик", "исполнитель", "грузоотправитель",
    "грузополучатель", "плательщик", "получатель", "продавец", "подрядчик",
    "инн", "кпп", "огрн", "бик", "р/с", "р/сч", "к/с", "к/сч",
    "банк", "реквизиты", "адрес", "телефон", "директор", "руководитель",
    "бухгалтер", "подпись", "печать", "ндс", "итого", "итог", "всего",
    "прописью", "договор", "договора", "счета", "основание", "дата",
    "номер", "№", "валюта", "руб", "руб.", "рублей", "копеек", "коп",
    "сумма", "цена", "количество", "единица", "наименование", "ед", "изм",
    "артикул", "код", "кол-во", "кол", "ставка", "подпункт", "подписал",
}


def is_doc_header_line(line: str) -> bool:
    """Строка — шапка/подвал счёта или накладной (реквизиты), а не позиция товара."""
    toks = _norm(line).split()
    if not toks:
        return True
    hits = sum(1 for t in toks if t in _DOC_FIELD_WORDS or t.rstrip(":;") in _DOC_FIELD_WORDS)
    # 2+ реквизитных слова или «ИНН/КПП 7707...» → служебная строка
    if hits >= 2 or (hits >= 1 and re.search(r"\d{6,}", line)):
        return True
    # «СЧЕТ НА ОПЛАТУ № 123 от 12.09.2026»
    if hits >= 1 and len(toks) <= 6 and not re.search(r"(кг|л|мм|шт|меш|м2|м3)", line, re.I):
        return True
    return False


# ---------- Фасеты товара: добываем из названия и атрибутов ----------
_FROST_RE = re.compile(r"\bf\s*-?\s*(\d{1,3})\b", re.IGNORECASE)
_COLOR_WORDS = {
    "белый", "белая", "белое", "белые", "серый", "серая", "серое", "серые",
    "черный", "чёрный", "черная", "чёрная", "коричневый", "коричневая",
    "красный", "красная", "зеленый", "зелёный", "зеленая", "желтый", "жёлтый",
    "синий", "синяя", "прозрачный", "прозрачная", "бежевый", "бежевая",
    "терракотовый", "терракотовая", "кирпичный", "кирпичная",
}
_ATTR_KEYS = {
    "цвет": "color", "морозостойкость": "frost", "марка морозостойкости": "frost",
    "водостойкость": "waterproof", "влагостойкость": "waterproof",
    "тип": "usage", "назначение": "usage", "применение": "usage",
    "вес": "weight", "фасовка": "weight", "упаковка": "pack",
    "объем": "volume", "объём": "volume", "размер": "size", "толщина": "thickness",
    "плотность": "density", "прочность": "strength", "марка": "grade",
}


# ---------- Единица продажи на витрине ----------
_SELL_UNIT_WORDS: tuple[tuple[str, str], ...] = (
    ("упак", "упак."), ("пачк", "упак."), ("рулон", "рулон"), ("рул.", "рулон"),
    ("мешок", "мешок"), ("мешка", "мешок"), ("мешке", "мешок"),
    ("ведро", "ведро"), ("ведра", "ведро"), ("ведёр", "ведро"), ("ведер", "ведро"),
    ("канистр", "канистра"), ("банк", "банка"), ("короб", "коробка"),
    ("поддон", "поддон"), ("палет", "поддон"), ("паллет", "поддон"),
    ("компл", "компл."), ("бухта", "бухта"), ("моток", "моток"),
    ("лист", "лист"),
)
_PACK_PIECES_RE = re.compile(r"(?:^|[\s(\[,;])(?:[2-9]|\d{2,})\s*шт\b", re.IGNORECASE)
_POGON_SALE_RE = re.compile(r"пог\.?\s*м\b|\bп\s*/\s*м\b|за\s+(?:погонный\s+)?метр", re.IGNORECASE)
_BY_WEIGHT_RE = re.compile(r"за\s*кг\b|на\s*вес\b|отвес\b|развес\b", re.IGNORECASE)
_UNIT_ATTR_RE = re.compile(r"единиц|ед\.?\s*изм", re.IGNORECASE)


def sell_unit(p: "Product", learned_units: dict | None = None) -> str:
    """Единица продажи: выученная AI (product_units) > атрибут «Единица» >
    пог.м/вес > слова упаковки > «N шт» (N>1) > шт."""
    if learned_units and str(p.sku) in learned_units:
        return learned_units[str(p.sku)]
    for a in (p.attributes or []):
        if _UNIT_ATTR_RE.search(str(a.get("name") or "")):
            canon = canonical_unit(str(a.get("text") or ""))
            if canon:
                return "упак." if canon == "упак" else canon
    low = _norm(p.name)
    if _POGON_SALE_RE.search(low):
        return "пог.м"
    if _BY_WEIGHT_RE.search(low):
        return "кг"
    for w, u in _SELL_UNIT_WORDS:
        if w in low:
            return u
    if _PACK_PIECES_RE.search(low):
        return "упак."
    return "шт"


def _facets_of(p: Product, learned_units: dict | None = None) -> dict:
    """Фасеты товара: цвет, морозостойкость F-число, внутренний/наружный, фасовка."""
    f: dict[str, object] = {"unit": sell_unit(p, learned_units)}
    low = _norm(p.name)
    toks = set(low.split())
    colors = [w for w in _COLOR_WORDS if w in toks]
    if colors:
        # приводим к именительному мужскому роду
        base = {"белая": "белый", "белое": "белый", "белые": "белый",
                "серая": "серый", "серое": "серый", "серые": "серый",
                "черная": "черный", "чёрная": "черный", "красная": "красный",
                "зеленая": "зеленый", "зелёная": "зеленый", "синяя": "синий",
                "прозрачная": "прозрачный", "коричневая": "коричневый",
                "бежевая": "бежевый", "желтая": "желтый", "жёлтая": "желтый",
                "терракотовая": "терракотовый", "кирпичная": "кирпичный"}
        f["color"] = sorted({base.get(c, c) for c in colors})
    m = _FROST_RE.search(low)
    if m:
        f["frost"] = f"F{int(m.group(1))}"
    if re.search(r"наружн|для наружных|уличн|фасадн", low):
        f["scope"] = "наружный"
    elif re.search(r"внутренн|для внутренних|интерьерн", low):
        f["scope"] = "внутренний"
    packs = sorted(_extract_pack(p.name))
    if packs:
        f["pack"] = packs
    # бренд: каноническое имя по _BRAND_ALIASES («кнауф»/«knauf» → knauf)
    for canon, variants in _BRAND_ALIASES.items():
        if toks & set(variants):
            f["brand"] = canon
            break
    # категория OpenCart: к какой группе относится товар
    cid = getattr(p, "category_id", None)
    if cid:
        f["category_id"] = cid
    cids = getattr(p, "category_ids", None)
    if cids:
        f["category_ids"] = list(cids)
    # характеристики из OpenCart
    for a in (p.attributes or []):
        k = _norm(str(a.get("name") or ""))
        v = str(a.get("text") or "").strip()
        if not v:
            continue
        for key_ru, key in _ATTR_KEYS.items():
            if key_ru in k and key not in f:
                f[key] = v[:60]
    return f


def _norm(text: str) -> str:
    """Нижний регистр + ё→е + NFKC + чистка мусорных символов."""
    t = unicodedata.normalize("NFKC", text or "").lower().replace("ё", "е")
    t = re.sub(r"[\"'«»„“”()№]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _norm_tokens(text: str) -> list[str]:
    """Токены нормализованной строки с бренд-развёрткой и фиксами опечаток."""
    out = []
    for raw in _norm(text).split():
        tok = _TOKEN_FIX.get(raw, raw)
        out.append(tok)
        # кириллица-версия латинского бренда (и наоборот) достаётся из алиасов
        for group in _BRAND_ALIASES.values():
            if tok in group:
                out.extend(t for t in group if t != tok)
                break
    return out


def _extract_pack(name: str) -> set[str]:
    """Фасовки вида «30кг», «10л», «3000мм» из названия → set канонических видов."""
    packs = set()
    for m in _SPEC_RE.finditer(name):
        num = m.group(1).replace(",", ".")
        unit = m.group(2).lower()
        unit = {"г": "кг" if float(num) >= 50 else "г",
                "мл": "л", "см": "мм", "м²": "м2"}.get(unit, unit)
        packs.add(f"{num}{unit}")
    return packs


# Габариты «N x N [x N]»: 1900х900мм, 50х50х3м, 2500*1200
_DIMS_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(мм|см|м)?\s*[xх×*]\s*"
    r"(\d+(?:[.,]\d+)?)\s*(мм|см|м)?\s*"
    r"(?:[xх×*]\s*(\d+(?:[.,]\d+)?)\s*(мм|см|м)?)?",
    re.IGNORECASE)
_DIM2MM = {"мм": 1.0, "см": 10.0, "м": 1000.0}


def _dims_mm(text: str) -> list[float]:
    """«50х50х3м»→[3000,50,50] мм (убывание). Число без единицы наследует
    последнюю единицу матча если <5 («1.5х2 м»→м), иначе мм («50х50»→мм)."""
    best: list[float] = []
    for m in _DIMS_RE.finditer(text or ""):
        g = m.groups()
        last_u = next((x.lower() for x in reversed(g) if x and x.lower() in _DIM2MM), None)
        nums = []
        for i in (0, 2, 4):
            if not g[i]:
                continue
            n = float(g[i].replace(",", "."))
            u = (g[i + 1] or "").lower() or (last_u if n < 5 else None) or "мм"
            nums.append(round(n * _DIM2MM.get(u, 1.0), 1))
        if len(nums) > len(best):
            best = nums
    return sorted(best, reverse=True)


def _dims_of(p: Product) -> dict:
    """Габариты/вес/объём/фасовка товара → строка product_dims.
    Приоритет: атрибуты OpenCart (Вес/Объем/Толщина/Размер), фоллбэк — название."""
    d: dict[str, object] = {}
    attrs = {_norm(str(a.get("name") or "")): str(a.get("text") or "").strip()
             for a in (p.attributes or [])}
    w_attr = next((v for k, v in attrs.items() if ("вес" in k or "фасовк" in k) and v), "")
    v_attr = next((v for k, v in attrs.items() if "объем" in k.replace("ё", "е") and v), "")
    for t in ([w_attr] if w_attr else []) + [p.name or ""]:
        q = next((x for x in parse_qty(t) if x["dim"] == "mass"), None)
        if q:
            d["weight_kg"] = q["base_value"]
            break
    for t in ([v_attr] if v_attr else []) + [p.name or ""]:
        q = next((x for x in parse_qty(t) if x["dim"] == "volume" and x["unit"] == "л"), None)
        if q:
            d["volume_l"] = q["base_value"]
            break
    texts = [p.name or ""] + [v for k, v in attrs.items()
                              if any(w in k for w in ("размер", "габарит", "длин")) and v]
    for t in texts:
        dims = _dims_mm(t)
        if len(dims) >= 2:
            d["length_mm"], d["width_mm"] = dims[0], dims[1]
            if len(dims) >= 3:
                d["height_mm"] = dims[2]
            break
    if "height_mm" not in d:
        th_attr = next((v for k, v in attrs.items() if "толщин" in k and v), "")
        for t in ([th_attr] if th_attr else []):
            q = next((x for x in parse_qty(t) if x["dim"] == "length"), None)
            if q:
                d["height_mm"] = round(q["base_value"] * 1000, 1)
                break
    packs = sorted(_extract_pack(p.name or ""))
    if packs:
        d["pack"] = ", ".join(packs)
    return d


class CatalogCore:
    """Индексированное ядро поверх product_db. Ленивое, пересобирается по запросу."""

    def __init__(self):
        self._lock = threading.Lock()
        self._built = False
        self._by_sku: dict[str, Product] = {}
        self._inv: dict[str, set[str]] = {}      # токен → skus
        self._pack_idx: dict[str, set[str]] = {} # «30кг» → skus
        self._tokens_of: dict[str, set[str]] = {}
        self._facets: dict[str, dict] = {}
        self._learned: dict[str, dict[str, int]] = {}
        self._rejected: dict[str, dict[str, int]] = {}
        self._domain_idx: dict[str, set[str]] = {}   # раздел → токены
        self._domain_learned: dict[str, dict[str, int]] = {}
        self._version = 0
        self._src_rev = -1
        self._learn_rev = -1

    # ---------- построение индекса ----------

    def _stale(self) -> bool:
        return ((not self._built)
                or (self._src_rev != getattr(product_db, "_rev", 0))
                or (self._learn_rev != learn_store.learn_store_learn_rev()))

    def rebuild(self) -> None:
        with self._lock:
            by_sku, inv, pack_idx, tokens_of, facets = {}, {}, {}, {}, {}
            dims_rows: list[dict] = []
            try:
                learned_units = learn_store.get_units_map()
            except Exception:
                learned_units = {}
            for p in product_db.list_products():
                if not p.name:
                    continue
                toks = set(_norm_tokens(p.name))
                toks.update(_norm_tokens(p.sku))
                toks.update(_norm_tokens(p.model))
                # токены категории намекают на смысл («штукатурка», «гипс»)
                for cid in (p.category_ids or []):
                    toks.add(f"cat{cid}")
                # габариты/вес/объём — ядро майнит их в постоянную память (product_dims)
                d = _dims_of(p)
                if d:
                    dims_rows.append({"sku": p.sku, "source": "core", **d})
                # фасетные токены: цвет/морозостойкость/scope тоже индексируем
                f = _facets_of(p, learned_units)
                if d.get("weight_kg"):
                    f["weight_kg"] = d["weight_kg"]
                if d.get("length_mm"):
                    f["dims_mm"] = [d["length_mm"], d.get("width_mm", 0), d.get("height_mm", 0)]
                facets[p.sku] = f
                for c in f.get("color", []):
                    toks.add(c)
                if f.get("frost"):
                    toks.add(str(f["frost"]).lower())
                if f.get("scope"):
                    toks.add(str(f["scope"]))
                tokens_of[p.sku] = toks
                for t in toks:
                    inv.setdefault(t, set()).add(p.sku)
                for pk in _extract_pack(p.name):
                    pack_idx.setdefault(pk, set()).add(p.sku)
                by_sku[p.sku] = p
            # --- обучение: выученные алиасы добавляют токены к SKU ---
            learned = learn_store.get_learned_aliases()
            rejected = learn_store.get_rejected()
            for phrase, sku_hits in learned.items():
                ptoks = set(_norm_tokens(phrase))
                for sku in sku_hits:
                    if sku in tokens_of:
                        tokens_of[sku] |= ptoks
                        for t in ptoks:
                            inv.setdefault(t, set()).add(sku)
            # --- габариты товаров → персистентная память ядра ---
            try:
                learn_store.upsert_product_dims(dims_rows)
            except Exception:
                pass
            self._learned = learned
            self._rejected = rejected
            # --- домены разделов: статический словарь + выученные термины ---
            dom_idx: dict[str, set[str]] = {}
            for dom, terms in _DOMAIN_VOCAB.items():
                dom_idx[dom] = set(_norm_tokens(" ".join(terms)))
            dom_learned = learn_store.get_domain_terms()
            for dom, term_hits in dom_learned.items():
                bucket = dom_idx.setdefault(dom, set())
                for term in term_hits:
                    bucket.update(_norm_tokens(term))
            self._domain_idx = dom_idx
            self._domain_learned = dom_learned
            self._by_sku = by_sku
            self._inv = inv
            self._pack_idx = pack_idx
            self._tokens_of = tokens_of
            self._facets = facets
            self._built = True
            self._version += 1
            self._src_rev = getattr(product_db, "_rev", 0)
            self._learn_rev = learn_store.learn_store_learn_rev()

    def _ensure(self):
        if self._stale():
            self.rebuild()

    # ---------- публичное API ----------

    def all(self) -> list[Product]:
        self._ensure()
        return list(self._by_sku.values())

    def get(self, sku: str) -> Product | None:
        self._ensure()
        return self._by_sku.get(sku)

    def search(self, query: str, limit: int = 20) -> list[Product]:
        """Полнотекстовый поиск по ядру: токены запроса ∩ индекс + фасовки."""
        self._ensure()
        toks = [t for t in _norm_tokens(query) if len(t) >= 2]
        packs = _extract_pack(query)
        scores: dict[str, int] = {}
        for t in toks:
            for sku in self._inv.get(t, ()):
                scores[sku] = scores.get(sku, 0) + 1
        # частичное совпадение для длинных слов (OCR рубит окончания)
        for t in toks:
            if len(t) < 4:
                continue
            for idx_tok, skus in self._inv.items():
                if idx_tok.startswith(t) or t.startswith(idx_tok):
                    for sku in skus:
                        scores[sku] = scores.get(sku, 0) + 1
        for pk in packs:
            for sku in self._pack_idx.get(pk, ()):
                scores[sku] = scores.get(sku, 0) + 2  # совпала фасовка — бонус
        # --- обучение: выученная пара фраза→sku бустится, отклонённая — режется ---
        q_norm = _norm(query)
        for phrase, sku_hits in self._learned.items():
            if phrase in q_norm or q_norm in phrase:
                for sku, hits in sku_hits.items():
                    if sku in self._by_sku:
                        scores[sku] = scores.get(sku, 0) + 3 * hits
        for phrase, sku_hits in self._rejected.items():
            if phrase in q_norm or q_norm in phrase:
                for sku, hits in sku_hits.items():
                    scores[sku] = scores.get(sku, 0) - 5 * hits
                    if scores[sku] < 0:
                        scores[sku] = 0

        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [self._by_sku[sku] for sku, _ in ranked[:limit] if sku in self._by_sku]

    def relevant_for_spec(self, spec_text: str, limit: int = 120) -> list[Product]:
        """Подмножество каталога под текст спецификации: одна строка = позиция."""
        self._ensure()
        acc: dict[str, int] = {}
        for line in spec_text.splitlines():
            for p in self.search(line, limit=10):
                acc[p.sku] = acc.get(p.sku, 0) + 1
        # дедуп + топ по частоте встречаемости
        ranked = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))
        picks = [self._by_sku[s] for s, _ in ranked[:limit]]
        # дополняем всем каталогом, если ядро пустое/маленькое
        if len(picks) < min(limit, len(self._by_sku) // 10):
            rest = [p for p in self._by_sku.values() if p.sku not in acc]
            picks.extend(rest[: limit - len(picks)])
        return picks

    # ---------- обучение ----------

    def learn(self, phrase: str, sku: str, accepted: bool,
              source: str = "feedback") -> None:
        """Записать подтверждение (accepted=True) или отказ (False) для пары
        «фраза из спецификации → sku». Перестройка индекса — ленивая."""
        if accepted:
            learn_store.learn_alias(phrase, sku, source=source)
        else:
            learn_store.reject_match(phrase, sku)

    def retrain(self) -> dict:
        """Принудительное переобучение: сброс и полная пересборка индекса
        (каталог + выученные связи + домены)."""
        with self._lock:
            self._built = False
            self._src_rev = -1
            self._learn_rev = -1
        self._ensure()
        return self.stats()

    def observe_not_found(self, phrase: str, source: str = "spec") -> None:
        """Позиция не нашлась в каталоге — запоминаем спрос."""
        learn_store.observe_not_found(phrase, source)

    def facets(self, sku: str) -> dict:
        """Фасеты товара: color, frost, scope, pack, brand, category."""
        self._ensure()
        return self._facets.get(sku, {})

    # ---------- связанные товары (ко-упоминание в документах) ----------

    def observe_bundle(self, skus: list[str], source: str = "spec") -> int:
        """Товары встретились вместе (спека/заказ/тендер) — растим связи."""
        return learn_store.observe_bundle(skus, source)

    def related(self, sku: str, limit: int = 10) -> list[dict]:
        """Связанные товары: [{sku, hits, name}] по силе ко-упоминания."""
        out = []
        for r in learn_store.get_related(sku, limit):
            p = self._by_sku.get(r["sku"])
            out.append({"sku": r["sku"], "hits": r["hits"],
                        "name": p.name if p else "",
                        "price": p.retail_price if p else 0})
        return out

    def product_profile(self, sku: str) -> dict:
        """Полное досье товара: карточка + фасеты + выученные фразы +
        отклонённые пары + связанные товары."""
        self._ensure()
        p = self._by_sku.get(sku)
        if not p:
            return {"status": "error", "detail": f"sku {sku} не найден"}
        learned = learn_store.get_alias_rows(sku)
        rejected = [ph for ph, skus in self._rejected.items() if sku in skus]
        return {
            "sku": p.sku,
            "name": p.name,
            "price": p.retail_price,
            "wholesale_price": getattr(p, "wholesale_price", None),
            "cost_price": p.cost_price_cash or p.cost_price_cashless,
            "quantity": getattr(p, "quantity", None),
            "facets": self._facets.get(sku, {}),
            "learned_phrases": learned,
            "rejected_phrases": rejected,
            "related": self.related(sku, 10),
            "domains": [c["domain"] for c in self.classify(p.name)],
        }

    # ---------- разделы сервера: классификация и обучение по доменам ----------

    def classify(self, text: str, top: int = 3) -> list[dict]:
        """К каким разделам сервера относится фраза: [{domain, score}]."""
        self._ensure()
        toks = set(_norm_tokens(text))
        if not toks:
            return []
        scores = []
        for dom, dtoks in self._domain_idx.items():
            hits = len(toks & dtoks)
            if hits:
                scores.append({"domain": dom, "score": hits})
        scores.sort(key=lambda x: -x["score"])
        return scores[:top]

    def domain_of(self, text: str) -> str:
        """Доминирующий раздел для фразы ('' если ни один не подошёл)."""
        ranked = self.classify(text, top=1)
        return ranked[0]["domain"] if ranked else ""

    def learn_domain(self, domain: str, term: str, target: str = "",
                     kind: str = "term", source: str = "feedback") -> None:
        """Выучить термин/факт раздела — перестройка индекса ленивая."""
        learn_store.learn_domain(domain, term, target, kind, source)

    def knowledge(self, samples: int = 5) -> dict:
        """Карта знаний ядра по разделам: {domain: {static, learned, sample}}."""
        self._ensure()
        out = {}
        all_domains = set(_DOMAIN_VOCAB) | set(self._domain_learned)
        for dom in sorted(all_domains):
            learned = self._domain_learned.get(dom, {})
            out[dom] = {
                "static_terms": len(_DOMAIN_VOCAB.get(dom, [])),
                "learned_terms": len(learned),
                "index_tokens": len(self._domain_idx.get(dom, ())),
                "sample": list(learned)[:samples]
                          or _DOMAIN_VOCAB.get(dom, [])[:samples],
            }
        return out

    def stats(self) -> dict:
        self._ensure()
        return {
            "products": len(self._by_sku),
            "tokens": len(self._inv),
            "pack_variants": len(self._pack_idx),
            "facets": sum(1 for f in self._facets.values() if f),
            "learned_aliases": sum(len(v) for v in self._learned.values()),
            "rejected_pairs": sum(len(v) for v in self._rejected.values()),
            "domains": len(self._domain_idx),
            "domain_learned_terms": sum(len(v) for v in self._domain_learned.values()),
            "index_version": self._version,
        }


catalog_core = CatalogCore()


# ---------- Реестр разделов сервера: ядро знает все домены наизусть ----------
# Статический словарь терминов каждого раздела. Поверх него при пересборке
# подмешиваются выученные термины из learn_store.domain_knowledge.
_DOMAIN_VOCAB: dict[str, list[str]] = {
    "catalog": ["товар", "артикул", "sku", "каталог", "категория", "цена",
                "розница", "опт", "остаток", "фасовка", "упаковка", "бренд",
                "производитель", "себестоимость", "характеристика"],
    "dashboard": ["дашборд", "roi", "маржа", "прибыль", "бюджет",
                  "статистика", "топ товаров", "портфель"],
    "ads": ["директ", "кампания", "реклама", "объявление", "ставка", "бид",
            "ключевое слово", "ctr", "показ", "клик", "аукцион", "топ-1",
            "адгруппа", "adgroup", "конверсия", "cpc"],
    "seo": ["seo", "мета", "meta title", "meta description", "keywords",
            "json-ld", "schema", "sitemap", "индексация", "переобход",
            "сниппет", "выдача"],
    "competitors": ["конкурент", "конкуренты", "петрович", "мониторинг цен",
                    "цены конкурентов", "шпионаж", "леруа", "leroy", "obi",
                    "максидом", "всеинструменты"],
    "competitors_bids": ["ставки конкурентов", "аукционные данные",
                         "перебить ставку", "позиция объявления",
                         "спецразмещение"],
    "opencart": ["opencart", "заказ", "статус заказа", "покупатель",
                 "оформление", "чекаут", "ai_manager", "ocmod",
                 "модификатор"],
    "media": ["изображение", "фото", "картинка", "медиа", "фото товара",
              "медиабиблиотека"],
    "sites": ["витрина", "поддомен", "гео-сайт", "блок страницы", "тема",
              "sitebuilder", "конструктор", "шаблон", "секция"],
    "ai_seo": ["ai seo", "генерация мета", "seo текст", "автоописание"],
    "budget_roi": ["распределение бюджета", "roi план", "сценарий бюджета",
                   "отдача", "эффективность рекламы"],
    "promotions": ["акция", "скидка", "промо", "распродажа",
                   "спецпредложение", "купон", "промокод"],
    "tenders": ["тендер", "закупка", "контракт", "победитель", "нмцк",
                "44-фз", "223-фз", "госзакупка", "тендергуру", "tenderguru",
                "кп", "коммерческое предложение", "обеспечение заявки",
                "площадка", "етп", "смета по тендеру", "предмет закупки"],
    "reviews": ["отзыв", "отзывы", "рейтинг", "модерация отзывов", "оценка"],
    "autosmeta": ["смета", "спецификация", "спека", "позиция сметы",
                  "перечень работ", "ведомость", "калькуляция"],
    "content": ["статья", "блог", "контент", "публикация", "slug",
                "автопубликация", "контент-фабрика"],
    "clients_objects": ["объект", "стройка", "клиент", "адрес объекта",
                        "прораб", "заказчик объекта"],
    "sync": ["синхронизация", "импорт", "прайс поставщика", "загрузка прайса",
             "staging", "выгрузка", "обмен данными"],
    "webmaster": ["вебмастер", "метрика", "визиты", "посетители", "просмотры",
                  "поисковые запросы", "страницы в поиске", "исключено",
                  "счетчик метрики"],
    "tools": ["телеграм", "telegram", "уведомление", "dadata", "дадата",
              "инн", "проверка инн", "sms", "смс", "верификация"],
    "logistics": ["доставка", "склад", "грибки", "дмитровское", "газель",
                  "фура", "легковой", "тариф", "километр", "зона доставки",
                  "haversine", "машина", "газон", "москва", "мо",
                  "московская область"],
    "geo": ["город", "гео", "гео-страница", "поддомен города", "регион",
            "московская область", "доставка по городу"],
    "parser": ["спецификация", "ocr", "распознавание", "счёт", "накладная",
               "позиция", "строка счёта", "not_found", "не найдено"],
}
