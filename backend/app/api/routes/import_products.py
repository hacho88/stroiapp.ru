from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from app.db import import_store
from app.services.opencart_api import opencart_api
from app.services.product_db import product_db

router = APIRouter()


@router.get("/import/products/needing-images")
async def needing_images(limit: int = 100, offset: int = 0):
    """Products that have a source image_path but no uploaded OpenCart image yet."""
    try:
        limit = max(1, min(500, limit))
        return {"total": import_store.count_needing_images(), "products": import_store.get_needing_images(limit=limit, offset=offset)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/import/products/{item_id}/set-image")
async def set_image(item_id: int, payload: dict = Body(...)):
    try:
        import_store.set_image(item_id, payload.get("image") or "")
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/import/products/stats")
async def import_stats():
    try:
        return import_store.stats()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/import/products/categories")
async def import_categories():
    try:
        return {"tree": import_store.category_tree()}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/import/products")
async def import_list(limit: int = 50, page: int = 1, search: str = "", cat0: str = "", cat1: str = "", cat2: str = "", pushed: int | None = None):
    try:
        limit = max(1, min(500, limit))
        return import_store.list_products(limit=limit, page=page, search=search, cat0=cat0, cat1=cat1, cat2=cat2, pushed=pushed)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/import/products/{item_id}")
async def import_get(item_id: int):
    try:
        p = import_store.get_product(item_id)
        if not p:
            return {"status": "error", "detail": "not found"}
        return p
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/import/products/bulk")
async def import_bulk(payload: dict = Body(...)):
    try:
        products = payload.get("products") or []
        if not products:
            return {"status": "error", "detail": "products required"}
        result = import_store.bulk_insert(products)
        return {"status": "ok", **result}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.delete("/import/products/clear")
async def import_clear():
    try:
        return {"status": "ok", "deleted": import_store.clear_all()}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.delete("/import/products/{item_id}")
async def import_delete(item_id: int):
    try:
        import_store.delete_product(item_id)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


async def _find_category_id(name: str) -> int:
    """Find an existing OpenCart category id by exact name (searches all)."""
    if not name:
        return 0
    data = await opencart_api.get_action("category/list")
    for c in (data.get("categories") or []):
        if (c.get("name") or "").strip().lower() == name.strip().lower():
            return int(c.get("category_id") or 0)
    return 0


async def _ensure_category_path(cat0: str, cat1: str, cat2: str) -> int:
    """Resolve leaf category id for path cat0>cat1>cat2, creating missing levels."""
    names = [n for n in (cat0, cat1, cat2) if n]
    if not names:
        return 0
    data = await opencart_api.get_action("category/list")
    existing = data.get("categories") or []
    by_key = {}
    for c in existing:
        by_key[(int(c.get("parent_id") or 0), (c.get("name") or "").strip().lower())] = int(c.get("category_id") or 0)
    parent = 0
    for name in names:
        key = (parent, name.strip().lower())
        if key in by_key:
            parent = by_key[key]
            continue
        created = await opencart_api.post_action("category/add", {"name": name, "parent_id": parent, "status": 1})
        new_id = int(created.get("category_id") or created.get("id") or 0)
        if not new_id:
            break
        parent = new_id
    return parent


@router.post("/import/products/{item_id}/push")
async def import_push(item_id: int):
    """Push one imported product to the live OpenCart site."""
    try:
        item = import_store.get_product(item_id)
        if not item:
            return {"status": "error", "detail": "not found"}
        if item.get("pushed") and item.get("product_id"):
            return {"status": "ok", "product_id": item["product_id"], "already": True}
        cat_id = await _ensure_category_path(item.get("cat0", ""), item.get("cat1", ""), item.get("cat2", ""))
        payload = {
            "name": item["name"],
            "model": item.get("prop_type") or item["name"],
            "sku": item.get("sku") or item.get("xml_id") or "",
            "price": item.get("price") or 0,
            "quantity": 1000,
            "status": 1,
            "image": item.get("image") or "",
            "weight": (item.get("weight") or 0) / 1000.0,
            "description": item.get("description") or "",
            "meta_title": item["name"],
            "category_id": cat_id,
        }
        res = await opencart_api.post_action("product/add", payload)
        pid = int(res.get("product_id") or res.get("id") or 0)
        if pid:
            import_store.mark_pushed(item_id, pid)
            # Кладём в «Товары на сайте» (ProductDB) — сразу виден на moscow.stroiapp.ru
            try:
                product_db.sync_from_opencart([{
                    "product_id": pid,
                    "sku": payload["sku"],
                    "name": payload["name"],
                    "model": payload["model"],
                    "price": payload["price"],
                    "quantity": payload["quantity"],
                    "image": payload["image"],
                }])
            except Exception:
                pass
            return {"status": "ok", "product_id": pid, "category_id": cat_id}
        return {"status": "error", "detail": res}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
