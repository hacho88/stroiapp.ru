import asyncio
from fastapi import APIRouter, HTTPException, Body
from app.services.competitor_spy import competitor_spy
from app.services.ai_advisor import ai_advisor
from app.services.ad_spy import ad_spy
from app.db.competitor_store import (
    add_competitor, list_competitors, get_prices, get_comparison,
    get_competitor_products, get_competitor_product_stats,
    get_competitor_ads, get_ads_stats,
    add_price as store_add_price,
)

router = APIRouter(prefix="/competitors-bids", tags=["competitors-bids"])


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Конкуренты и ставки — раздел работает"}


@router.get("/list")
def get_competitors():
    """Список всех конкурентов"""
    return {"competitors": list_competitors()}


@router.post("/add")
def add_new_competitor(payload: dict):
    """Добавить конкурента"""
    name = payload.get("name", "").strip()
    url = payload.get("url", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя обязательно")
    comp_id = add_competitor(name, url)
    return {"status": "added", "id": comp_id, "name": name}


@router.delete("/delete/{competitor_id}")
def delete_competitor(competitor_id: int):
    """Удалить конкурента"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parents[2] / "data" / "app.db"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("DELETE FROM competitor_prices WHERE competitor_id = ?", (competitor_id,))
            conn.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
            conn.commit()
        return {"status": "deleted", "id": competitor_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/scan/{competitor_id}")
async def scan_competitor(competitor_id: int):
    """Сканировать цены конкурента по URL"""
    comps = list_competitors()
    comp = next((c for c in comps if c["id"] == competitor_id), None)
    if not comp:
        raise HTTPException(status_code=404, detail="Конкурент не найден")
    if not comp.get("url"):
        raise HTTPException(status_code=400, detail="URL конкурента не задан")
    results = await competitor_spy.scan_url(comp["url"])
    if results and "error" in results[0]:
        # Возвращаем 400 с понятным сообщением вместо сырого 502
        raise HTTPException(status_code=400, detail=results[0]["error"])
    imported = 0
    for i, item in enumerate(results):
        sku = f"COMP-{competitor_id}-{i+1}"
        store_add_price(competitor_id, sku, item.get("name", ""), float(item.get("price", 0)))
        imported += 1
    return {"status": "scanned", "items_found": len(results), "imported": imported}


@router.post("/import-prices")
def import_prices(payload: dict):
    """Ручной импорт цен конкурента"""
    competitor_id = payload.get("competitor_id")
    prices = payload.get("prices", [])
    if not competitor_id:
        raise HTTPException(status_code=400, detail="competitor_id обязателен")
    imported = 0
    for item in prices:
        sku = item.get("sku", "").strip()
        if not sku:
            continue
        store_add_price(competitor_id, sku, item.get("name", ""), float(item.get("price", 0)))
        imported += 1
    return {"status": "imported", "imported": imported}


@router.get("/prices/{competitor_id}")
def get_competitor_prices(competitor_id: int):
    """Цены конкурента"""
    return {"prices": get_prices(competitor_id)}


@router.get("/compare")
def compare_prices():
    """Сравнение цен с конкурентами"""
    return {"comparisons": competitor_spy.compare()}


@router.get("/top")
async def get_top(limit: int = 10):
    """Рейтинг ТОП-N позиций магазина"""
    return {
        "positions": [],
        "total_queries": 0,
        "avg_position": 0,
        "top_10_count": 0,
        "top_100_count": 0,
    }


@router.post("/fetch-bids")
async def fetch_bids(payload: dict):
    """Сбор ставок конкурентов через внешние API (SpyWords / Keys.so)"""
    return {"status": "ok", "bids": [], "source": payload.get("source", "spywords")}


@router.get("/products/{competitor_id}")
def get_products(competitor_id: int, limit: int = 100, offset: int = 0):
    """Товары конкурента (структурированные данные из последнего сканирования)"""
    products = get_competitor_products(competitor_id, limit, offset)
    stats = get_competitor_product_stats(competitor_id)
    return {"products": products, "stats": stats}


@router.get("/stats/{competitor_id}")
def get_stats(competitor_id: int):
    """Статистика по товарам конкурента"""
    return get_competitor_product_stats(competitor_id)


@router.get("/recommendations")
async def get_recommendations(top_n: int = 10):
    """AI-рекомендации: на какие товары запускать рекламу, какие ключи, какие ставки"""
    return await ai_advisor.generate_ad_recommendations(top_n=top_n)


@router.post("/analyze-keywords")
async def analyze_keywords(payload: dict):
    """AI анализирует название товара и предлагает ключевые слова для Яндекс Директ"""
    product_name = payload.get("product_name", "").strip()
    if not product_name:
        raise HTTPException(status_code=400, detail="product_name обязателен")
    return await ai_advisor.analyze_keywords(product_name)


@router.post("/discover")
async def discover_competitors(payload: dict):
    """Автопоиск конкурентов через Яндекс: находит, добавляет и сканирует"""
    query = payload.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query обязателен (например: строительные материалы москва)")
    max_competitors = payload.get("max_competitors", 5)
    return await competitor_spy.auto_discover_and_scan(query, max_competitors=max_competitors)


@router.post("/scan-ads/{competitor_id}")
async def scan_competitor_ads(competitor_id: int, payload: dict = None):
    """Сканировать рекламные объявления конкурента в Яндекс Директ"""
    keywords = payload.get("keywords", []) if payload else None
    return await ad_spy.scan_ads_for_competitor(competitor_id, keywords=keywords)


@router.post("/scan-ads-bulk")
async def scan_ads_bulk(payload: dict):
    """Массовый поиск рекламных объявлений по ключевым словам"""
    keywords = payload.get("keywords", [])
    if not keywords:
        raise HTTPException(status_code=400, detail="keywords обязателен (список строк)")
    return await ad_spy.scan_ads_bulk(keywords)


@router.get("/ads/{competitor_id}")
def get_ads(competitor_id: int, limit: int = 100):
    """Рекламные объявления конкурента"""
    return {"ads": get_competitor_ads(competitor_id, limit=limit)}


@router.get("/ads")
def get_all_ads(limit: int = 200):
    """Все рекламные объявления"""
    return {"ads": get_competitor_ads(None, limit=limit)}


@router.get("/ads-stats")
def ads_stats():
    """Статистика по рекламным объявлениям"""
    return get_ads_stats()


@router.get("/ads-strategy/{competitor_id}")
async def get_ad_strategy(competitor_id: int):
    """Анализ рекламной стратегии конкурента"""
    return await ad_spy.get_competitor_ad_strategy(competitor_id)


@router.get("/our-products-ads")
async def get_our_products_ads(limit: int = 20):
    """Анализ рекламы по нашим товарам: кто ещё рекламируется по тем же запросам"""
    return await ad_spy.analyze_ads_for_our_products(limit=limit)


@router.post("/add-recommended")
def add_recommended_competitors():
    """Быстро добавляет 10 рекомендуемых строительных магазинов"""
    from app.services.competitor_spy import competitor_spy
    added = []
    for store in competitor_spy.POPULAR_BUILDING_STORES[:10]:
        existing = [c for c in list_competitors() if store["domain"] in (c.get("url") or "")]
        if not existing:
            comp_id = add_competitor(store["name"], store["url"])
            added.append({"id": comp_id, "name": store["name"], "url": store["url"]})
    return {"status": "ok", "added": added, "total": len(added)}


@router.post("/scan-playwright/{competitor_id}")
async def scan_with_playwright(competitor_id: int):
    """
    Сканирует сайт конкурента через Playwright (реальный браузер).
    Работает с SPA-сайтами (React/Vue), где httpx не справляется.
    """
    from app.services.playwright_scanner import get_scanner

    competitors = list_competitors()
    comp = next((c for c in competitors if c["id"] == competitor_id), None)
    if not comp:
        raise HTTPException(status_code=404, detail="Конкурент не найден")
    url = comp.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="У конкурента нет URL")

    try:
        scanner = await get_scanner()
        result = await scanner.scan_website(url, max_wait_ms=30000)

        # Сохраняем найденные товары
        if result["products"]:
            from app.db.competitor_store import save_competitor_products
            valid_products = [
                {"name": p["name"], "price": p["price"], "url": p.get("url", ""), "image": p.get("image", "")}
                for p in result["products"]
                if p.get("name") and p.get("price")
            ]
            if valid_products:
                save_competitor_products(competitor_id, valid_products)
                for p in valid_products:
                    store_add_price(competitor_id, p["name"], p["price"])

        return {
            "status": "ok",
            "domain": result["domain"],
            "products_found": len(result["products"]),
            "error": result.get("error"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Playwright error: {exc}")


@router.post("/scan-url-playwright")
async def scan_any_url_playwright(url: str = Body(..., embed=True)):
    """
    Сканирует ЛЮБОЙ сайт по URL через Playwright без добавления в базу.
    Возвращает найденные товары.
    """
    from app.services.playwright_scanner import get_scanner

    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL должен начинаться с http:// или https://")

    try:
        scanner = await get_scanner()
        result = await scanner.scan_website(url, max_wait_ms=30000)
        return {
            "status": "ok",
            "domain": result["domain"],
            "products_found": len(result["products"]),
            "products": result["products"][:20],  # первые 20 товаров
            "error": result.get("error"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Playwright error: {exc}")


@router.post("/analyze-bids")
def analyze_bids(payload: dict):
    """
    Анализирует ставки конкурентов по ключевым словам через Яндекс Директ API.
    Возвращает: ставки, прогноз показов, кликов и бюджета.
    """
    keywords = payload.get("keywords", [])
    if not keywords:
        raise HTTPException(status_code=400, detail="keywords обязателен")

    from app.services.direct_commander import get_direct_commander
    dc = get_direct_commander()

    # Проверяем токен
    if not dc.token:
        return {
            "status": "no_token",
            "message": "YANDEX_DIRECT_TOKEN не настроен. Добавьте токен в .env",
            "keywords": keywords,
        }

    try:
        # Проверяем токен — получаем список кампаний
        campaigns = dc.get_campaigns()

        # Ставки по ключевым словам (только для существующих в кампаниях)
        bids = dc.get_keyword_bids(keywords)

        return {
            "status": "ok",
            "token_valid": True,
            "sandbox": dc.sandbox,
            "campaigns_count": len(campaigns),
            "keywords_checked": len(keywords),
            "bids": bids,
            "note": "Ставки показываются только для ключей, уже добавленных в кампании. Для прогноза по новым ключам используйте Яндекс Директ → Инструменты → Прогноз бюджета." if not dc.sandbox else "Режим Песочницы (Sandbox). Создайте тестовую кампанию для получения ставок.",
        }
    except Exception as exc:
        import traceback
        error_trace = traceback.format_exc()
        print("[ERROR] analyze_bids:", error_trace)
        raise HTTPException(status_code=500, detail=f"Yandex API error: {exc}\n{error_trace[:500]}")
