"""
Speculation Rules API routes for Chromium Prerender pipeline.
"""

from fastapi import APIRouter

from app.services.speculation_engine import get_speculation_engine

router = APIRouter(prefix="/speculation", tags=["speculation"])


@router.get("/status")
def speculation_status():
    return {"status": "ok", "service": "speculation"}


@router.post("/generate")
async def speculation_generate(current_path: str = "/"):
    """Generate and save speculation rules for the current page context."""
    engine = get_speculation_engine()
    result = await engine.generate_and_save(current_path)
    return result


@router.get("/rules")
async def speculation_rules():
    """Retrieve the currently active speculation rules from OpenCart."""
    engine = get_speculation_engine()
    rules = await engine.get_saved_rules()
    if rules:
        return {"status": "ok", "rules": rules}
    return {"status": "ok", "rules": {}}
