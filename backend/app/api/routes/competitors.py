from fastapi import APIRouter

from app.services.competitor_spy import competitor_spy

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("/status")
def competitors_status():
    return {"status": "ok", "service": "competitors"}


@router.post("/scan")
async def scan(url: str):
    return await competitor_spy.scan_url(url)


@router.post("/add")
def add_competitor(name: str, url: str = ""):
    competitor_id = competitor_spy.add(name, url)
    return {"status": "added", "id": competitor_id}


@router.get("/list")
def list_competitors():
    return competitor_spy.list()


@router.post("/importPrices")
def import_prices(competitor_id: int, prices: list[dict]):
    return competitor_spy.add_manual_prices(competitor_id, prices)


@router.get("/compare")
def compare():
    return competitor_spy.compare()
