from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.opencart_api import opencart_api

router = APIRouter(prefix="/autosmeta", tags=["autosmeta"])

MARKUP = 1.285


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Автосмета — раздел работает"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Загрузка фото/PDF/Excel сметы"""
    content = await file.read()
    return {"filename": file.filename, "status": "uploaded", "size": len(content), "document_id": 1}


@router.post("/recognize")
async def recognize_document(payload: dict):
    """Распознавание сметы (Tesseract OCR) + сверка со складом — пока возвращаем наши товары как распознанные"""
    try:
        products = await opencart_api.get_action("product/list", {"limit": 50})
        items = products.get("products", []) if isinstance(products, dict) else (products if isinstance(products, list) else [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    matched = []
    for p in items[:15]:
        price = float(p.get("price", 0) or 0)
        price_beznal = price * MARKUP
        matched.append({
            "name": p.get("name", ""),
            "product_id": p.get("product_id"),
            "price_nal": round(price, 2),
            "price_beznal": round(price_beznal, 2),
            "quantity": 1,
            "unit": "шт.",
        })

    total_nal = sum(i["price_nal"] * i["quantity"] for i in matched)
    total_beznal = sum(i["price_beznal"] * i["quantity"] for i in matched)

    return {
        "items": matched,
        "matched_count": len(matched),
        "missing_count": 0,
        "total_nal": round(total_nal, 2),
        "total_beznal": round(total_beznal, 2),
    }


@router.post("/generate-invoice")
async def generate_invoice(payload: dict):
    """Генерация счёта (нал / безнал по выбору)"""
    payment_type = payload.get("payment_type", "nal")
    items = payload.get("items", [])
    total = sum(
        (i.get("price_nal") if payment_type == "nal" else i.get("price_beznal", 0)) * i.get("quantity", 1)
        for i in items
    )
    return {
        "invoice_id": f"INV-{hash(str(items)) % 100000:05d}",
        "payment_type": payment_type,
        "total": round(total, 2),
        "items_count": len(items),
        "invoice_url": None,
    }
