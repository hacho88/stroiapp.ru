import asyncio
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    ai_deepseek, ai_seo, auth, autosmeta, budget_roi, cache_warmer, clients_objects, competitors, competitors_bids,
    content_factory, dashboard, geo, import_products, lead, logistics, opencart, product, promotions, reviews,
    semantic, seo, site, site_builder, speculation, sync, telegram, tenders, yandex_metrika, yandex_webmaster,
)
from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(f"{settings.api_prefix}/") and not path.startswith(f"{settings.api_prefix}/auth/"):
        token = request.headers.get("x-auth-token", "")
        if not auth.verify_token(token):
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(ai_deepseek.router, prefix=settings.api_prefix)
app.include_router(site_builder.router, prefix=settings.api_prefix)
app.include_router(ai_seo.router, prefix=settings.api_prefix)
app.include_router(product.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(seo.router, prefix=settings.api_prefix)
app.include_router(lead.router, prefix=settings.api_prefix)
app.include_router(site.router, prefix=settings.api_prefix)
app.include_router(telegram.router, prefix=settings.api_prefix)
app.include_router(opencart.router, prefix=settings.api_prefix)
app.include_router(competitors.router, prefix=settings.api_prefix)
app.include_router(competitors_bids.router, prefix=settings.api_prefix)
app.include_router(geo.router, prefix=settings.api_prefix)
app.include_router(speculation.router, prefix=settings.api_prefix)
app.include_router(semantic.router, prefix=settings.api_prefix)
app.include_router(cache_warmer.router, prefix=settings.api_prefix)
app.include_router(budget_roi.router, prefix=settings.api_prefix)
app.include_router(promotions.router, prefix=settings.api_prefix)
app.include_router(tenders.router, prefix=settings.api_prefix)
app.include_router(reviews.router, prefix=settings.api_prefix)
app.include_router(autosmeta.router, prefix=settings.api_prefix)
app.include_router(content_factory.router, prefix=settings.api_prefix)
app.include_router(clients_objects.router, prefix=settings.api_prefix)
app.include_router(sync.router, prefix=settings.api_prefix)
app.include_router(logistics.router, prefix=settings.api_prefix)
app.include_router(import_products.router, prefix=settings.api_prefix)
app.include_router(yandex_webmaster.router, prefix=settings.api_prefix)
app.include_router(yandex_metrika.router, prefix=settings.api_prefix)


@app.on_event("startup")
async def start_background_tasks():
    from app.services.geo_auto_generator import get_geo_auto_generator
    geo_auto = get_geo_auto_generator()
    asyncio.create_task(geo_auto.start())

    from app.services.blog_auto_publisher import get_blog_auto_publisher
    blog_auto = get_blog_auto_publisher()
    asyncio.create_task(blog_auto.start())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/geo/auto-status")
def geo_auto_status():
    from app.services.geo_auto_generator import get_geo_auto_generator
    return get_geo_auto_generator().status()


@app.get(f"{settings.api_prefix}/blog/auto-status")
def blog_auto_status():
    from app.services.blog_auto_publisher import get_blog_auto_publisher
    return get_blog_auto_publisher().status()
