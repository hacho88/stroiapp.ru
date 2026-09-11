import csv
import io
import re

from fastapi import APIRouter, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse
from typing import Optional

from app.models.product import ProductPriceInput, ProductCreate, ProductUpdate
from app.services.product_db import product_db
from app.services.opencart_api import opencart_api
from app.services.deepseek_client import deepseek_client

router = APIRouter(prefix="/product", tags=["product"])


@router.get("/status")
def product_status():
    return {"status": "ok", "service": "product", "total": len(product_db.list_products())}


@router.get("/prices")
def product_prices(limit: int = 100):
    products = product_db.list_products()[:limit]
    return {"status": "ok", "count": len(products), "products": [{"sku": p.sku, "name": p.name, "retail_price": p.retail_price, "wholesale_price": p.wholesale_price} for p in products]}


@router.get("/list")
def list_products(
    search: str = "",
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_roi: float | None = None,
    sort_by: str = "name",
    limit: int = 500,
    offset: int = 0,
):
    """Список товаров с поиском, фильтрацией, сортировкой и пагинацией."""
    if not any([search, category_id is not None, min_price is not None, max_price is not None, min_roi is not None, sort_by != "name", limit != 500, offset != 0]):
        return product_db.list_products()
    return product_db.list_products_filtered(
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        min_roi=min_roi,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )


@router.get("/get/{sku}")
def get_product(sku: str):
    product = product_db.get_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/update")
def update_product_prices(payload: ProductPriceInput):
    return product_db.upsert_costs(
        payload.sku,
        payload.cost_price_cash,
        payload.cost_price_cashless,
        payload.retail_price,
        payload.wholesale_price,
    )


@router.post("/importFromDump")
def import_from_dump():
    return {"status": "imported", "count": product_db.reload_from_dump()}


@router.get("/exportCosts")
def export_costs():
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["sku", "name", "cost_price_cash", "cost_price_cashless", "retail_price", "wholesale_price", "roi"])
    for product in product_db.list_products():
        writer.writerow([
            product.sku,
            product.name,
            product.cost_price_cash,
            product.cost_price_cashless,
            product.retail_price,
            product.wholesale_price,
            product.roi,
        ])
    buffer.seek(0)
    content = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    return StreamingResponse(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=product_costs.csv"},
    )


@router.post("/importCosts")
async def import_costs(file: UploadFile):
    raw = await file.read()
    text = raw.decode("utf-8-sig")
    sample = text[:2048]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    result = product_db.bulk_upsert_costs(list(reader))
    return {"status": "imported", **result}


from app.core.config import settings


