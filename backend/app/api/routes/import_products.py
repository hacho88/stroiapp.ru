import asyncio
import ssl
import urllib.request

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from app.db import import_store
from app.services.opencart_api import opencart_api

router = APIRouter()

IMAGE_SOURCE = "https://globalsnab.com"
_image_job = {"running": False, "done": 0, "failed": 0, "total": 0}

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def _download(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx) as resp:
            if resp.status != 200:
                return None
            data = resp.read()
            return data if len(data) > 500 else None
    except Exception:
        return None


async def _fetch_images_worker():
    _image_job["running"] = True
    _image_job["done"] = 0
    _image_job["failed"] = 0
    try:
        offset = 0
        while True:
            batch = import_store.get_needing_images(limit=50, offset=0)
            if not batch:
                break
            for item in batch:
                src = IMAGE_SOURCE + item["image_path"]
                data = await asyncio.get_event_loop().run_in_executor(None, _download, src)
                if not data:
                    _image_job["failed"] += 1
                    import_store.set_image(item["id"], "NOIMAGE")
                    continue
                ext = (item["image_path"].rsplit(".", 1)[-1] or "jpg").lower()
                fname = f"import_{item['id']}.{ext if ext in ('jpg','jpeg','png','gif','webp') else 'jpg'}"
                res = await opencart_api.upload_image(data, fname, "image/jpeg")
                path = res.get("path") or ""
                if res.get("status") == "uploaded" and path:
                    import_store.set_image(item["id"], path)
                    _image_job["done"] += 1
                else:
                    _image_job["failed"] += 1
                await asyncio.sleep(0.05)
            offset += 50
            _image_job["total"] = import_store.count_needing_images() + _image_job["done"] + _image_job["failed"]
    finally:
        _image_job["running"] = False


@router.post("/import/products/fetch-images")
async def fetch_images():
    if _image_job["running"]:
        return {"status": "ok", "running": True, **_image_job}
    _image_job["total"] = import_store.count_needing_images()
    asyncio.create_task(_fetch_images_worker())
    return {"status": "ok", "started": True, **_image_job}


@router.get("/import/products/image-status")
async def image_status():
    remaining = import_store.count_needing_images()
    return {**_image_job, "remaining": remaining}


@router.get("/import/products/stats")
async def import_stats():
    try:
        return import_store.stats()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/import/products")
async def import_list(limit: int = 50, page: int = 1, search: str = "", cat0: str = "", pushed: int | None = None):
    try:
        limit = max(1, min(500, limit))
        return import_store.list_products(limit=limit, page=page, search=search, cat0=cat0, pushed=pushed)
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
            return {"status": "ok", "product_id": pid, "category_id": cat_id}
        return {"status": "error", "detail": res}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
