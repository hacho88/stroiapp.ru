"""
Cache Warmer API routes for TTFB optimization pipeline.
"""

from fastapi import APIRouter

from app.services.cache_warmer import get_cache_warmer

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/status")
def cache_status():
    return {"status": "ok", "service": "cache_warmer"}


@router.post("/warm")
async def cache_warm(max_urls: int = 200):
    """Parse sitemap and aggressively warm cache by hitting URLs with Chrome UA."""
    warmer = get_cache_warmer()
    result = await warmer.run(max_urls=max_urls)
    return result
