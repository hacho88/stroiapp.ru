from fastapi import APIRouter

from app.models.automation import SEORequest
from app.services.product_db import product_db
from app.services.seo_generator import seo_generator

router = APIRouter(prefix="/seo", tags=["seo"])


@router.get("/status")
def seo_status():
    return {"status": "ok", "service": "seo"}


@router.post("/generateDescription")
async def generate_description(payload: SEORequest):
    return await seo_generator.generate_description(payload)


@router.post("/generateAllDescriptions")
async def generate_all_descriptions(payloads: list[SEORequest]):
    return await seo_generator.bulk_generate(payloads)


@router.post("/autoFillMeta")
async def auto_fill_meta(payload: SEORequest):
    return await seo_generator.auto_fill_meta(payload)


@router.post("/generateFAQ")
def generate_faq(payload: SEORequest):
    return seo_generator.generate_faq(payload)


@router.post("/updateContent")
def update_content(payloads: list[SEORequest]):
    return {"status": "updated", "products": len(payloads)}


@router.get("/bulkGenerate")
async def bulk_generate_for_products(min_roi: int = 120, limit: int = 20):
    products = [
        p for p in product_db.list_products()
        if p.roi >= min_roi
    ][:limit]
    requests = [
        SEORequest(sku=p.sku, name=p.name, specs={"model": p.model, "price": str(p.retail_price)})
        for p in products
    ]
    results = await seo_generator.bulk_generate(requests)
    return {"status": "generated", "count": len(results), "results": results}
