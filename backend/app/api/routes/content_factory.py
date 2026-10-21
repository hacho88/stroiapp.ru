import re
import asyncio
import logging
import random
from fastapi import APIRouter, HTTPException
from app.services.deepseek_client import deepseek_client
from app.services.product_db import product_db
from app.db import journal_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content-factory", tags=["content-factory"])

# Целевая площадка — Журнал moscow.stroiapp.ru (НЕ блог OpenCart).
# 5-6 статей в сутки, от 10 000 знаков, строго по товарам раздела «Товары на сайте».
MAX_PER_DAY = 6
MIN_CHARS = 10000
JOURNAL_URL = "https://moscow.stroiapp.ru/journal"
_TONES = ["article-dark", "article-blue", "article-grey", "article-warm", "article-red"]
_CATEGORIES = {"Продукт", "Инструкция", "Бизнес", "Сервис", "Видео"}


def _check_daily_limit() -> bool:
    return journal_store.published_today_count() < MAX_PER_DAY


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def _read_time(html: str) -> str:
    minutes = max(1, round(len(_strip_html(html)) / 1800))
    return f"{minutes} мин чтения"


def _product_info(p) -> str:
    """Компактная выжимка карточки товара для промпта."""
    parts = [f"название: {p.name}", f"артикул: {p.sku}"]
    if getattr(p, "model", ""):
        parts.append(f"модель: {p.model}")
    if getattr(p, "retail_price", 0):
        parts.append(f"цена: {p.retail_price} ₽")
    attrs = getattr(p, "attributes", None) or []
    if attrs:
        kv = [f"{a.get('name', '')}: {a.get('value', a.get('text', ''))}" for a in attrs[:12] if isinstance(a, dict)]
        kv = [x for x in kv if x.strip(': ')]
        if kv:
            parts.append("характеристики: " + "; ".join(kv))
    desc = _strip_html(getattr(p, "description", "") or "")
    if desc:
        parts.append("описание: " + desc[:600])
    return "\n".join(parts)


