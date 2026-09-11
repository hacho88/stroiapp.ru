from app.models.automation import InvoiceRequest
from app.services.dadata_api import dadata_api


class LeadProcessor:
    async def create_invoice(self, request: InvoiceRequest) -> dict[str, str | int | None]:
        inn_info = await dadata_api.validate_inn(request.inn)
        if inn_info.get("status") == "found":
            name = inn_info.get("name", "")
            address = inn_info.get("address", "")
        else:
            name = "Организация не найдена"
            address = ""
        return {
            "status": "created",
            "inn": request.inn,
            "email": request.email,
            "order_id": request.order_id,
            "company_name": name,
            "address": address,
            "pdf_url": f"/invoices/{request.order_id or request.inn}.pdf",
        }

    async def validate_inn(self, inn: str) -> dict:
        return await dadata_api.validate_inn(inn)


lead_processor = LeadProcessor()