@router.post("/quickAdd")
async def quick_add_product(
    name: str = Form(...),
    sku: str = Form(""),
    file: UploadFile | None = None,
):
    """Быстрое добавление товара: только название + фото.
    AI сам генерирует описание, SEO, цены, категорию, модель."""
    import json

    # Генерируем SKU если не передан
    if not sku:
        existing = product_db.list_products()
        sku = f"AI{len(existing) + 1:05d}"

    if sku in {p.sku for p in product_db.list_products()}:
        raise HTTPException(status_code=409, detail=f"Товар {sku} уже существует")

    # Загрузка фото в OpenCart (если есть)
    image_path = ""
    if file and settings.opencart_api_url:
        try:
            raw = await file.read()
            img_result = await opencart_api.upload_image(raw, file.filename or f"{sku}.jpg")
            image_path = img_result.get("path") or img_result.get("image", "")
        except Exception:
            pass

    # AI генерирует ВСЁ — описание, SEO, цены, категорию, модель
    system = (
        "Ты — эксперт по строительным материалам и SEO-копирайтер магазина stroiapp.ru. "
        "По названию товара определяешь его характеристики, категорию, "
        "рыночную себестоимость, рекомендуешь розничную и оптовую цену. "
        "Пишешь продающее описание и SEO мета-теги. "
        "Отвечай ТОЛЬКО в формате JSON."
    )
    prompt = (
        f"Название товара: {name}\n\n"
        f"Определи и сгенерируй:\n"
        f"1. description — продающее описание (300-500 символов)\n"
        f"2. model — артикул/модель (если можно определить)\n"
        f"3. category_id — ID категории стройматериалов (1=цемент, 2=гипсокартон, "
        f"3=арматура, 4=утеплитель, 5=крепёж, 6=сухие смеси, 7=кровля, "
        f"8=сантехника, 9=электрика, 10=краска, 0=прочее)\n"
        f"4. cost_price_cash — примерная себестоимость наличный (₽)\n"
        f"5. cost_price_cashless — примерная себестоимость безнал (₽, +3-5%)\n"
        f"6. retail_price — розничная цена (наценка 30-45%)\n"
        f"7. wholesale_price — оптовая цена (наценка 10-20%)\n"
        f"8. meta_title — title для SEO (до 60 символов)\n"
        f"9. meta_description — meta description (до 160 символов)\n"
        f"10. meta_keyword — ключевые слова через запятую\n"
        f"11. quantity — рекомендованное начальное количество на складе\n\n"
        f"Формат JSON:\n"
        f'{{"description":"...","model":"...","category_id":0,'
        f'"cost_price_cash":0,"cost_price_cashless":0,'
        f'"retail_price":0,"wholesale_price":0,'
        f'"meta_title":"...","meta_description":"...","meta_keyword":"...",'
        f'"quantity":0}}\n'
        f"Только JSON."
    )

    response = await deepseek_client.chat(prompt, max_tokens=1200, temperature=0.4, system=system)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            ai = json.loads(match.group(0))
        else:
            ai = json.loads(response)
    except (json.JSONDecodeError, ValueError):
        ai = {
            "description": name,
            "model": "",
            "category_id": 0,
            "cost_price_cash": 0,
            "cost_price_cashless": 0,
            "retail_price": 0,
            "wholesale_price": 0,
            "meta_title": name,
            "meta_description": "",
            "meta_keyword": "",
            "quantity": 0,
        }

    # Создаём товар в базе
    product = product_db.add_product(
        sku=sku,
        name=name,
        model=ai.get("model", ""),
        quantity=ai.get("quantity", 0),
        cost_price_cash=ai.get("cost_price_cash", 0),
        cost_price_cashless=ai.get("cost_price_cashless", 0),
        retail_price=ai.get("retail_price", 0),
        wholesale_price=ai.get("wholesale_price", 0),
        category_id=ai.get("category_id", 0),
        description=ai.get("description", ""),
        meta_title=ai.get("meta_title", ""),
        meta_description=ai.get("meta_description", ""),
        meta_keyword=ai.get("meta_keyword", ""),
        image=image_path,
    )

    # Создаём в OpenCart
    oc_result = None
    seo_result = None
    if settings.opencart_api_url:
        try:
            oc_result = await opencart_api.product_add({
                "sku": sku,
                "name": name,
                "model": ai.get("model", ""),
                "quantity": ai.get("quantity", 0),
                "price": ai.get("retail_price", 0),
                "description": ai.get("description", ""),
                "category_id": ai.get("category_id", 0),
                "image": image_path,
            })
            # SEO
            if oc_result and oc_result.get("product_id"):
                seo_result = await opencart_api.seo_update_meta(
                    oc_result["product_id"],
                    meta_title=ai.get("meta_title", ""),
                    meta_description=ai.get("meta_description", ""),
                    meta_keyword=ai.get("meta_keyword", ""),
                )
        except Exception as exc:
            oc_result = {"status": "error", "detail": str(exc)}

    return {
        "status": "created",
        "sku": sku,
        "product": product,
        "ai_generated": ai,
        "image": image_path,
        "opencart": oc_result,
        "seo": seo_result,
    }


