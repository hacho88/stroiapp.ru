from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.opencart_api import opencart_api
from app.services.tender_monitor import tender_monitor
from app.services.max_notifier import max_notifier

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get("/status")
def get_status():
    sources = []
    if settings.tenderguru_api_code:
        sources.append({"name": "TenderGuru", "status": "active", "type": "API", "coverage": "44-ФЗ, 223-ФЗ (госзакупки)"})
    else:
        sources.append({"name": "TenderGuru", "status": "no key", "type": "API", "coverage": "44-ФЗ, 223-ФЗ"})
    if settings.damia_api_key:
        sources.append({"name": "DaMIA", "status": "active", "type": "API", "coverage": "44-ФЗ, 223-ФЗ, 615-ПП"})
    else:
        sources.append({"name": "DaMIA", "status": "no key", "type": "API", "coverage": "44-ФЗ, 223-ФЗ, 615-ПП"})
    sources.append({"name": "B2B-Center", "status": "active", "type": "HTTP парсинг", "coverage": "коммерческие тендеры"})
    return {"status": "ok", "sources": sources, "total_sources": len(sources)}


@router.post("/searchWon")
async def search_won_tenders(payload: dict):
    """Найти выигранные тендеры за последние N дней по нашим товарам."""
    days = payload.get("days", 7)
    keywords = payload.get("keywords")
    tenders = await tender_monitor.find_won_tenders(days=days, keywords=keywords)
    if tenders and isinstance(tenders[0], dict) and "error" in tenders[0]:
        raise HTTPException(status_code=400, detail=tenders[0]["error"])
    return {"status": "ok", "tenders": tenders, "count": len(tenders)}


@router.post("/matchProducts")
async def match_products(payload: dict):
    """Сопоставить позиции тендера с нашими товарами."""
    contract = payload.get("contract", {})
    if not contract:
        raise HTTPException(status_code=400, detail="contract обязателен")
    result = tender_monitor.match_tender_to_products(contract)
    return {"status": "ok", **result}


@router.post("/generateKP")
async def generate_kp(payload: dict):
    """AI генерирует коммерческое предложение для победителя тендера со сметой."""
    winner = payload.get("winner", {})
    matched_products = payload.get("matched_products", [])
    building = payload.get("building")
    estimate = payload.get("estimate")
    if not matched_products:
        raise HTTPException(status_code=400, detail="matched_products обязателен")
    kp = await tender_monitor.generate_kp_for_winner(
        winner, matched_products, building=building, estimate=estimate
    )
    return kp


@router.post("/sendKP")
async def send_kp(payload: dict):
    """Отправить КП на email победителя."""
    kp = payload.get("kp", {})
    to_email = payload.get("email", "")
    if not to_email:
        raise HTTPException(status_code=400, detail="email обязателен")
    result = await tender_monitor.send_kp_email(kp, to_email)
    return result


@router.post("/monitorAndSend")
async def monitor_and_send(payload: dict):
    """Полный цикл: найти выигранные тендеры → определить здание → смета → КП → отправить."""
    days = payload.get("days", 7)
    auto_send = payload.get("auto_send", False)
    result = await tender_monitor.monitor_and_send(days=days, auto_send=auto_send)

    # MAX-уведомление о найденных тендерах
    if result.get("matched_tenders", 0) > 0:
        for r in result["results"][:10]:
            winner = r.get("winner", {})
            building = r.get("building", {})
            estimate = r.get("estimate", {})
            msg = (
                f"<b>📋 Тендер по нашим товарам</b><br><br>"
                f"Победитель: {winner.get('winner_name', '?')}<br>"
                f"Объект: {building.get('building_type', '?')} {building.get('building_subtype', '')}<br>"
                f"Площадь: {building.get('area_m2', 0)} м², этажей: {building.get('floors', 1)}<br>"
                f"Совпадений товаров: {r.get('matched_count', 0)}<br>"
                f"Смета: {estimate.get('total', r.get('total_estimate', 0))} ₽"
            )
            try:
                await max_notifier.send_message(text=msg)
            except Exception:
                pass

    return result


@router.post("/detectBuilding")
async def detect_building(payload: dict):
    """AI определяет тип здания по тексту тендера."""
    contract = payload.get("contract", {})
    if not contract:
        raise HTTPException(status_code=400, detail="contract обязателен")
    result = await tender_monitor.detect_building_type(contract)
    return {"status": "ok", "building": result}


@router.post("/calculateEstimate")
async def calculate_estimate(payload: dict):
    """AI рассчитывает смету по типу здания и нашим товарам."""
    building = payload.get("building", {})
    matched_products = payload.get("matched_products", [])
    if not matched_products:
        raise HTTPException(status_code=400, detail="matched_products обязателен")
    result = await tender_monitor.calculate_estimate(building, matched_products)
    return {"status": "ok", "estimate": result}


@router.post("/search")
async def search_tenders(payload: dict):
    """Поиск тендеров — возвращаем наши товары как потенциальные позиции для тендера."""
    region = payload.get("region", "Москва")
    try:
        products = await opencart_api.get_action("product/list", {"limit": 100})
        items = products.get("products", []) if isinstance(products, dict) else (products if isinstance(products, list) else [])
    except Exception:
        items = []

    # Fallback: локальная база
    if not items:
        from app.services.product_db import product_db
        items = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "price": p.retail_price,
            }
            for p in product_db.list_products() if p.retail_price > 0
        ][:20]

    tenders = []
    for p in items[:20]:
        price_non_cash = (float(p.get("price", 0) or 0)) * 1.285
        tenders.append({
            "tender_id": f"T-{p.get('product_id')}",
            "name": p.get("name", ""),
            "estimated_volume": "100-500",
            "unit": "шт.",
            "our_price_beznal": round(price_non_cash, 2),
            "product_id": p.get("product_id"),
        })

    return {"tenders": tenders, "region": region, "total_found": len(tenders)}


@router.post("/check-coverage")
async def check_coverage(payload: dict):
    """Проверка покрытия ассортиментом тендера."""
    tender_items = payload.get("items", [])
    if not tender_items:
        return {"covered_items": [], "missing_items": [], "coverage_percent": 0}

    try:
        products = await opencart_api.get_action("product/list", {"limit": 500})
        our_names = [p.get("name", "").lower() for p in (products.get("products", []) if isinstance(products, dict) else (products if isinstance(products, list) else []))]
    except Exception:
        our_names = []

    covered = []
    missing = []
    for item in tender_items:
        name = item.get("name", "").lower()
        matched = any(name in on or on in name for on in our_names)
        if matched:
            covered.append(item)
        else:
            missing.append(item)

    coverage = round((len(covered) / len(tender_items)) * 100, 1) if tender_items else 0
    return {"covered_items": covered, "missing_items": missing, "coverage_percent": coverage}


@router.post("/submit")
async def submit_tender(payload: dict):
    """Подготовка заявки на тендер (генерация КП)."""
    items = payload.get("items", [])
    total = sum(float(i.get("our_price_beznal", 0) or i.get("price", 0)) * int(i.get("quantity", 1)) for i in items)
    return {"status": "prepared", "document_url": None, "total_price": round(total, 2), "items_count": len(items), "payment_type": "beznal"}
