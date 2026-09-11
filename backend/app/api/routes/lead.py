from fastapi import APIRouter

from app.models.automation import InvoiceRequest
from app.services.lead_processor import lead_processor

router = APIRouter(prefix="/lead", tags=["lead"])


@router.get("/status")
def lead_status():
    return {"status": "ok", "service": "lead"}


@router.post("/invoice")
async def create_invoice(payload: InvoiceRequest):
    return await lead_processor.create_invoice(payload)


@router.get("/validateInn")
async def validate_inn(inn: str):
    return await lead_processor.validate_inn(inn)
