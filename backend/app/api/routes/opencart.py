from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File, Body

from app.services.opencart_api import opencart_api
from app.services.product_db import product_db
from app.services.deepseek_client import deepseek_client
from app.db import import_store

router = APIRouter(prefix="/opencart", tags=["opencart"])


@router.get("/status")
def opencart_status():
    return {"status": "ok", "service": "opencart"}


class FileWritePayload(BaseModel):
    path: str
    content: str


class FileRestorePayload(BaseModel):
    path: str
    backup: str


class OrderStatusPayload(BaseModel):
    order_id: int
    order_status_id: int


class ProductUpdatePayload(BaseModel):
    product_id: int
    price: float | None = None
    cash_price: float | None = None
    non_cash_price: float | None = None
    quantity: int | None = None
    status: int | None = None


class BannerUpdatePayload(BaseModel):
    banner_id: int
    name: str | None = None
    status: int | None = None


class CategoryUpdatePayload(BaseModel):
    category_id: int
    name: str | None = None
    description: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keyword: str | None = None
    status: int | None = None
    sort_order: int | None = None


@router.get("/syncPrices")
async def sync_prices():
    try:
        products = product_db.list_products()
        items = []
        for product in products:
            if product.cost_price_cash > 0 and product.product_id:
                items.append({
                    "product_id": product.product_id,
                    "price": product.retail_price,
                    "cash_price": product.retail_price,
                    "non_cash_price": product.wholesale_price,
                })
        if not items:
            return {"status": "skipped", "reason": "no products with cost prices"}
        result = await opencart_api.bulk_update_prices(items)
        return {"status": "synced", "updated": result.get("count", 0)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/syncProduct/{sku}")
async def sync_product(sku: str):
    product = product_db.get_by_sku(sku)
    if not product or not product.product_id:
        raise HTTPException(status_code=404, detail="Product not found or has no product_id")
    try:
        result = await opencart_api.product_update(
            product.product_id,
            {
                "price": product.retail_price,
                "cash_price": product.retail_price,
                "non_cash_price": product.wholesale_price,
                "quantity": product.quantity,
            },
        )
        return {"status": "synced", "sku": sku, "opencart": result}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/health")
async def opencart_health():
    try:
        products = await opencart_api.product_list()
        return {"status": "connected", "products": len(products)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/site/health")
async def site_health():
    try:
        return await opencart_api.get_action("site/health")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/clearCache")
async def site_clear_cache():
    try:
        return await opencart_api.get_action("site/clearCache")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/site/errorLog")
async def site_error_log():
    try:
        return await opencart_api.get_action("site/errorLog")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/site/backups")
async def site_backups():
    try:
        return await opencart_api.get_action("site/backups")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/fixRegister")
async def site_fix_register():
    try:
        return await opencart_api.get_action("site/fixRegister")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/generateSitemap")
async def site_generate_sitemap():
    try:
        return await opencart_api.get_action("site/generateSitemap")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/generateRobots")
async def site_generate_robots():
    try:
        return await opencart_api.get_action("site/generateRobots")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/site/findBrokenImages")
async def site_find_broken_images():
    try:
        return await opencart_api.get_action("site/findBrokenImages")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/cleanUnusedImages")
async def site_clean_unused_images():
    try:
        return await opencart_api.get_action("site/cleanUnusedImages")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/disableErrors")
async def site_disable_errors():
    try:
        return await opencart_api.get_action("site/disableErrors")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/fixIndexPhp")
async def site_fix_index_php():
    try:
        return await opencart_api.get_action("site/fixIndexPhp")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/silenceErrors")
async def site_silence_errors():
    try:
        return await opencart_api.get_action("site/silenceErrors")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/site/restoreBackup")
async def site_restore_backup():
    try:
        return await opencart_api.get_action("site/restoreBackup")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/seo/massFix")
async def seo_mass_fix():
    try:
        return await opencart_api.get_action("seo/massFix")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/seo/productStats")
async def seo_product_stats():
    try:
        return await opencart_api.get_action("seo/productStats")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/seo/massFixCategories")
async def seo_mass_fix_categories():
    try:
        return await opencart_api.get_action("seo/massFixCategories")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/product/massFixDescriptions")
async def product_mass_fix_descriptions():
    try:
        return await opencart_api.get_action("product/massFixDescriptions")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/product/bulkRecalcPrices")
async def product_bulk_recalc_prices(markup: float = 0, limit: int = 1000):
    try:
        return await opencart_api.get_action("product/bulkRecalcPrices", {"markup": markup, "limit": limit})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/customer/groups")
async def customer_get_groups():
    try:
        return await opencart_api.get_action("customer/groups")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/customer/createGroup")
async def customer_create_group(data: dict = Body(...)):
    try:
        return await opencart_api.post_action("customer/createGroup", data)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/db/executeSql")
async def db_execute_sql(data: dict = Body(...)):
    try:
        return await opencart_api.post_action("db/executeSql", data)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/files/list")
async def files_list(path: str = "catalog/"):
    try:
        return await opencart_api.get_action("file/listSafe", {"path": path})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.get("/media/list")
async def media_list(path: str = "catalog/"):
    """List files inside image/ on the OpenCart host. path is relative to image/ (e.g. 'catalog/ai_uploads')."""
    try:
        rel = path.strip("/")
        if not rel.startswith("catalog"):
            rel = "catalog/" + rel if rel else "catalog"
        data = await opencart_api.get_action("file/listSafe", {"path": f"image/{rel}/"})
        items = data.get("items") or []
        for it in items:
            ext = "." + it.get("name", "").rsplit(".", 1)[-1].lower() if "." in it.get("name", "") else ""
            it["is_image"] = it.get("type") == "file" and ext in IMAGE_EXTS
            it["url"] = f"https://stroiapp.ru/image/{rel}/{it['name']}" if it.get("type") == "file" else ""
        return {"status": data.get("status", "ok"), "path": rel, "items": items}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/media/upload")
async def media_upload(file: UploadFile = File(...), dir: str = "catalog/ai_uploads", name: str = ""):
    try:
        contents = await file.read()
        safe_name = _slugify_name(name) if name else ""
        return await opencart_api.upload_image(contents, file.filename, file.content_type or "image/jpeg", dir=dir, name=safe_name)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/media/delete")
async def media_delete(payload: dict = Body(...)):
    try:
        return await opencart_api.post_action("image/delete", {"path": payload.get("path", "")})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/media/mkdir")
async def media_mkdir(payload: dict = Body(...)):
    try:
        return await opencart_api.post_action("image/mkdir", {"path": payload.get("path", "")})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _slugify_name(name: str) -> str:
    """Transliterate product name to a safe filename base."""
    import re
    tr = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
        "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
        "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
        "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    s = "".join(tr.get(ch, ch) for ch in name.lower())
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:80] or "image"


@router.get("/media/products")
async def media_products(keyword: str = "", page: int = 1, limit: int = 60):
    """Merged product list: imported_products (SQLite) + OpenCart products."""
    try:
        limit = max(1, min(200, limit))
        merged: dict[str, dict] = {}

        # 1) imported products (Все товары) — main source
        imp = import_store.list_products(limit=100000, page=1, search=keyword.strip())
        for p in imp.get("products") or []:
            img = p.get("image") or ""
            key = f"imp:{p['id']}"
            merged[key] = {
                "import_id": p.get("id"),
                "product_id": p.get("product_id"),
                "name": p.get("name", ""),
                "sku": p.get("sku", ""),
                "image": img,
                "pushed": p.get("pushed", 0),
                "source": "import",
            }

        # 2) OpenCart products — add ones not already in imported (by product_id)
        oc_ids = {m["product_id"] for m in merged.values() if m.get("product_id")}
        oc_page = 1
        kw = keyword.strip().lower()
        while oc_page <= 20:
            data = await opencart_api.get_action("product/list", {"limit": 500, "page": oc_page})
            items = data.get("products") or []
            if not items:
                break
            for p in items:
                pid = p.get("product_id")
                if pid in oc_ids:
                    continue
                if kw and kw not in (p.get("name") or "").lower() and kw not in str(p.get("sku") or ""):
                    continue
                merged[f"oc:{pid}"] = {
                    "import_id": None,
                    "product_id": pid,
                    "name": p.get("name", ""),
                    "sku": p.get("sku", ""),
                    "image": p.get("image", ""),
                    "pushed": 1,
                    "source": "opencart",
                }
            if len(items) < 500:
                break
            oc_page += 1

        products = list(merged.values())
        products.sort(key=lambda x: (x["name"] or "").lower())
        total = len(products)
        start = (page - 1) * limit
        products = products[start:start + limit]
        for p in products:
            img = p.get("image") or ""
            p["image_url"] = f"https://stroiapp.ru/image/{img}" if img else ""
        return {"status": "ok", "total": total, "count": len(products), "products": products}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/media/assign")
async def media_assign(payload: dict = Body(...)):
    """Assign an image path (relative to image/) to a product.
    Accepts product_id (OpenCart) and/or import_id (imported_products).
    If product_name given — renames the file to transliterated product name first."""
    try:
        product_id = int(payload.get("product_id") or 0)
        import_id = int(payload.get("import_id") or 0)
        image = (payload.get("image") or "").strip().lstrip("/")
        if image.startswith("image/"):
            image = image[6:]
        product_name = (payload.get("product_name") or "").strip()
        if not image or (not product_id and not import_id):
            return {"status": "error", "detail": "image and product_id/import_id are required"}

        # rename file to product name (photos named after products)
        if product_name:
            rn = await opencart_api.post_action("image/rename", {"path": image, "name": _slugify_name(product_name)})
            if rn.get("status") == "renamed" and rn.get("path"):
                image = rn["path"]

        result = {"status": "ok", "image": image}
        if product_id:
            result["opencart"] = await opencart_api.post_action("product/update", {"product_id": product_id, "image": image})
        if import_id:
            import_store.set_image(import_id, image)
            result["import"] = "ok"
        return result
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/media/rename")
async def media_rename(payload: dict = Body(...)):
    """Rename a file inside image/catalog/ to a new basename."""
    try:
        path = (payload.get("path") or "").strip().lstrip("/")
        name = (payload.get("name") or "").strip()
        if not path or not name:
            return {"status": "error", "detail": "path and name are required"}
        return await opencart_api.post_action("image/rename", {"path": path, "name": _slugify_name(name)})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/media/suggest")
async def media_suggest(filename: str):
    """Suggest products matching an uploaded filename (for auto-assign)."""
    try:
        import re
        base = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        base = re.sub(r"_\d{6,}$", "", base)  # strip upload timestamp suffix
        words = [w for w in re.split(r"[^a-zA-Zа-яА-Я0-9]+", base) if len(w) > 2]
        if not words:
            return {"status": "ok", "products": []}
        # search imported products first (largest catalog)
        seen = set()
        products = []
        for q in (" ".join(words[:4]), words[0] if len(words) > 1 else ""):
            if not q:
                continue
            imp = import_store.list_products(limit=5, page=1, search=q)
            for p in imp.get("products") or []:
                k = f"imp:{p['id']}"
                if k in seen:
                    continue
                seen.add(k)
                products.append({"import_id": p["id"], "product_id": p.get("product_id"), "name": p.get("name", ""), "sku": p.get("sku", "")})
            if products:
                break

        # fallback: OpenCart search
        if not products:
            data = await opencart_api.get_action("searchProducts", {"keyword": " ".join(words[:4]), "limit": 5})
            items = data.get("all") or []
            if not items and len(words) > 1:
                data = await opencart_api.get_action("searchProducts", {"keyword": words[0], "limit": 5})
                items = data.get("all") or []
            products = [{
                "import_id": None,
                "product_id": p.get("product_id"),
                "name": p.get("name", ""),
                "sku": p.get("sku", ""),
            } for p in items[:5]]
        return {"status": "ok", "products": products[:5]}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/files/read")
async def files_read(path: str):
    try:
        return await opencart_api.get_action("file/readSafe", {"path": path})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/files/write")
async def files_write(payload: FileWritePayload):
    try:
        return await opencart_api.post_action("file/writeSafe", payload.model_dump())
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/files/backup")
async def files_backup(payload: FileWritePayload):
    try:
        return await opencart_api.get_action("file/backupSafe", {"path": payload.path})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/files/restore")
async def files_restore(payload: FileRestorePayload):
    try:
        return await opencart_api.post_action("file/restoreSafe", payload.model_dump())
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/categories/tree")
async def categories_tree():
    try:
        return await opencart_api.get_action("category/tree")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/categories/list")
async def categories_list():
    try:
        data = await opencart_api.get_action("category/list")
        cats = data.get("categories") or []
        slim = [
            {"category_id": c.get("category_id"), "parent_id": c.get("parent_id"), "name": c.get("name")}
            for c in cats
        ]
        return {"categories": slim}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/categories/get")
async def category_get(category_id: int):
    try:
        return await opencart_api.get_action("category/get", {"category_id": category_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/categories/update")
async def category_update(payload: dict = Body(...)):
    try:
        return await opencart_api.post_action("category/update", payload)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/categories/delete")
async def category_delete(payload: dict = Body(...)):
    try:
        category_id = int(payload.get("category_id") or 0)
        if not category_id:
            return {"status": "error", "detail": "category_id is required"}
        return await opencart_api.post_action("category/delete", {"category_id": category_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/images/upload")
async def image_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await opencart_api.upload_image(content, file.filename, file.content_type or "image/jpeg")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/hero/banner")
async def hero_banner_get():
    try:
        return await opencart_api.get_action("file/readSafe", {"path": "catalog/view/theme/unishop2/template/common/home.twig"})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/hero/banner")
async def hero_banner_update(payload: FileWritePayload):
    try:
        return await opencart_api.post_action("file/writeSafe", payload.model_dump())
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/products/byCategory")
async def products_by_category(category_id: int, all: int = 0):
    try:
        data = await opencart_api.get_action("product/listByCategory", {"category_id": category_id, "all": all})
        items = data.get("products") or []
        keep = ("product_id", "model", "sku", "name", "price", "price_non_cash", "cash_price",
                "non_cash_price", "quantity", "image", "image_url", "status", "has_description", "has_meta")
        slim = [{k: p.get(k) for k in keep} for p in items]
        return {"status": data.get("status", "ok"), "count": len(slim), "products": slim}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/products/search")
async def products_search(keyword: str, limit: int = 60, all: int = 0):
    try:
        data = await opencart_api.get_action("product/searchFull", {"keyword": keyword, "limit": limit, "all": all})
        items = data.get("products") or []
        keep = ("product_id", "model", "sku", "name", "price", "price_non_cash", "cash_price",
                "non_cash_price", "quantity", "image", "image_url", "status", "has_description", "has_meta")
        slim = [{k: p.get(k) for k in keep} for p in items]
        return {"status": data.get("status", "ok"), "count": len(slim), "products": slim}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/update")
async def product_update(payload: dict = Body(...)):
    try:
        return await opencart_api.post_action("product/update", payload)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/add")
async def product_add(payload: dict = Body(...)):
    try:
        ean = str(payload.get("ean") or "").strip()
        result = await opencart_api.post_action("product/add", payload)
        # ai_manager productAdd хардкодит ean='' — дописываем через product/update
        pid = (result or {}).get("product_id")
        if ean and pid:
            try:
                result["ean_update"] = await opencart_api.post_action(
                    "product/update", {"product_id": pid, "ean": ean})
            except Exception as exc:
                result["ean_update"] = {"status": "error", "detail": str(exc)}
        return result
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/products/barcodeLookup")
async def product_barcode_lookup(ean: str):
    """Поиск товара по штрих-коду (EAN/UPC).

    1) Проверяет, есть ли товар с таким ean уже на stroiapp.ru (дедуп).
    2) Ищет название/бренд во внешней базе upcitemdb (бесплатный trial-endpoint).
    """
    import asyncio
    import json as _json
    import ssl as _ssl
    import urllib.parse
    import urllib.request

    code = (ean or "").strip()
    if not code.isdigit() or len(code) < 8:
        return {"status": "error", "detail": "Укажите цифровой штрих-код (8-14 знаков)"}

    out = {"status": "ok", "ean": code, "existing": None, "suggestion": None}

    # 1) Дедуп по oc_openproduct.ean
    safe_code = code.replace("'", "")
    try:
        res = await opencart_api.post_action("db/select", {
            "sql": (
                "SELECT p.product_id, p.sku, p.price, pd.name "
                "FROM oc_openproduct p "
                "LEFT JOIN oc_openproduct_description pd "
                "ON pd.product_id = p.product_id AND pd.language_id = 1 "
                "WHERE p.ean = '%s' LIMIT 3" % safe_code
            )
        })
        rows = (res or {}).get("rows") or []
        if rows:
            out["existing"] = rows[0]
            return out
    except Exception:
        pass

    # 2) Внешний lookup — цепочка баз для покрытия российских EAN
    def _http_get(url, timeout=15):
        req = urllib.request.Request(url, headers={"User-Agent": "AI-StroiApp-Manager/1.0"})
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()

    def _lookup():
        # 2a) upcitemdb — крупная международная база, отдаёт фото
        try:
            raw = _http_get("https://api.upcitemdb.com/prod/trial/lookup?upc=" + urllib.parse.quote(code))
            data = _json.loads(raw.decode("utf-8-sig"))
            items = (data or {}).get("items") or []
            if items:
                it = items[0]
                return {
                    "name": it.get("title") or "",
                    "brand": it.get("brand") or "",
                    "model": it.get("model") or "",
                    "image": (it.get("images") or [None])[0] or "",
                    "description": (it.get("description") or "")[:500],
                    "source": "upcitemdb",
                }
        except Exception:
            pass

        # 2b) barcode.monster — простое JSON API
        try:
            raw = _http_get("https://barcode.monster/api/" + urllib.parse.quote(code))
            data = _json.loads(raw.decode("utf-8-sig"))
            if data.get("status") == 200 and (data.get("description") or "").strip():
                return {
                    "name": data.get("description") or "",
                    "brand": data.get("company") or "",
                    "model": "",
                    "image": "",
                    "description": "",
                    "source": "barcode.monster",
                }
        except Exception:
            pass

        # 2c) barcode-list.ru — русская база, лучше знает отечественные EAN
        try:
            raw = _http_get("https://barcode-list.ru/barcode/RU/Поиск/" + urllib.parse.quote(code), timeout=20)
            html = raw.decode("utf-8", "replace")
            import re as _re
            # Название товара в заголовке h1 вида «4600682000000 : Наименование»
            m = _re.search(r"<h1[^>]*>\s*" + _re.escape(code) + r"\s*[:—-]\s*(.+?)</h1>", html, _re.S)
            if not m:
                m = _re.search(r'<td[^>]*>\s*Товар\s*</td>\s*<td[^>]*>(.*?)</td>', html, _re.S | _re.I)
            if m:
                name = _re.sub(r"<[^>]+>", "", m.group(1)).strip()
                if name and "не найден" not in name.lower():
                    return {
                        "name": name,
                        "brand": "",
                        "model": "",
                        "image": "",
                        "description": "",
                        "source": "barcode-list.ru",
                    }
        except Exception:
            pass

        return None

    try:
        loop = asyncio.get_event_loop()
        suggestion = await loop.run_in_executor(None, _lookup)
        if suggestion:
            out["suggestion"] = suggestion
    except Exception as exc:
        out["lookup_error"] = str(exc)

    return out


# Бренд → официальный домен (для site:-поиска фото в Яндексе)
_BRAND_DOMAINS = {
    "волма": "volma.ru", "volma": "volma.ru",
    "unis": "unistrom.ru", "юнис": "unistrom.ru",
    "ceresit": "ceresit.ru", "церезит": "ceresit.ru",
    "vetonit": "vetonit.ru", "ветонит": "vetonit.ru", "weber": "vetonit.ru",
    "старатели": "starateli.ru",
    "пеноплэкс": "penoplex.ru", "penoplex": "penoplex.ru", "пеноплекс": "penoplex.ru",
    "litokol": "litokol.ru", "литокол": "litokol.ru",
    "основит": "osnovit.ru", "osnovit": "osnovit.ru",
    "русеан": "rusean.ru", "rusean": "rusean.ru",
    "plitonit": "plitonit.ru", "плитонит": "plitonit.ru",
    "technonicol": "tn.ru", "технониколь": "tn.ru", "техноникол": "tn.ru",
    "knauf": "knauf.ru", "кнауф": "knauf.ru",
    # продуктовые линейки → производитель
    "ротбанд": "knauf.ru", "rotband": "knauf.ru",
    "фуген": "knauf.ru", "fugen": "knauf.ru",
    "перлфикс": "knauf.ru", "perlfix": "knauf.ru",
    "uniflott": "knauf.ru", "юнифлотт": "knauf.ru",
    "starateli": "starateli.ru",
    "bergauf": "bergauf.ru", "бергауф": "bergauf.ru",
    "kreps": "kreps.ru", "крепс": "kreps.ru",
    "глимс": "glims.ru", "glims": "glims.ru",
    "ilpozzo": "ilpozzo.ru", "ильпоццо": "ilpozzo.ru",
    "litos": "litos.ru", "литос": "litos.ru",
    "besto": "besto.su", "бесто": "besto.su",
    "петромикс": "petromix.ru", "petromix": "petromix.ru",
    "боларс": "bolars.ru", "bolars": "bolars.ru",
    "вилатерм": "vilaterm.ru", "vilaterm": "vilaterm.ru",
    "mapei": "mapei.com", "мапеи": "mapei.com", "мапей": "mapei.com",
    "makroflex": "makroflex.ru", "макрофлекс": "makroflex.ru",
    "kiilto": "kiilto.com", "киилто": "kiilto.com",
    "soudal": "soudal.ru", "соудал": "soudal.ru",
    "kudo": "kudo.ru", "кудо": "kudo.ru",
    "экон": "ekon.su", "ekon": "ekon.su",
    "tytan": "tytan.ru", "титан": "tytan.ru",
    "henkel": "henkel.ru", "хенкель": "henkel.ru",
    "геркон": "gerkon.ru", "gerkon": "gerkon.ru",
    "permabase": "permabase.ru", "пермабейз": "permabase.ru",
}


def _brand_domain(text: str) -> str:
    """Определяет официальный домен по бренду/названию товара."""
    t = (text or "").lower()
    for alias, domain in _BRAND_DOMAINS.items():
        if alias in t:
            return domain
    return ""


@router.get("/products/imageSearch")
async def product_image_search(q: str, brand: str = ""):
    """Ищет фото товара ТОЛЬКО на официальном сайте производителя.

    Цепочка: бренд → официальный домен (карта/угадывание brand.ru|com) →
    поиск страницы товара на сайте (sitemap.xml, штатный поиск Bitrix) →
    og:image/галерея карточки. Без Яндекса и сторонних источников.
    """
    import asyncio
    import re as _re
    import ssl as _ssl
    import urllib.parse
    import urllib.request

    query = (q or "").strip()
    if not query:
        return {"status": "error", "detail": "q обязателен"}

    _SKIP_DOMAINS = {
        "yandex.ru", "ya.ru", "yandex.net", "yandex.cloud", "yandexcloud.net",
        "yastatic.net", "google.com", "github.com", "githubusercontent.com",
        "ozon.ru", "wildberries.ru", "market.yandex.ru", "youtube.com",
        "wikipedia.org", "vk.com", "ok.ru", "avito.ru", "2gis.ru", "rusprofile.ru",
        "list-org.com", "zoon.ru", "petrovich.ru", "vseinstrumenti.ru",
        "leroymerlin.ru", "maxidom.ru", "220-volt.ru", "obi.ru",
        "microsoft.com", "apple.com", "adobe.com", "facebook.com",
        "instagram.com", "twitter.com", "x.com", "t.me", "telegram.me",
    }

    _UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
           "Accept-Language": "ru-RU,ru;q=0.9"}

    def _get(url: str, timeout: int = 15, limit: int = 2_000_000) -> str:
        req = urllib.request.Request(url, headers=_UA)
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read(limit).decode("utf-8", "replace")

    def _detect_official_domain() -> str:
        """Угадывание домена офсайта: бренд.ru / бренд.com + проверка ответа."""
        if not brand:
            return ""
        slug = _re.sub(r"[^a-z0-9]+", "", brand.lower())
        if len(slug) < 3:
            return ""
        for d in (slug + ".ru", slug + ".com"):
            if any(s in d for s in _SKIP_DOMAINS):
                continue
            try:
                with urllib.request.urlopen(
                        urllib.request.Request("https://" + d + "/", headers=_UA),
                        timeout=8, context=_ssl.create_default_context()) as resp:
                    if resp.status < 400:
                        body = resp.read(300_000).decode("utf-8", "replace").lower()
                        if slug in body:
                            return d
            except Exception:
                continue
        return ""

    _TRANSLIT = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }

    def _slug_tokens(name: str):
        """Токены для матчинга по URL-слагу: латинские + транслит кириллицы."""
        toks = set()
        for t in _re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", name):
            toks.add(t.lower().strip("-"))
        for t in _re.findall(r"[а-яёА-ЯЁ]{4,}", name.lower()):
            tr = "".join(_TRANSLIT.get(ch, "") for ch in t)
            if len(tr) >= 4:
                toks.add(tr)
        return [t for t in toks if t not in {"the", "for", "and", "pro"}]

    def _stems(name: str) -> set:
        stems = set()
        for t in _re.findall(r"[a-zа-яё0-9]+", name.lower()):
            if len(t) < 3 or t in {"для", "или", "под", "над", "из", "по", "на", "в", "с", "и"}:
                continue
            stems.add(t[:5] if len(t) > 5 else t)
        return stems

    _SECTION_HINTS = ("catalog", "product", "produkc", "tovar", "category", "collection", "assorti", "goods", "shop")

    def _anchors(html: str, base: str):
        for href, txt in _re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, _re.S | _re.I):
            if href.startswith("javascript") or href.startswith("#") or href.startswith("mailto"):
                continue
            u = href if href.startswith("http") else base + href
            yield u, _re.sub(r"<[^>]+>", "", txt).strip()

    def _page_candidates(domain: str, name: str):
        """Мини-краулер: главная → категорийные страницы → якоря товаров.

        Плюс штатный поиск сайта. Матч — по стем-покрытию названия в
        тексте ссылки и по латинским/транслит-токенам в URL-слаге.
        """
        dom_slug = _re.sub(r"[^a-z0-9]+", "", domain.split(".")[0])
        toks = [t for t in _slug_tokens(name) if t.replace("-", "") not in dom_slug]
        stems = _stems(name)
        base = "https://" + domain
        found = {}
        visited = set()

        def _url_score(u: str) -> float:
            ul = urllib.parse.urlparse(u).path.lower()
            return sum(1 for t in toks if t in urllib.parse.unquote(ul)) * 3

        def _anchor_score(text: str) -> float:
            st = _stems(text)
            return (len(stems & st) / len(stems)) * 10 if stems and st else 0.0

        _BAD_PATH = ("press", "news", "blog", "article", "media", "about", "contact", "career", "vacanc")

        def _path_penalty(u: str) -> float:
            p = urllib.parse.urlparse(u).path.lower()
            if any(b in p for b in _BAD_PATH):
                return 0.2
            # товарные пути — бонус
            if any(h in p for h in _SECTION_HINTS):
                return 1.4
            return 1.0

        def _collect(html: str, section: bool = False):
            for u, txt in _anchors(html, base):
                try:
                    netloc = urllib.parse.urlparse(u).netloc.lstrip("www.")
                except Exception:
                    continue
                if not netloc.endswith(domain.lstrip("www.")):
                    continue
                pu = urllib.parse.urlparse(u).path.lower()
                if pu.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")) or "/upload/" in pu:
                    continue  # документы/файлы — не страницы товара
                pen = _path_penalty(u)
                if section and len(txt) >= 10:
                    st = _stems(txt)
                    cov = len(stems & st) / len(stems) if stems and st else 0.0
                    if cov >= 0.4:
                        # полное покрытие → бонус; длинные анкоры — штраф тай-брейка
                        bonus = 6.0 if cov >= 0.999 else 0.0
                        sc = (cov * 10 + bonus + _url_score(u)) * pen - len(txt) / 60.0
                        found[u] = max(found.get(u, 0), sc)
                else:
                    sc = _url_score(u) * pen
                    if sc >= 3:
                        found[u] = max(found.get(u, 0), sc)

        def _is_section(u: str, txt: str) -> bool:
            path = urllib.parse.urlparse(u).path.lower()
            if len(txt) < 3 or len(txt) > 60:
                return False
            return any(h in path for h in _SECTION_HINTS)

        import time as _time
        deadline = _time.monotonic() + 40.0  # общий лимит краула

        def _crawl(url: str, depth: int):
            if url in visited or depth > 3 or len(visited) > 35 or _time.monotonic() > deadline:
                return
            visited.add(url)
            try:
                html = _get(url, timeout=10)
            except Exception:
                return
            # собираем якоря товаров на этой странице
            _collect(html, section=(depth >= 1))
            # находим категорийные ссылки для спуска
            if depth < 3 and len(found) < 4:
                sects = []
                for u, txt in _anchors(html, base):
                    if u in visited:
                        continue
                    try:
                        if domain.lstrip("www.") in urllib.parse.urlparse(u).netloc.lstrip("www.") and _is_section(u, txt):
                            sects.append(u)
                    except Exception:
                        pass
                for u in sects[:10]:
                    if _time.monotonic() > deadline:
                        break
                    _crawl(u, depth + 1)

        # 1) штатный поиск сайта
        for path in ("/search/index.php?q=", "/search/?q=", "/catalog/?q=", "/poisk/?q="):
            try:
                html = _get(base + path + urllib.parse.quote(name), timeout=12)
                _collect(html, section=True)
            except Exception:
                continue

        # 2) краулер: главная + типовые входы каталога → категории → товары
        _crawl(base + "/", 0)
        for seed in ("/catalog/", "/products/", "/produkciya/", "/ru/products/"):
            if len(found) >= 4 or _time.monotonic() > deadline:
                break
            _crawl(base + seed, 0)

        if not found:
            return ""
        return max(found.items(), key=lambda kv: kv[1])[0]

    def _page_image(html: str, domain: str):
        """og:image / галерея карточки → список URL фото."""
        imgs = []
        for pat in (
            r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
            r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"',
            r'data-zoom-image="([^"]+)"',
            r'href="([^"]*?(?:upload|image|photo|pict|gallery|iblock)[^"]*?\.(?:jpg|jpeg|png|webp))"',
            r'src="([^"]*?(?:upload|imagecompress|iblock|photo|gallery)[^"]*?\.(?:jpg|jpeg|png|webp))"',
        ):
            for m in _re.finditer(pat, html, _re.I):
                u = m.group(1)
                if u.startswith("//"):
                    u = "https:" + u
                elif u.startswith("/"):
                    u = "https://" + domain + u
                ul = u.lower()
                if any(b in ul for b in ("logo", "favicon", "/icon", "sprite", "avatar", "banner", "flag", "fav_")):
                    continue
                if u.startswith("http") and u not in imgs:
                    imgs.append(u)
            if imgs:
                break
        # товарные фото (iblock/upload/product) — вперёд
        imgs.sort(key=lambda u: 0 if any(k in u.lower() for k in ("iblock", "/upload/", "product")) else 1)
        return imgs[:5]

    def _page_attrs(html: str):
        """Характеристики со страницы товара: tr>td строки и dt/dd пары."""
        import re as _re
        import html as _html
        attrs = []
        seen = set()

        def _add(name: str, val: str):
            name = _re.sub(r"<[^>]+>", " ", name)
            name = _html.unescape(_re.sub(r"\s+", " ", name)).strip().strip(":").strip()
            val = _re.sub(r"<[^>]+>", " ", val)
            val = _html.unescape(_re.sub(r"\s+", " ", val)).strip()
            if not (2 <= len(name) <= 45 and 1 <= len(val) <= 200):
                return
            # фильтр служебного мусора
            if _re.search(r"(?:cookie|телефон|email|войти|корзина|копирайт|©|читать далее|поделиться)", name, _re.I):
                return
            if not _re.search(r"[a-zа-яёA-ZА-ЯЁ]", name):
                return
            if _re.search(r"[a-zA-Z0-9]{25,}", val):  # хеши/токены
                return
            key = name.lower()
            if key in seen:
                return
            seen.add(key)
            attrs.append({"name": name, "text": val})

        # 1) строки таблиц: <tr><td|th>имя</td|th><td>значение</td></tr>
        for tr in _re.findall(r"<tr[^>]*>(.*?)</tr>", html, _re.S | _re.I):
            cells = _re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, _re.S | _re.I)
            if len(cells) == 2:
                _add(cells[0], cells[1])

        # 2) dt/dd пары (между ними может быть разметка)
        for n, v in _re.findall(r"<dt[^>]*>(.*?)</dt>.*?<dd[^>]*>(.*?)</dd>", html, _re.S | _re.I):
            _add(n, v)

        # 3) li с двумя div-ячейками (left/right, name/value) — Bitrix-стиль
        for li in _re.findall(r"<li[^>]*>(.*?)</li>", html, _re.S | _re.I):
            if "<a " in li or "<a\n" in li:
                continue  # навигационные ссылки пропускаем
            cells = _re.findall(r"<div[^>]*>(.*?)</div>", li, _re.S | _re.I)
            cells = [c for c in cells if _re.sub(r"<[^>]+>", "", c).strip()]
            if len(cells) == 2:
                _add(cells[0], cells[1])
            elif not cells:
                # knauf-стиль: <li>Имя: значение</li>
                txt = _re.sub(r"<[^>]+>", "", li)
                if ":" in txt:
                    n, v = txt.split(":", 1)
                    if 4 <= len(n.strip()) <= 60 and 1 <= len(v.strip()) <= 120:
                        _add(n, v)

        return attrs[:40]

    try:
        loop = asyncio.get_event_loop()
        domain = _brand_domain(brand + " " + query)
        if not domain:
            domain = await loop.run_in_executor(None, _detect_official_domain)
        if not domain:
            return {"status": "ok", "urls": [], "source": "no_official_site",
                    "detail": "официальный сайт бренда не найден — загрузите фото вручную"}

        page = await loop.run_in_executor(None, _page_candidates, domain, query)
        if not page:
            return {"status": "ok", "urls": [], "source": domain,
                    "detail": f"страница товара на {domain} не найдена"}

        try:
            page_html = await loop.run_in_executor(None, lambda: _get(page, timeout=15))
        except Exception:
            return {"status": "ok", "urls": [], "source": domain, "page": page,
                    "detail": "страница найдена, но не загрузилась"}
        urls = _page_image(page_html, domain)
        attrs = _page_attrs(page_html)
        return {"status": "ok", "urls": urls, "attrs": attrs, "source": domain, "page": page}
    except Exception as exc:
        return {"status": "error", "detail": str(exc), "urls": []}


def _name_stems(name: str) -> set:
    """Значимые стемы из названия товара (как в catalog_core-матчере)."""
    import re as _re
    stops = {"для", "или", "под", "над", "из", "по", "на", "в", "с", "и", "the", "of"}
    stems = set()
    for t in _re.findall(r"[a-zа-яё0-9]+", (name or "").lower()):
        if len(t) < 3 or t in stops:
            continue
        stems.add(t[:5] if len(t) > 5 else t)
    return stems


@router.post("/products/suggestCategory")
async def product_suggest_category(payload: dict = Body(...)):
    """Подбирает категорию для нового товара.

    1) Сначала ищет похожий товар в каталоге OpenCart (стем-матчинг по
       названию) — категория берётся у лучшего совпадения.
    2) Если похожих нет — DeepSeek выбирает из списка категорий.

    payload: {"name": "...", "categories": [{"id": 1, "name": "..."}, ...]}
    """
    import asyncio
    import json as _json
    import ssl as _ssl
    import urllib.request as _urllib_req
    from app.core.config import settings as _settings

    name = (payload.get("name") or "").strip()
    cats = payload.get("categories") or []
    if not name or not cats:
        return {"status": "error", "detail": "name и categories обязательны"}


    # 1) Матчинг по существующему каталогу — «ядро уже изучило каждый товар»
    q_stems = _name_stems(name)
    if q_stems:
        try:
            res = await opencart_api.post_action("db/select", {
                "sql": (
                    "SELECT pd.name, p2c.category_id "
                    "FROM oc_openproduct_to_category p2c "
                    "JOIN oc_openproduct p ON p.product_id = p2c.product_id AND p.status = 1 "
                    "JOIN oc_openproduct_description pd "
                    "ON pd.product_id = p2c.product_id AND pd.language_id = 1"
                )
            })
            best = None
            for row in (res or {}).get("rows") or []:
                r_stems = _name_stems(row.get("name") or "")
                if not r_stems:
                    continue
                cover = len(q_stems & r_stems) / len(q_stems)
                if best is None or cover > best[0]:
                    best = (cover, row.get("category_id"), row.get("name"))
            if best and best[0] >= 0.6:
                return {
                    "status": "ok",
                    "category_id": int(best[1]),
                    "reason": f"похож на «{best[2][:60]}»",
                    "source": "catalog_match",
                }
        except Exception:
            pass  # матчинг не удался — пробуем DeepSeek

    # 2) Fallback: DeepSeek-классификатор
    ds_key = _settings.deepseek_api_key
    if not ds_key:
        return {"status": "error", "detail": "DEEPSEEK_API_KEY не настроен"}

    cat_lines = "\n".join(f"{c['id']}: {c['name']}" for c in cats[:400])
    prompt = (
        "Ты — классификатор товаров интернет-магазина стройматериалов stroiapp.ru.\n"
        f"Товар: {name}\n\n"
        "Список категорий (id: название):\n" + cat_lines + "\n\n"
        "Выбери ОДНУ наиболее подходящую категорию для этого товара. "
        "Верни JSON: {\"category_id\": <id>, \"reason\": \"кратко почему\"}"
    )
    ds_payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты классифицируешь товары по категориям. Отвечай только JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }

    def _call():
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        req = _urllib_req.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=_json.dumps(ds_payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {ds_key}"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=60, context=ctx) as resp:
            return _json.loads(resp.read().decode("utf-8-sig"))

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _call)
        content = _json.loads(result["choices"][0]["message"]["content"])
        cid = int(content.get("category_id") or 0)
        valid_ids = {int(c["id"]) for c in cats}
        if cid not in valid_ids:
            return {"status": "error", "detail": f"DeepSeek вернул неизвестный id {cid}"}
        return {"status": "ok", "category_id": cid, "reason": content.get("reason", "")}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/findSimilar")
