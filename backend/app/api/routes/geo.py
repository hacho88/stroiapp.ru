"""
API роуты для геотаргетинга.
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/detect")
def geo_detect(request: Request):
    """Определить город посетителя по IP."""
    from app.services.geo_service import get_geo_service

    # Получаем IP из заголовков
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else None

    gs = get_geo_service()
    result = gs.detect_city_by_ip(client_ip)
    return {
        "status": "ok",
        "detected": result["detected"],
        "city": result["city"],
        "method": result["method"],
        "ip": result.get("ip"),
        "distance_km": result.get("distance_km"),
    }


@router.get("/cities")
def geo_cities(region: str | None = None):
    """Получить список городов. Можно фильтровать по региону."""
    from app.services.geo_service import get_geo_service

    gs = get_geo_service()
    if region:
        cities = gs.get_cities_for_region(region)
    else:
        cities = gs.get_all_cities()

    return {
        "status": "ok",
        "count": len(cities),
        "cities": cities,
    }


@router.get("/regions")
def geo_regions():
    """Получить список уникальных регионов."""
    from app.data.geo_regions import get_unique_regions

    return {
        "status": "ok",
        "regions": get_unique_regions(),
    }


@router.post("/describe")
def geo_describe(payload: dict):
    """Сгенерировать гео-описание для товара в указанном городе."""
    from app.services.geo_service import get_geo_service
    from app.data.geo_regions import get_city_by_id

    product_name = payload.get("product_name", "")
    city_id = payload.get("city_id", "")

    if not product_name:
        raise HTTPException(status_code=400, detail="product_name обязателен")

    city = get_city_by_id(city_id) if city_id else None
    if not city:
        # Default to Moscow
        city = get_city_by_id("moscow")

    gs = get_geo_service()
    result = gs.generate_geo_description(product_name, city)
    return {
        "status": "ok",
        "product": product_name,
        "geo_data": result,
    }


@router.post("/generate-pages")
async def geo_generate_pages(payload: dict | None = None, background_tasks: BackgroundTasks = None):
    """Создать таблицу и сгенерировать гео-страницы. limit: сколько товаров обработать (0 = все).
    Запускает генерацию в фоне — ответ возвращается сразу."""
    from app.services.geo_pages_service import get_geo_pages_service

    gps = get_geo_pages_service()
    limit = (payload or {}).get("limit", 50)

    # Step 1: Create table
    table_result = await gps.create_table()
    if table_result.get("status") != "ok":
        return {"status": "error", "step": "create_table", "details": table_result}

    # Step 2: Schedule generation as background task
    import asyncio
    from app.services.geo_auto_generator import get_geo_auto_generator

    auto = get_geo_auto_generator()

    async def _run_generation():
        """Run generation in background, surviving HTTP disconnect."""
        try:
            gen_result = await gps.generate_all(limit=limit)
            print(f"[GeoGen] Background generation complete: {gen_result.get('total_products', 0)} products, {gen_result.get('total_generated', 0)} pages")
        except Exception as e:
            print(f"[GeoGen] Background generation error: {str(e)[:300]}")

    # Schedule as a task that survives request disconnect
    asyncio.create_task(_run_generation())

    return {
        "status": "started",
        "message": f"Generation started for {limit if limit > 0 else 'all'} products. Check /geo/status for progress.",
        "table_created": True,
    }


@router.get("/status")
def geo_status():
    """Статус авто-генератора гео-страниц."""
    from app.services.geo_auto_generator import get_geo_auto_generator
    auto = get_geo_auto_generator()
    return auto.status()
