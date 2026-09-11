from fastapi import APIRouter
from pydantic import BaseModel

from app.models.product import BudgetRequest
from app.services.dashboard import dashboard_service
from app.services.direct_commander import get_direct_commander
from app.services.ad_generator import ad_generator
from app.services.campaign_optimizer import campaign_optimizer
from app.services.product_db import product_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.post("/calculate")
def calculate(payload: BudgetRequest):
    return dashboard_service.calculate(payload.budget, product_db.list_products())


@router.get("/compare")
def compare():
    return dashboard_service.compare(product_db.list_products())


@router.get("/stats")
def stats():
    products = product_db.list_products()
    return {
        "status": "ok",
        "total_products": len(products),
        "profitable": sum(1 for p in products if p.roi >= 100),
        "avg_roi": sum(p.roi for p in products) / max(len(products), 1),
    }


@router.post("/launchAll")
async def launch_all():
    """Запуск кампании: AI → Директ → позиция #1 Москва и МО."""
    products = [p.model_dump() for p in product_db.list_products() if p.roi >= 120]
    return await get_direct_commander().launch_campaign(products)


@router.get("/campaigns")
def list_campaigns():
    return get_direct_commander().get_campaigns()


class GenerateAdsRequest(BaseModel):
    product_name: str = ""
    product_id: int | None = None
    limit: int = 5


@router.post("/generateAds")
async def generate_ads(req: GenerateAdsRequest):
    """AI генерирует тексты объявлений и ключевые слова для товаров."""
    if req.product_name:
        products = [{"name": req.product_name, "url": "https://stroiapp.ru"}]
    elif req.product_id:
        products = [{"name": f"Product {req.product_id}", "url": "https://stroiapp.ru"}]
    else:
        products = [
            p.model_dump() for p in product_db.list_products() if p.roi >= 120
        ][:req.limit]

    ads = await ad_generator.generate_batch(products)
    return {"status": "ok", "ads": ads, "count": len(ads)}


@router.post("/previewLaunch")
async def preview_launch():
    """Предпросмотр: AI генерирует топ-объявления с анализом конкурентов."""
    products = campaign_optimizer.get_profitable_products(min_roi=100, limit=5)
    ads = []
    for product in products:
        ad = await campaign_optimizer.generate_top_ad(product)
        ads.append(ad)
    return {
        "status": "ok",
        "strategy": "position_1_moscow_mo",
        "products_count": len(products),
        "ads": ads,
        "message": "Предпросмотр. Для запуска используйте /dashboard/launchAll",
    }


@router.post("/optimizeBids/{campaign_id}/{ad_group_id}")
async def optimize_bids(campaign_id: int, ad_group_id: int):
    """Оптимизация ставок для позиции #1 по всем ключевым словам группы."""
    return await campaign_optimizer.optimize_bids_for_position_one(campaign_id, ad_group_id)


@router.get("/campaignStats/{campaign_id}")
async def campaign_stats(campaign_id: int):
    """Статистика кампании: показы, клики, расход, CTR."""
    dc = get_direct_commander()
    return dc.get_campaign_stats([campaign_id])


@router.get("/profitableProducts")
def profitable_products(min_roi: int = 100, limit: int = 20):
    """Топ товаров по марже и ROI для рекламы."""
    products = campaign_optimizer.get_profitable_products(min_roi=min_roi, limit=limit)
    return {"status": "ok", "products": products, "count": len(products)}
