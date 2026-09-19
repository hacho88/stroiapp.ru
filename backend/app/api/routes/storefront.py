import time

from fastapi import APIRouter

from app.services.opencart_api import opencart_api
from app.services.product_db import product_db

# Публичный каталог для гео-витрин (moscow.stroiapp.ru и др.).
# Читается из ProductDB — того же источника, что и раздел «ТОВАРЫ НА САЙТЕ».
# Отдаёт ТОЛЬКО безопасные поля: без себестоимости, опта, ROI и служебных метрик.
router = APIRouter(prefix="/storefront", tags=["storefront"])

SHOP = "https://stroiapp.ru"
IMG = SHOP + "/image/"


def _img(image: str) -> str:
    if not image:
        return ""
    s = str(image)
    return s if s.startswith("http") else IMG + s


def _product_url(pid) -> str:
    return f"{SHOP}/index.php?route=product/product&product_id={pid}"


def _public(p) -> dict:
    return {
        "id": p.product_id,
        "sku": p.sku,
        "name": p.name,
        "price": p.retail_price,
        "image": _img(p.image),
        "quantity": p.quantity,
        "category_id": p.category_id,
        "url": _product_url(p.product_id),
    }


@router.get("/products")
def storefront_products(limit: int = 48, category_id: int | None = None, search: str = ""):
    items = product_db.list_products()
    if category_id is not None:
        items = [p for p in items if p.category_id == category_id]
    if search:
        q = search.lower()
        items = [p for p in items if q in (p.name or "").lower() or q in (p.sku or "").lower()]
    out = [_public(p) for p in items if p.name and p.retail_price > 0]
    return {"status": "ok", "count": len(out[:limit]), "products": out[:limit]}


_cat_cache = {"ts": 0.0, "data": []}


@router.get("/categories")
async def storefront_categories():
    # кэш 5 мин — категории меняются редко, а OpenCart дергать на каждый хит не надо
    if _cat_cache["data"] and time.time() - _cat_cache["ts"] < 300:
        return {"status": "ok", "categories": _cat_cache["data"]}
    data = await opencart_api.get_action("category/list")
    arr = (data or {}).get("categories") or []
    top = [
        {"category_id": c.get("category_id"), "name": c.get("name"), "image": _img(c.get("image"))}
        for c in arr
        if str(c.get("parent_id")) == "0" and c.get("name")
    ]
    if top:
        _cat_cache.update({"ts": time.time(), "data": top})
    return {"status": "ok", "categories": top}
