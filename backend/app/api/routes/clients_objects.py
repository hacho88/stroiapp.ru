from fastapi import APIRouter, HTTPException
from app.services.opencart_api import opencart_api

router = APIRouter(prefix="/clients-objects", tags=["clients-objects"])

_objects = []
_object_counter = 1


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Клиенты и объекты — раздел работает"}


@router.get("/clients")
async def list_clients():
    """Список клиентов с сайта OpenCart"""
    try:
        clients = await opencart_api.get_action("customer/list", {"limit": 100})
        if isinstance(clients, dict) and "customers" in clients:
            return {"clients": clients["customers"], "count": len(clients["customers"])}
        return {"clients": [], "count": 0}
    except Exception:
        return {"clients": [], "count": 0}


@router.post("/add-object")
async def add_object(payload: dict):
    """Добавление объекта строительства (паспорт стройки)"""
    global _object_counter
    obj = {
        "object_id": _object_counter,
        "name": payload.get("name", "Объект без названия"),
        "address": payload.get("address", ""),
        "client_name": payload.get("client_name", ""),
        "stage": payload.get("stage", "фундамент"),
        "start_date": payload.get("start_date", ""),
        "end_date": payload.get("end_date", ""),
    }
    _objects.append(obj)
    _object_counter += 1
    return {"object_id": obj["object_id"], "status": "created", "object": obj}


@router.get("/objects")
async def list_objects():
    """Список объектов строительства"""
    return {"objects": _objects}


@router.get("/object/{object_id}/stages")
async def get_object_stages(object_id: int):
    """Этапы строительства объекта"""
    obj = next((o for o in _objects if o["object_id"] == object_id), None)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    stages = ["фундамент", "каркас", "кровля", "отделка", "инженерия", "сдача"]
    current = obj.get("stage", "фундамент")
    return {"object_id": object_id, "stages": stages, "current_stage": current}


@router.post("/forecast-demand")
async def forecast_demand(payload: dict):
    """Прогноз потребности материалов по объекту"""
    stage = payload.get("stage", "фундамент")
    area = payload.get("area", 100)  # м²
    forecasts = {
        "фундамент": [{"name": "Цемент М500", "quantity": area * 0.3, "unit": "мешок"}, {"name": "Щебень", "quantity": area * 0.5, "unit": "м³"}],
        "каркас": [{"name": "Арматура", "quantity": area * 2, "unit": "м"}, {"name": "Брус", "quantity": area * 0.1, "unit": "м³"}],
        "отделка": [{"name": "Штукатурка", "quantity": area * 3, "unit": "мешок"}, {"name": "Краска", "quantity": area * 0.2, "unit": "л"}],
    }
    items = forecasts.get(stage, [{"name": "Строительные материалы", "quantity": area * 0.5, "unit": "м³"}])
    return {"forecast": items, "total_volume": sum(i["quantity"] for i in items), "next_delivery_date": "2026-06-05"}


@router.post("/notify")
async def send_notification(payload: dict):
    """Уведомление клиенту (WhatsApp / Telegram)"""
    return {"status": "sent", "channel": payload.get("channel", "whatsapp"), "message": payload.get("message", "")}