@router.post("/bulkAdd")
async def bulk_add_products(payload: dict):
    """Массовое добавление товаров. Принимает массив товаров."""
    products = payload.get("products", [])
    if not products or not isinstance(products, list):
        raise HTTPException(status_code=400, detail="products должен быть массивом")

    result = product_db.bulk_add_products(products)

    # Синхронизация с OpenCart (по одному, чтобы получить product_id)
    oc_results = []
    if settings.opencart_api_url:
        for p in products:
            sku = (p.get("sku") or "").strip()
            product = product_db.get_by_sku(sku)
            if not product:
                continue
            try:
                oc = await opencart_api.product_add({
                    "sku": sku,
                    "name": p.get("name", ""),
                    "model": p.get("model", ""),
                    "quantity": p.get("quantity", 0),
                    "price": p.get("retail_price", 0),
                    "description": p.get("description", ""),
                    "category_id": p.get("category_id", 0),
                })
                oc_results.append({"sku": sku, "status": "ok", "product_id": oc.get("product_id")})
            except Exception as exc:
                oc_results.append({"sku": sku, "status": "error", "detail": str(exc)})

    return {"status": "ok", **result, "opencart": oc_results}


@router.post("/uploadImage/{sku}")
async def upload_product_image(sku: str, file: UploadFile):
    """Загрузить изображение товара в OpenCart."""
    product = product_db.get_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    if not settings.opencart_api_url:
        raise HTTPException(status_code=400, detail="OpenCart API не настроен")

    raw = await file.read()
    try:
        result = await opencart_api.upload_image(raw, file.filename or f"{sku}.jpg")
        image_path = result.get("path") or result.get("image", "")

        # Обновляем товар в базе
        product_db.edit_product(sku, image=image_path)

        # Обновляем в OpenCart
        if product.product_id:
            await opencart_api.product_edit(product.product_id, {"image": image_path})

        return {"status": "uploaded", "sku": sku, "image": image_path, "opencart": result}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/aiPrice/{sku}")
async def ai_generate_price(sku: str):
    """DeepSeek анализирует товар и предлагает оптимальную цену на основе себестоимости и рынка."""
    import json

    product = product_db.get_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    cost = product.cost_price_cash or product.cost_price_cashless or 0
    if not cost:
        raise HTTPException(status_code=400, detail="Нет себестоимости — нечего анализировать")

    system = (
        "Ты — аналитик цен строительного магазина stroiapp.ru. "
        "Анализируешь себестоимость и предлагаешь оптимальные цены для розницы и опта. "
        "Учитывай тип материала, рыночные наценки, конкурентные цены. "
        "Отвечай ТОЛЬКО в формате JSON."
    )
    prompt = (
        f"Товар: {product.name}\n"
        f"Себестоимость (наличный): {product.cost_price_cash}₽\n"
        f"Себестоимость (безнал): {product.cost_price_cashless}₽\n"
        f"Текущая розничная цена: {product.retail_price}₽\n"
        f"Текущая оптовая цена: {product.wholesale_price}₽\n\n"
        f"Предложи оптимальные цены:\n"
        f"1. retail_price — розничная цена (наценка 25-45%)\n"
        f"2. wholesale_price — оптовая цена (наценка 10-20%)\n"
        f"3. recommended_position — рекомендованная позиция в рекламе (1-3)\n"
        f"4. reasoning — обоснование (кратко)\n\n"
        f"Формат JSON:\n"
        f'{{"retail_price":0,"wholesale_price":0,"recommended_position":1,"reasoning":"..."}}\n'
        f"Только JSON."
    )

    response = await deepseek_client.chat(prompt, max_tokens=500, temperature=0.3, system=system)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            parsed = json.loads(response)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=500, detail="AI не смог сгенерировать цену")

    # Применяем цены
    product_db.edit_product(
        sku,
        retail_price=parsed.get("retail_price", product.retail_price),
        wholesale_price=parsed.get("wholesale_price", product.wholesale_price),
    )

    # Синхронизация с OpenCart
    oc_result = None
    if settings.opencart_api_url and product.product_id:
        try:
            oc_result = await opencart_api.product_edit(product.product_id, {
                "price": parsed.get("retail_price", product.retail_price),
            })
        except Exception as exc:
            oc_result = {"status": "error", "detail": str(exc)}

    return {
        "status": "priced",
        "sku": sku,
        "ai_price": parsed,
        "opencart": oc_result,
    }


