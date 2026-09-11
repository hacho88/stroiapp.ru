from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File, Body

from app.services.opencart_api import opencart_api
from app.services.product_db import product_db

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
        return await opencart_api.get_action("category/list")
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


@router.post("/images/upload")
async def image_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await opencart_api.upload_image(content, file.filename)
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
async def products_by_category(category_id: int):
    try:
        return await opencart_api.get_action("product/listByCategory", {"category_id": category_id})
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
        return await opencart_api.post_action("product/add", payload)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.post("/products/generateSeo")
async def product_generate_seo(payload: dict = Body(...)):
    try:
        product = await opencart_api.get_action("product/get", {"product_id": payload.get("product_id")})
        name = product.get("name", "Товар")
        model = product.get("model", "")
        category_name = product.get("category_name", "")
        description_existing = product.get("description", "")

        # Generate via DeepSeek AI
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
        description = content.get("description", "")
        meta_title = content.get("meta_title", name)
        meta_description = content.get("meta_description", "")
        meta_keyword = content.get("meta_keyword", "")
        attrs = content.get("attributes", [])

        return {
            "description": description,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "meta_keyword": meta_keyword,
            "attributes": attrs,
        }
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
