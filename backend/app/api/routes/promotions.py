from fastapi import APIRouter, HTTPException
from app.services.opencart_api import opencart_api

router = APIRouter(prefix="/promotions", tags=["promotions"])

# Временное хранилище акций в памяти (пока без БД)
_promotions = []
_promotion_counter = 1


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Акции и локомотивы — раздел работает"}


@router.post("/find-bundles")
async def find_bundles(payload: dict):
    """Поиск товаров-связок (локомотивы + вагоны) по категориям"""
    try:
        products = await opencart_api.get_action("product/list", {"limit": 200})
        items = products.get("products", []) if isinstance(products, dict) else (products if isinstance(products, list) else [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Группировка по категории (если есть category_id)
    by_cat = {}
    for p in items:
        cat = p.get("category_id", 0)
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(p)

    bundles = []
    for cat_id, prods in by_cat.items():
        if len(prods) < 2:
            continue
        # Локомотив — самый дорогой, вагон — следующий по цене
        sorted_prods = sorted(prods, key=lambda x: float(x.get("price", 0) or 0), reverse=True)
        locomotive = sorted_prods[0]
        wagon = sorted_prods[1]
        locomotive_price = float(locomotive.get("price", 0) or 0)
        wagon_price = float(wagon.get("price", 0) or 0)
        discount = round(wagon_price * 0.1, 2)  # 10% скидка на вагон
        bundles.append({
            "category_id": cat_id,
            "locomotive": {
                "product_id": locomotive.get("product_id"),
                "name": locomotive.get("name", ""),
                "price": locomotive_price,
            },
            "wagon": {
                "product_id": wagon.get("product_id"),
                "name": wagon.get("name", ""),
                "price": wagon_price,
            },
            "discount": discount,
            "bundle_price": round(locomotive_price + wagon_price - discount, 2),
            "savings": discount,
        })

    return {"bundles": bundles[:10], "total_found": len(bundles)}


@router.post("/create")
async def create_promotion(payload: dict):
    """Создание динамической акции"""
    global _promotion_counter
    promo = {
        "promotion_id": _promotion_counter,
        "status": "active",
        "name": payload.get("name", "Акция без названия"),
        "type": payload.get("type", "bundle"),
        "discount_pct": payload.get("discount_pct", 10),
        "products": payload.get("products", []),
        "created_at": "2026-05-30",
    }
    _promotions.append(promo)
    _promotion_counter += 1
    return {"promotion_id": promo["promotion_id"], "status": "created", "promotion": promo}


@router.get("/list")
async def list_promotions():
    """Список активных акций"""
    return {"promotions": _promotions}