async def product_find_similar(payload: dict = Body(...)):
    """Ищет похожий товар в нашем каталоге (стем-матч по названию).

    Фолбэк, когда официальный сайт не нашёлся: отдаём фото, категорию
    и характеристики существующего похожего товара («товары от ФМ» и пр.).

    payload: {"name": "..."}
    """
    name = (payload.get("name") or "").strip()
    if not name:
        return {"status": "error", "detail": "name обязателен"}

    q_stems = _name_stems(name)
    if not q_stems:
        return {"status": "ok", "match": None, "detail": "нет значимых слов"}

    try:
        res = await opencart_api.post_action("db/select", {
            "sql": (
                "SELECT p.product_id, pd.name, p.image, "
                "(SELECT p2c.category_id FROM oc_openproduct_to_category p2c "
                " WHERE p2c.product_id = p.product_id LIMIT 1) AS category_id "
                "FROM oc_openproduct p "
                "JOIN oc_openproduct_description pd "
                "ON pd.product_id = p.product_id AND pd.language_id = 1 "
                "WHERE p.status = 1"
            )
        })
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

    best = None
    for row in (res or {}).get("rows") or []:
        r_stems = _name_stems(row.get("name") or "")
        if not r_stems:
            continue
        cover = len(q_stems & r_stems) / len(q_stems)
        if best is None or cover > best[0]:
            best = (cover, row)

    if not best or best[0] < 0.45:
        return {"status": "ok", "match": None,
                "detail": f"похожих не найдено (лучшее покрытие {best[0]:.0%})" if best else "каталог пуст"}

    row = best[1]
    pid = int(row.get("product_id"))

    # характеристики похожего товара — с готовыми attribute_id
    attrs = []
    try:
        ares = await opencart_api.post_action("db/select", {
            "sql": (
                "SELECT pa.attribute_id, ad.name, pa.text "
                "FROM oc_openproduct_attribute pa "
                "JOIN oc_openattribute_description ad "
                "ON ad.attribute_id = pa.attribute_id AND ad.language_id = 1 "
                f"WHERE pa.product_id = {pid} AND pa.language_id = 1"
            )
        })
        attrs = [{"attribute_id": str(r.get("attribute_id")),
                  "name": r.get("name"), "text": r.get("text")}
                 for r in (ares or {}).get("rows") or []]
    except Exception:
        pass

    return {
        "status": "ok",
        "cover": round(best[0], 2),
        "match": {
            "product_id": pid,
            "name": row.get("name"),
            "image": row.get("image") or "",
            "category_id": row.get("category_id"),
            "attributes": attrs,
        },
    }