@router.post("/add")
async def add_product(payload: ProductCreate):
    """Добавить новый товар. Опционально AI генерирует описание и SEO."""
    if payload.generate_ai:
        ai_data = await _generate_ai_content(payload.name, payload.description)
        payload.description = ai_data.get("description", payload.description)
        payload.model = ai_data.get("model", payload.model)

    try:
        product = product_db.add_product(
            sku=payload.sku,
            name=payload.name,
            model=payload.model,
            quantity=payload.quantity,
            cost_price_cash=payload.cost_price_cash,
            cost_price_cashless=payload.cost_price_cashless,
            retail_price=payload.retail_price,
            wholesale_price=payload.wholesale_price,
            category_id=payload.category_id,
            description=payload.description,
            image=payload.image,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    oc_result = None
    if settings.opencart_api_url:
        try:
            oc_result = await opencart_api.product_add({
                "sku": payload.sku,
                "name": payload.name,
                "model": payload.model,
                "quantity": payload.quantity,
                "price": payload.retail_price,
                "description": payload.description,
                "category_id": payload.category_id,
                "image": payload.image,
            })
        except Exception as exc:
            oc_result = {"status": "error", "detail": str(exc)}

    seo_result = None
    if payload.generate_ai and oc_result and oc_result.get("product_id"):
        try:
            seo_result = await opencart_api.seo_update_meta(
                oc_result["product_id"],
                meta_title=ai_data.get("meta_title", ""),
                meta_description=ai_data.get("meta_description", ""),
                meta_keyword=ai_data.get("meta_keyword", ""),
            )
        except Exception:
            pass

    return {
        "status": "created",
        "product": product,
        "opencart": oc_result,
        "seo": seo_result,
    }


@router.put("/edit/{sku}")
async def edit_product(sku: str, payload: ProductUpdate):
    """Редактировать товар. Обновляет только переданные поля."""
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    product = product_db.edit_product(sku, **update_data)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    oc_result = None
    if settings.opencart_api_url and product.product_id:
        try:
            oc_payload = {}
            if payload.name is not None:
                oc_payload["name"] = payload.name
            if payload.quantity is not None:
                oc_payload["quantity"] = payload.quantity
            if payload.retail_price is not None:
                oc_payload["price"] = payload.retail_price
            if payload.description is not None:
                oc_payload["description"] = payload.description
            if payload.image is not None:
                oc_payload["image"] = payload.image
            if oc_payload:
                oc_result = await opencart_api.product_edit(product.product_id, oc_payload)
        except Exception as exc:
            oc_result = {"status": "error", "detail": str(exc)}

    seo_result = None
    if any(v is not None for v in [payload.meta_title, payload.meta_description, payload.meta_keyword]):
        if settings.opencart_api_url and product.product_id:
            try:
                seo_result = await opencart_api.seo_update_meta(
                    product.product_id,
                    meta_title=payload.meta_title or "",
                    meta_description=payload.meta_description or "",
                    meta_keyword=payload.meta_keyword or "",
                )
            except Exception:
                pass

    return {"status": "updated", "product": product, "opencart": oc_result, "seo": seo_result}


@router.delete("/delete/{sku}")
async def delete_product(sku: str):
    """Удалить товар из базы и OpenCart."""
    product = product_db.get_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    deleted = product_db.delete_product(sku)

    oc_result = None
    if settings.opencart_api_url and product.product_id:
        try:
            oc_result = await opencart_api.product_delete(product.product_id)
        except Exception as exc:
            oc_result = {"status": "error", "detail": str(exc)}

    return {"status": "deleted", "sku": sku, "opencart": oc_result}


@router.post("/aiGenerate/{sku}")
async def ai_generate_content(sku: str):
    """AI генерирует описание, SEO meta и ключевые слова для товара."""
    product = product_db.get_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    ai_data = await _generate_ai_content(product.name, product.description)

    product_db.edit_product(
        sku,
        description=ai_data.get("description", ""),
        meta_title=ai_data.get("meta_title", ""),
        meta_description=ai_data.get("meta_description", ""),
        meta_keyword=ai_data.get("meta_keyword", ""),
    )

    seo_result = None
    if settings.opencart_api_url and product.product_id:
        try:
            seo_result = await opencart_api.seo_update_meta(
                product.product_id,
                meta_title=ai_data.get("meta_title", ""),
                meta_description=ai_data.get("meta_description", ""),
                meta_keyword=ai_data.get("meta_keyword", ""),
            )
        except Exception as exc:
            seo_result = {"status": "error", "detail": str(exc)}

    return {
        "status": "generated",
        "sku": sku,
        "ai_content": ai_data,
        "seo": seo_result,
    }


async def _generate_ai_content(name: str, existing_desc: str = "") -> dict:
    """DeepSeek генерирует описание, SEO и ключевые слова для товара."""
    import json

    system = (
        "Ты — SEO-копирайтер для строительного магазина stroiapp.ru. "
        "Создаёшь продающие описания товаров, SEO meta-теги и ключевые слова. "
        "Отвечай ТОЛЬКО в формате JSON."
    )
    prompt = (
        f"Товар: {name}\n"
        f"Существующее описание: {existing_desc[:200] if existing_desc else 'нет'}\n\n"
        f"Сгенерируй:\n"
        f"1. description — продающее описание (300-500 символов)\n"
        f"2. meta_title — title для SEO (до 60 символов)\n"
        f"3. meta_description — meta description (до 160 символов)\n"
        f"4. meta_keyword — ключевые слова через запятую\n"
        f"5. model — артикул/модель если можно определить из названия\n\n"
        f"Формат JSON:\n"
        f'{{"description":"...","meta_title":"...","meta_description":"...","meta_keyword":"...","model":"..."}}\n'
        f"Только JSON."
    )

    response = await deepseek_client.chat(prompt, max_tokens=800, temperature=0.5, system=system)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(response)
    except (json.JSONDecodeError, ValueError):
        return {"description": response, "meta_title": name, "meta_description": "", "meta_keyword": "", "model": ""}


@router.post("/foreman/calculatePrices")
def foreman_calculate_prices(payload: dict):
    """Прораб загружает список SKU — система ищет в ProductDB и считает цены."""
    skus = payload.get("skus", [])
    margin_retail = payload.get("margin_retail", 1.35)
    margin_wholesale = payload.get("margin_wholesale", 1.25)
    if not skus or not isinstance(skus, list):
        raise HTTPException(status_code=400, detail="skus must be a non-empty list")
    results = product_db.calculate_prices_for_foreman(skus, margin_retail, margin_wholesale)
    found = sum(1 for r in results if r["found"])
    return {
        "status": "calculated",
        "total": len(results),
        "found": found,
        "not_found": len(results) - found,
        "items": results,
    }


@router.post("/foreman/uploadDocument")
async def foreman_upload_document(file: UploadFile):
    """Загружает PDF, фото, TXT — извлекает SKU через DeepSeek (PDF/TXT) или OCR (фото)."""
    filename = (file.filename or "").lower()
    raw = await file.read()
    skus = []
    error = None
    source = "unknown"

    try:
        if filename.endswith('.pdf'):
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                # DeepSeek извлекает SKU из текста
                skus = await deepseek_client.extract_skus(text)
                source = "pdf+deepseek"
            except ImportError:
                error = "PyPDF не установлен — установите: pip install pypdf"

        elif filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            try:
                import pytesseract
                from PIL import Image as PILImage
                image = PILImage.open(io.BytesIO(raw))
                text = pytesseract.image_to_string(image, lang='rus+eng')
                # DeepSeek извлекает SKU из OCR-текста
                skus = await deepseek_client.extract_skus(text)
                source = "ocr+deepseek"
            except ImportError:
                error = "OCR не установлен — установите: pip install pytesseract Pillow"

        elif filename.endswith(('.txt', '.csv', '.tsv')):
            text = raw.decode("utf-8-sig")
            skus = await deepseek_client.extract_skus(text)
            source = "text+deepseek"

        else:
            try:
                text = raw.decode("utf-8-sig")
                skus = await deepseek_client.extract_skus(text)
                source = "text+deepseek"
            except UnicodeDecodeError:
                error = "Неизвестный формат файла"

    except Exception as e:
        error = str(e)

    return {
        "status": "extracted" if skus else "no_skus",
        "filename": file.filename,
        "source": source,
        "skus_found": len(skus),
        "skus": skus,
        "error": error,
    }