def _slugify(text: str) -> str:
    """Convert Russian text to URL-safe slug."""
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    slug = text.lower().strip()
    slug = ''.join(translit.get(c, c) for c in slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
    return slug[:80] or 'article'


@router.get("/status")
def get_status():
    return {
        "status": "ok",
        "message": "Контент-фабрика — Журнал moscow.stroiapp.ru",
        "deepseek": bool(deepseek_client.api_key),
        "published_today": journal_store.published_today_count(),
        "max_per_day": MAX_PER_DAY,
        "queue_size": len(journal_store.list_articles(status="draft")),
    }


@router.post("/generate-articles")
async def generate_articles(payload: dict):
    """Генерация статей Журнала по товарам раздела «Товары на сайте» (ProductDB).
    Стиль: Дзен/Хабр от практика, 10 000+ знаков. Черновики сохраняются в journal_store."""
    count = min(payload.get("count", 2), 6)
    custom_topics = payload.get("topics", [])

    # Темы: (название товара, выжимка карточки, sku)
    topics = []
    if custom_topics:
        topics = [(str(t), "", "") for t in custom_topics]
    else:
        used = journal_store.used_skus()
        products = [p for p in product_db.list_products()
                    if p.sku not in used and (p.name or "").strip()]
        # предпочитаем товары в наличии
        in_stock = [p for p in products if getattr(p, "quantity", 0) > 0]
        pool = in_stock if len(in_stock) >= count else products
        for p in random.sample(pool, min(count, len(pool))):
            topics.append((p.name, _product_info(p), p.sku))

    if not topics:
        return {"generated": [], "count": 0, "status": "done",
                "detail": "Нет свободных товаров — по всем позициям «Товаров на сайте» уже есть статьи."}

    generated = []
    for i, (topic, info, sku) in enumerate(topics[:count]):
        if deepseek_client.api_key:
            article_data = await deepseek_client.generate_blog_article(topic, info)
        else:
            article_data = {
                "title": topic,
                "category": "Продукт",
                "intro": f"Статья о {topic} — практический опыт применения.",
                "content": f"<h2>О {topic}</h2><p>Строительные материалы — основа любого ремонта. В этой статье разберём {topic}.</p><h3>Характеристики</h3><p>Подробное описание характеристик и применения.</p><h3>Советы</h3><p>Практические советы по выбору и использованию.</p>",
                "meta_title": f"{topic} — купить в StroiApp | Журнал"[:70],
                "meta_description": f"Статья о {topic}: характеристики, применение, советы. Купить с НДС, доставка по Москве"[:160],
            }

        title = article_data.get("title", topic)
        content = article_data.get("content", "")
        category = article_data.get("category", "Продукт")
        if category not in _CATEGORIES:
            category = "Продукт"
        slug = _slugify(title)
        chars = len(_strip_html(content))

        aid = journal_store.add_article(
            slug=slug, title=title, category=category,
            tone=_TONES[i % len(_TONES)],
            intro=article_data.get("intro", "") or _strip_html(content)[:180].strip(),
            content=content, product_sku=sku, product_name=topic,
            read_time=_read_time(content), status="draft",
        )
        generated.append({
            "id": aid,
            "title": title,
            "slug": slug,
            "category": category,
            "chars": chars,
            "under_limit": chars < MIN_CHARS,
            "meta_title": article_data.get("meta_title", ""),
            "meta_description": article_data.get("meta_description", ""),
            "status": "draft",
        })

    return {"generated": generated, "count": len(generated), "status": "done"}


@router.post("/publish")
async def publish_article(payload: dict):
    """Публикация статьи в Журнал moscow.stroiapp.ru (status=draft → published в journal_store)"""
    if not _check_daily_limit():
        return {"status": "limit_reached", "detail": f"Лимит {MAX_PER_DAY} статей в день исчерпан. Попробуйте завтра."}

    article = None
    article_id = payload.get("article_id")

    if article_id:
        draft = journal_store.get_article(article_id)
        if draft:
            article = draft
    else:
        drafts = journal_store.list_articles(status="draft", limit=1)
        if drafts:
            article = drafts[0]

    if not article and payload.get("title") and payload.get("content"):
        # Прямая публикация статьи, переданной в payload
        slug = payload.get("slug") or _slugify(payload["title"])
        content = payload["content"]
        category = payload.get("category", "Продукт")
        if category not in _CATEGORIES:
            category = "Продукт"
        aid = journal_store.add_article(
            slug=slug, title=payload["title"], category=category,
            tone=random.choice(_TONES), intro=payload.get("intro", ""),
            content=content, product_sku=payload.get("product_sku", ""),
            product_name=payload.get("product_name", ""),
            read_time=_read_time(content), status="draft",
        )
        article = journal_store.get_article(aid)

    if not article:
        raise HTTPException(status_code=400, detail="Нет статьи для публикации. Сначала сгенерируйте или передайте title+content.")

    row = journal_store.mark_published(article["id"])
    published_today = journal_store.published_today_count()
    return {
        "article_id": row["id"],
        "status": "published",
        "url": f"{JOURNAL_URL}?slug={row['slug']}",
        "title": row["title"],
        "slug": row["slug"],
        "published_today": published_today,
        "remaining_today": MAX_PER_DAY - published_today,
    }


@router.post("/auto-publish")
async def auto_publish():
    """Автопубликация: генерирует статьи по товарам и публикует их в Журнал.
    Вызывается по расписанию (cron/scheduler) 1 раз в день."""
    if not _check_daily_limit():
        return {"status": "limit_reached", "published_today": journal_store.published_today_count()}

    slots = MAX_PER_DAY - journal_store.published_today_count()
    results = []

    for _ in range(slots):
        gen = await generate_articles({"count": 1})
        if gen.get("generated"):
            pub = await publish_article({"article_id": gen["generated"][0]["id"]})
            results.append(pub)
            await asyncio.sleep(2)

    return {
        "status": "done",
        "published": len(results),
        "results": results,
        "published_today": journal_store.published_today_count(),
    }


@router.get("/queue")
async def get_queue():
    """Очередь черновиков на публикацию в Журнал"""
    drafts = journal_store.list_articles(status="draft", limit=50)
    for a in drafts:
        a["chars"] = len(_strip_html(a.get("content", "")))
        a.pop("content", None)
    return {
        "queue": drafts,
        "queued_count": len(drafts),
        "published_today": journal_store.published_today_count(),
        "max_per_day": MAX_PER_DAY,
    }


@router.get("/articles")
async def list_articles(status: str = ""):
    """Все статьи Журнала (draft+published) для админки — со счётчиком просмотров."""
    items = journal_store.list_articles(status=status or None, limit=200)
    counts = journal_store.view_counts()
    for a in items:
        a["chars"] = len(_strip_html(a.get("content", "")))
        a.pop("content", None)
        a["url"] = f"{JOURNAL_URL}?slug={a['slug']}"
        a["views"] = counts.get(a["id"], 0)
    return {"articles": items, "total": len(items)}


@router.get("/articles/{article_id}")
async def get_article_full(article_id: int):
    """Полная статья с контентом — для редактирования в админке."""
    a = journal_store.get_article(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    a["chars"] = len(_strip_html(a.get("content", "")))
    a["url"] = f"{JOURNAL_URL}?slug={a['slug']}"
    a["stats"] = journal_store.article_stats(article_id)
    return {"article": a}


@router.put("/articles/{article_id}")
async def update_article(article_id: int, payload: dict):
    """Редактирование статьи: title, intro, content, category, slug, status."""
    a = journal_store.get_article(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    title = (payload.get("title") or "").strip() or None
    category = (payload.get("category") or "").strip() or None
    if category and category not in _CATEGORIES:
        category = "Продукт"
    intro = payload.get("intro")
    content = payload.get("content")
    slug = (payload.get("slug") or "").strip().lower() or None
    status = payload.get("status")
    if status not in ("draft", "published", None):
        status = None

    try:
        row = journal_store.update_article(
            article_id,
            title=title,
            category=category,
            intro=intro if intro is not None else None,
            content=content if content is not None else None,
            slug=slug,
            read_time=_read_time(content) if content else None,
            status=status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": "updated", "article": {
        "id": row["id"], "slug": row["slug"], "title": row["title"],
        "category": row["category"], "status": row["status"],
        "chars": len(_strip_html(row.get("content", ""))),
        "url": f"{JOURNAL_URL}?slug={row['slug']}",
    }}


@router.get("/articles/{article_id}/stats")
async def article_view_stats(article_id: int):
    """Кто читал статью: счётчик просмотров, уникальные IP, страны, последние визиты."""
    a = journal_store.get_article(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return {"article_id": article_id, "title": a["title"], **journal_store.article_stats(article_id)}


@router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    ok = journal_store.delete_article(article_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return {"status": "deleted", "article_id": article_id}
