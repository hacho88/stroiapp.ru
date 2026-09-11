import re
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.services.deepseek_client import deepseek_client
from app.services.opencart_api import opencart_api

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content-factory", tags=["content-factory"])


@router.get("/status")
def content_factory_status():
    return {"status": "ok", "service": "content_factory", "queue": len(_article_queue)}

_article_queue = []
_article_counter = 1
_last_publish_date = None
_published_today = 0
MAX_PER_DAY = 2


def _check_daily_limit() -> bool:
    global _last_publish_date, _published_today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _last_publish_date != today:
        _last_publish_date = today
        _published_today = 0
    return _published_today < MAX_PER_DAY


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
        "message": "Контент-фабрика — раздел работает",
        "deepseek": bool(deepseek_client.api_key),
        "published_today": _published_today,
        "max_per_day": MAX_PER_DAY,
        "queue_size": len(_article_queue),
    }


@router.post("/generate-articles")
async def generate_articles(payload: dict):
    """Генерация статей по реальным товарам магазина через DeepSeek.
    Стиль: Дзен/Хабр, 3000-5000 символов, SEO-оптимизировано."""
    count = min(payload.get("count", 2), 5)
    custom_topics = payload.get("topics", [])

    topics = custom_topics
    if not topics:
        products_resp = await opencart_api.product_list(limit=50)
        products = []
        if isinstance(products_resp, dict) and "products" in products_resp:
            products = products_resp["products"]
        elif isinstance(products_resp, list):
            products = products_resp

        if products:
            import random
            sample = random.sample(products, min(count, len(products)))
            topics = [p.get("name", str(p)) for p in sample]
        else:
            topics = [
                "Штукатурка Knauf Ротбанд 30 кг",
                "Цемент М500 Д0 50 кг",
                "Грунтовка Ceresit CT99",
            ][:count]

    generated = []
    for i, topic in enumerate(topics[:count]):
        if deepseek_client.api_key:
            article_data = await deepseek_client.generate_blog_article(topic)
        else:
            article_data = {
                "title": topic,
                "intro": f"Статья о {topic} — практический опыт применения.",
                "content": f"<h2>О {topic}</h2><p>Строительные материалы — основа любого ремонта. В этой статье разберём {topic}.</p><h3>Характеристики</h3><p>Подробное описание характеристик и применения.</p><h3>Советы</h3><p>Практические советы по выбору и использованию.</p>",
                "meta_title": f"{topic} — купить в StroiApp.ru | Блог"[:70],
                "meta_description": f"Статья о {topic}: характеристики, применение, советы. Купить с НДС, доставка по Москве"[:160],
            }

        slug = _slugify(article_data.get("title", topic))
        article = {
            "id": _article_counter + i,
            "title": article_data.get("title", topic),
            "slug": slug,
            "text": article_data.get("content", ""),
            "intro": article_data.get("intro", ""),
            "meta_title": article_data.get("meta_title", ""),
            "meta_description": article_data.get("meta_description", ""),
            "status": "ready",
        }
        generated.append(article)

    _article_queue.extend(generated)
    _article_counter += len(generated)
    return {"generated": generated, "count": len(generated), "status": "done"}


@router.post("/publish")
async def publish_article(payload: dict):
    """Публикация статьи в блог OpenCart (запись в oc_blog_article + SEO URL)"""
    global _published_today

    if not _check_daily_limit():
        return {"status": "limit_reached", "detail": f"Лимит {MAX_PER_DAY} статей в день исчерпан. Попробуйте завтра."}

    article = None
    article_id = payload.get("article_id")

    if article_id:
        for a in _article_queue:
            if a["id"] == article_id:
                article = _article_queue.pop(_article_queue.index(a))
                break
    elif _article_queue:
        article = _article_queue.pop(0)

    if not article:
        if payload.get("title") and payload.get("content"):
            article = {
                "title": payload["title"],
                "slug": payload.get("slug") or _slugify(payload["title"]),
                "text": payload["content"],
                "intro": payload.get("intro", ""),
                "meta_title": payload.get("meta_title", ""),
                "meta_description": payload.get("meta_description", ""),
            }
        else:
            raise HTTPException(status_code=400, detail="Нет статьи для публикации. Сначала сгенерируйте или передайте title+content.")

    title = article["title"]
    slug = article["slug"]
    intro = article.get("intro", "")
    content = article["text"]
    meta_title = article.get("meta_title", "")
    meta_description = article.get("meta_description", "")

    # Use PHP publisher on server — handles INSERT, SEO URL, slug uniqueness, cache
    publish_payload = {
        "title": title,
        "slug": slug,
        "intro": intro,
        "content": content,
        "meta_title": meta_title,
        "meta_description": meta_description,
        "author": "StroiApp",
    }
    result = await opencart_api.post_direct("api/blog_publish", publish_payload)

    if isinstance(result, dict) and result.get("status") == "published":
        _published_today += 1

        # Ping search engines about new blog content
        sitemap_url = "https://stroiapp.ru/index.php?route=api/blog_sitemap"
        try:
            import urllib.request as _ur
            for ping_url in [
                f"https://yandex.ru/ping?sitemap={sitemap_url}",
                f"https://www.google.com/ping?sitemap={sitemap_url}",
            ]:
                _ur.urlopen(ping_url, timeout=5)
        except Exception:
            pass

        return {
            "article_id": result.get("article_id"),
            "status": "published",
            "url": result.get("url", f"https://stroiapp.ru/blog/{slug}"),
            "title": result.get("title", article["title"]),
            "slug": result.get("slug", slug),
            "published_today": _published_today,
            "remaining_today": MAX_PER_DAY - _published_today,
        }
    else:
        return {"status": "error", "detail": str(result)[:300]}


@router.post("/auto-publish")
async def auto_publish():
    """Автопубликация: генерирует 1-2 статьи по товарам и публикует их.
    Вызывается по расписанию (cron/scheduler) 1 раз в день."""
    if not _check_daily_limit():
        return {"status": "limit_reached", "published_today": _published_today}

    slots = MAX_PER_DAY - _published_today
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
        "published_today": _published_today,
    }


@router.get("/queue")
async def get_queue():
    """Очередь статей на публикацию"""
    return {
        "queue": _article_queue,
        "queued_count": len(_article_queue),
        "published_today": _published_today,
        "max_per_day": MAX_PER_DAY,
    }
