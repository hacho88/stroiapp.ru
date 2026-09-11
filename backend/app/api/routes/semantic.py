"""
Semantic Parser API routes for AI-Optimized Layout & JSON-LD pipeline.
"""

from fastapi import APIRouter

from app.services.semantic_parser import get_semantic_parser

router = APIRouter(prefix="/semantic", tags=["semantic"])


@router.get("/status")
def semantic_status():
    return {"status": "ok", "service": "semantic"}


@router.post("/process")
async def semantic_process(limit: int = 50):
    """Process all products: clean HTML, restructure, inject JSON-LD."""
    parser = get_semantic_parser()
    result = await parser.process_all(limit=limit)
    return result


@router.post("/process-product")
async def semantic_process_product(product_id: int):
    """Process a single product by ID."""
    from app.services.opencart_api import opencart_api

    try:
        prod = await opencart_api.get_action("product/get", {"product_id": product_id})
    except Exception as exc:
        return {"status": "error", "message": str(exc)[:300]}

    if not prod or prod.get("error"):
        return {"status": "error", "message": "Product not found"}

    parser = get_semantic_parser()
    result = await parser.process_product(prod)
    return result
