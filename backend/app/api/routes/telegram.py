from fastapi import APIRouter

from app.models.automation import TelegramRequest
from app.services.telegram_notifier import telegram_notifier

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/status")
def telegram_status():
    return {"status": "ok", "service": "telegram"}


@router.post("/notify")
async def notify(payload: TelegramRequest):
    return await telegram_notifier.notify(payload)


@router.post("/test")
async def test_notification():
    return await telegram_notifier.send_message(
        telegram_notifier.manager_chat_id,
        "<b>Тест AI StroiApp</b>\nУведомления работают!"
    )


@router.post("/notifyOrder")
async def notify_order(order_id: int, total: float, items: list[str]):
    return await telegram_notifier.notify_order(order_id, total, items)


@router.post("/notifyPriceSync")
async def notify_price_sync(updated: int):
    return await telegram_notifier.notify_price_sync(updated)