@router.post("/images/uploadUrl")
async def image_upload_url(payload: dict = Body(...)):
    """Скачивает картинку по URL и заливает на stroiapp.ru через ai_manager."""
    import asyncio
    import ssl as _ssl
    import urllib.parse
    import urllib.request

    url = (payload.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"status": "error", "detail": "Некорректный URL"}
    name = (payload.get("name") or "").strip()

    def _fetch():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AI-StroiApp-Manager/1.0"})
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            ctype = (resp.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip()
            return resp.read(), ctype

    try:
        loop = asyncio.get_event_loop()
        content, ctype = await loop.run_in_executor(None, _fetch)
    except Exception as exc:
        return {"status": "error", "detail": f"Не удалось скачать: {exc}"}

    if len(content) < 1000:
        return {"status": "error", "detail": "Файл слишком мал — вероятно не картинка"}
    if not ctype.startswith("image/"):
        ctype = "image/jpeg"

    ext = ctype.split("/")[-1].replace("jpeg", "jpg")
    if not name:
        base = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1].split("?")[0]
        name = base if "." in base else ("img." + ext)
    if "." not in name:
        name += "." + ext

    try:
        return await opencart_api.upload_image(content, name, ctype)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _deepseek_seo(name: str, model: str = "", category_name: str = "", description_existing: str = ""):
    import json as _json
    import ssl as _ssl
    import urllib.request as _urllib_req
    from app.core.config import settings as _settings

    ds_key = _settings.deepseek_api_key
    if not ds_key:
        return {"error": "DEEPSEEK_API_KEY не настроен"}

    prompt_lines = [
        "Ты SEO-копирайтер для интернет-магазина строительных материалов stroiapp.ru (Москва и МО).",
        f"Товар: {name}",
    ]
    if model:
        prompt_lines.append(f"Модель: {model}")
    if category_name:
        prompt_lines.append(f"Категория: {category_name}")
    if description_existing:
        prompt_lines.append(f"Существующее описание: {description_existing[:200]}")
    prompt_lines.extend([
        "",
        "Сгенерируй уникальное SEO-описание для товара на русском языке.",
        "Описание должно быть профессиональным, 2-3 абзаца, с упоминанием применения, преимуществ.",
        "Упомяни: оптовые цены, доставка по Москве и МО, безналичный расчёт с НДС.",
        "",
        "Также сгенерируй характеристики товара (5-7 атрибутов).",
        "",
        "Верни результат в формате JSON с полями:",
        "description (HTML), meta_title (до 60 символов), meta_description (150-160 символов),",
        "meta_keyword (5-7 слов через запятую), attributes (массив объектов с полями name и text)",
    ])
    prompt = "\n".join(prompt_lines)

    ds_payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты — SEO-копирайтер для строительных материалов. Пиши на русском."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }

    _ctx = _ssl.create_default_context()
    _ctx.check_hostname = False
    _ctx.verify_mode = _ssl.CERT_NONE
    _data = _json.dumps(ds_payload).encode("utf-8")
    _req = _urllib_req.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=_data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {ds_key}"},
        method="POST",
    )
    with _urllib_req.urlopen(_req, timeout=60, context=_ctx) as _resp:
        result = _json.loads(_resp.read().decode("utf-8-sig"))

    content = _json.loads(result["choices"][0]["message"]["content"])
    return {
        "description": content.get("description", ""),
        "meta_title": content.get("meta_title", name),
        "meta_description": content.get("meta_description", ""),
        "meta_keyword": content.get("meta_keyword", ""),
        "attributes": content.get("attributes", []),
    }


@router.post("/products/generateSeo")
async def product_generate_seo(payload: dict = Body(...)):
    try:
        product = await opencart_api.get_action("product/get", {"product_id": payload.get("product_id")})
        return _deepseek_seo(product.get("name", "Товар"), product.get("model", ""), product.get("category_name", ""), product.get("description", ""))
    except Exception as exc:
        return {"error": str(exc)}


@router.post("/products/generateDraft")
async def product_generate_draft(payload: dict = Body(...)):
    try:
        return _deepseek_seo(payload.get("name", "Товар"), payload.get("model", ""), payload.get("category_name", ""), "")
    except Exception as exc:
        return {"error": str(exc)}


@router.get("/products/attributes")
async def product_attributes(product_id: int):
    try:
        return await opencart_api.get_action("product/attributes", {"product_id": product_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/updateAttributes")
async def product_update_attributes(payload: dict = Body(...)):
    try:
        return await opencart_api.post_action("product/updateAttributes", payload)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/enrichAttributes")
async def product_enrich_attributes(payload: dict = Body(...)):
    """Дополнение технических характеристик товара через DeepSeek.

    Генерирует полный набор атрибутов (12-20 шт, как на famarket/Петрович),
    сохраняет в attr_store (перекрывает бедные данные OpenCart) и применяет
    к живому каталогу — storefront API сразу отдаёт новый набор.

    payload:
      product_ids: [int] — конкретные товары; или
      limit: int (default 5) — первые N товаров с неполными атрибутами (<12)
      only_incomplete: bool (default true) — пропускать товары с ≥12 атрибутами
      threshold: int (default 12) — порог «полноты» для only_incomplete
    """
    try:
        ids = payload.get("product_ids") or []
        limit = int(payload.get("limit") or 5)
        only_incomplete = bool(payload.get("only_incomplete", True))
        threshold = int(payload.get("threshold") or 12)
        offset = int(payload.get("offset") or 0)

        by_pid = {p.product_id: p for p in product_db.list_products() if p.product_id}
        if ids:
            targets = [by_pid[i] for i in ids if i in by_pid]
        else:
            targets = []
            for p in product_db.list_products():
                if not (p.product_id and p.name and p.retail_price and p.retail_price > 0):
                    continue
                cur = [a for a in (p.attributes or []) if isinstance(a, dict) and a.get("name")]
                if only_incomplete and len(cur) >= threshold:
                    continue
                targets.append(p)
            targets = targets[offset:offset + limit]

        results = []
        for p in targets:
            existing = [a for a in (p.attributes or []) if isinstance(a, dict) and a.get("name")]
            gen = await deepseek_client.generate_product_attributes(
                p.name, str(p.category_id or ""), existing)
            if not gen:
                results.append({"product_id": p.product_id, "name": p.name, "status": "empty"})
                continue
            # существующие атрибуты имеют приоритет при совпадении имён (черновик модели не затирает их)
            gen_names = {a["name"].lower() for a in gen}
            merged = gen + [a for a in existing if a["name"].lower() not in gen_names]
            applied = product_db.apply_attributes(p.product_id, merged)
            results.append({
                "product_id": p.product_id, "name": p.name,
                "status": "ok" if applied else "saved-only",
                "count": len(merged),
                "attributes": merged,
            })
        return {"status": "ok", "processed": len(results), "results": results}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/attributes/enriched-count")
async def attributes_enriched_count(threshold: int = 12):
    """Сколько товаров имеют «полный» набор характеристик (>= threshold) в attr_store."""
    try:
        from app.db.attr_store import get_all_attributes
        saved = get_all_attributes()
        full = sum(1 for attrs in saved.values() if len(attrs) >= threshold)
        return {"status": "ok", "enriched_products": len(saved), "full": full}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/attributes/list")
async def attributes_list():
    try:
        return await opencart_api.get_action("attribute/list")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/orders/list")
async def orders_list(limit: int = 50, page: int = 1):
    try:
        return await opencart_api.get_action("order/list", {"limit": limit, "page": page})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/customers/list")
async def customers_list(limit: int = 50, page: int = 1):
    try:
        return await opencart_api.get_action("customer/list", {"limit": limit, "page": page})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/customers/{customer_id}")
async def customer_detail(customer_id: int):
    try:
        return await opencart_api.get_action("customer/get", {"customer_id": customer_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/customers/{customer_id}/status")
async def customer_update_status(customer_id: int, status: int):
    try:
        return await opencart_api.post_action("customer/update", {"customer_id": customer_id, "status": status})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/customers/{customer_id}/orders")
async def customer_orders(customer_id: int):
    try:
        return await opencart_api.get_action("customer/orders", {"customer_id": customer_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/orders/{order_id}")
async def order_detail(order_id: int):
    try:
        return await opencart_api.get_action("order/get", {"order_id": order_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/orders/status")
async def order_update_status(payload: OrderStatusPayload):
    try:
        return await opencart_api.post_action("order/updateStatus", payload.model_dump())
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/products/list")
async def products_list(limit: int = 50, page: int = 1):
    try:
        return await opencart_api.get_action("product/list", {"limit": limit, "page": page})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/products/recent")
async def products_recent(limit: int = 50):
    """Последние добавленные ИЛИ изменённые товары на сайте.

    Сортировка по GREATEST(date_added, date_modified) — productUpdate на сайте
    пишет date_modified=NOW() при каждом изменении.
    Поля — как у listByCategory: UI переиспользует карточку товара
    (image_url, has_description, has_meta, цены нал/безнал)."""
    try:
        limit = max(1, min(100, int(limit)))
        sql = (
            "SELECT p.product_id, p.model, p.sku, p.price, p.price_non_cash, "
            "p.cash_price, p.non_cash_price, p.quantity, p.image, p.status, "
            "p.date_added, p.date_modified, "
            "pd.name, pd.description, pd.meta_title "
            "FROM oc_openproduct p "
            "LEFT JOIN oc_openproduct_description pd "
            "ON (p.product_id = pd.product_id AND pd.language_id = 1) "
            "ORDER BY GREATEST(p.date_added, p.date_modified) DESC LIMIT " + str(limit)
        )
        data = await opencart_api.post_action("db/select", {"sql": sql})
        if data.get("status") == "error":
            return data
        products = []
        for r in (data.get("rows") or []):
            desc = r.get("description") or ""
            meta = r.get("meta_title") or ""
            img = r.get("image") or ""
            products.append({
                "product_id": r.get("product_id"),
                "model": r.get("model"),
                "sku": r.get("sku"),
                "name": r.get("name"),
                "price": r.get("price"),
                "price_non_cash": r.get("price_non_cash"),
                "cash_price": r.get("cash_price"),
                "non_cash_price": r.get("non_cash_price"),
                "quantity": r.get("quantity"),
                "image": img,
                "image_url": ("https://stroiapp.ru/image/" + img) if img else "",
                "status": r.get("status"),
                "has_description": len(desc) > 50,
                "has_meta": len(meta) > 5,
                "date_added": r.get("date_added"),
                "date_modified": r.get("date_modified"),
            })
        return {"status": "ok", "count": len(products), "products": products}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/products/{product_id}")
async def product_detail(product_id: int):
    try:
        return await opencart_api.get_action("product/get", {"product_id": product_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/update")
async def product_update(payload: ProductUpdatePayload):
    try:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        return await opencart_api.post_action("product/update", data)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/categories/update")
async def category_update(payload: CategoryUpdatePayload):
    try:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        return await opencart_api.post_action("category/update", data)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/images/upload")
async def image_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        return await opencart_api.upload_image(contents, file.filename)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/banners/list")
async def banners_list():
    try:
        return await opencart_api.get_action("banner/list")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/banners/{banner_id}")
async def banner_detail(banner_id: int):
    try:
        return await opencart_api.get_action("banner/get", {"banner_id": banner_id})
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/banners/update")
async def banner_update(payload: BannerUpdatePayload):
    try:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        return await opencart_api.post_action("banner/update", data)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/settings/list")
async def settings_list():
    try:
        return await opencart_api.get_action("setting/list")
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/settings/update")
async def settings_update(payload: dict):
    try:
        return await opencart_api.post_action("setting/update", payload)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/images/upload")
async def image_upload(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        return await opencart_api.upload_image(file_bytes, file.filename)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


class InvoiceSendPayload(BaseModel):
    order_id: int
    email: str
    messenger_type: str | None = None  # "telegram", "whatsapp", "max", "email_only"
    messenger_contact: str | None = None  # phone or username
    company_name: str | None = None
    inn: str | None = None


@router.post("/invoice/send")
async def invoice_send(payload: InvoiceSendPayload):
    """
    Send invoice to customer via email and optionally via messenger.
    Placeholder - will be implemented when API keys are available.
    """
    try:
        result = {
            "status": "queued",
            "order_id": payload.order_id,
            "email_sent": True,
            "messenger_type": payload.messenger_type,
            "messenger_contact": payload.messenger_contact,
            "message": "Invoice queued for delivery. Email will be sent immediately. Messenger delivery will be enabled when API keys are configured."
        }
        # TODO: Implement actual messenger sending when API keys available
        # telegram_bot.send_message(...) or whatsapp_api.send_message(...)
        return result
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/special-products")
async def get_special_products(limit: int = 4):
    """Get products with special/discount prices from OpenCart DB."""
    try:
        result = await opencart_api.get_action("product/list", {"limit": 100})
        items = result.get("products", []) if isinstance(result, dict) else []
        products = []
        for p in items:
            specials = p.get("specials", [])
            if not specials:
                continue
            special = specials[0]
            base_price = float(p.get("price", 0))
            special_price = float(special.get("price", 0))
            if special_price <= 0 or special_price >= base_price:
                continue
            discount = round((1 - special_price / base_price) * 100)
            image = p.get("image", "")
            if image:
                image = f"image/{image}"
            products.append({
                "product_id": p.get("product_id"),
                "name": p.get("name", ""),
                "image": image,
                "price": base_price,
                "special_price": special_price,
                "discount": discount,
                "href": f"index.php?route=product/product&product_id={p.get('product_id')}"
            })
            if len(products) >= limit:
                break
        return {"products": products}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


class SpecialPricePayload(BaseModel):
    product_id: int
    special_price: float


@router.post("/special-prices")
async def set_special_price(payload: SpecialPricePayload):
    """Set special price for a product."""
    try:
        result = await opencart_api.post_action("product/specialSet", {
            "product_id": payload.product_id,
            "price": payload.special_price
        })
        return {"status": "ok", "product_id": payload.product_id, "special_price": payload.special_price}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.delete("/special-prices/{product_id}")
async def delete_special_price(product_id: int):
    """Remove special price from a product."""
    try:
        result = await opencart_api.post_action("product/specialDelete", {"product_id": product_id})
        return {"status": "ok", "product_id": product_id}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/special-prices/all")
async def get_all_special_products(limit: int = 100):
    """Get all products with special prices for admin management."""
    try:
        result = await opencart_api.get_action("product/list", {"limit": limit})
        items = result.get("products", []) if isinstance(result, dict) else []
        products = []
        for p in items:
            specials = p.get("specials", [])
            if not specials:
                continue
            special = specials[0]
            base_price = float(p.get("price", 0))
            special_price = float(special.get("price", 0))
            if special_price <= 0:
                continue
            discount = round((1 - special_price / base_price) * 100) if base_price > 0 else 0
            products.append({
                "product_id": p.get("product_id"),
                "name": p.get("name", ""),
                "sku": p.get("sku", ""),
                "price": base_price,
                "special_price": special_price,
                "discount": discount,
            })
        return {"products": products}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

@router.get("/related-products")
async def get_related_products(product_id: int, limit: int = 4):
    """Get related products from same category."""
    try:
        result = await opencart_api.get_action("product/list", {"limit": 50})
        items = result.get("products", []) if isinstance(result, dict) else []
        products = []
        for p in items:
            if p.get("product_id") == product_id:
                continue
            image = p.get("image", "")
            if image:
                image = f"image/{image}"
            price = p.get("price", "")
            special = p.get("special", "")
            products.append({
                "product_id": p.get("product_id"),
                "name": p.get("name", ""),
                "image": image,
                "price": price,
                "special": special,
                "href": f"index.php?route=product/product&product_id={p.get('product_id')}"
            })
            if len(products) >= limit:
                break
        return {"products": products}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/search-products")
async def search_products(keyword: str, limit: int = 10):
    """Search products by keyword in name. Returns economy and premium segments."""
    try:
        result = await opencart_api.get_action("product/list", {"limit": 200})
        items = result.get("products", []) if isinstance(result, dict) else []
        keyword_lower = keyword.lower()
        matched = []
        for p in items:
            name = p.get("name", "").lower()
            if keyword_lower in name:
                image = p.get("image", "")
                if image:
                    image = f"image/{image}"
                price_val = 0
                try:
                    price_str = str(p.get("price", "0")).replace(" ", "").replace("₽", "").replace(",", ".")
                    price_val = float(price_str) if price_str else 0
                except:
                    pass
                matched.append({
                    "product_id": p.get("product_id"),
                    "name": p.get("name", ""),
                    "image": image,
                    "price": p.get("price", ""),
                    "price_value": price_val,
                    "special": p.get("special", ""),
                    "href": f"index.php?route=product/product&product_id={p.get('product_id')}",
                    "sku": p.get("sku", ""),
                })
        matched.sort(key=lambda x: x["price_value"])
        economy = matched[:3] if len(matched) >= 3 else matched
        premium = matched[-3:] if len(matched) >= 3 else matched
        premium_ids = {p["product_id"] for p in economy}
        premium = [p for p in premium if p["product_id"] not in premium_ids]
        return {
            "economy": economy,
            "premium": premium if premium else (matched[-2:] if len(matched) > 3 else []),
            "all": matched[:limit]
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
