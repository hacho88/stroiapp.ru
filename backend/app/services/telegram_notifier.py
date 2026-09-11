import httpx

from app.core.config import settings
from app.models.automation import TelegramRequest


class TelegramNotifier:
    def __init__(self) -> None:
        self.token = settings.telegram_bot_token
        self.manager_chat_id = settings.manager_telegram_chat_id
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: str, text: str) -> dict:
        if not self.token:
            return {"status": "skipped", "reason": "no token"}
        try:
            response = await self.client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
            response.raise_for_status()
            return {"status": "sent", "chat_id": chat_id}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    async def notify(self, request: TelegramRequest) -> dict:
        chat_id = request.chat_id or self.manager_chat_id
        if not chat_id:
            return {"status": "skipped", "reason": "no chat_id"}
        return await self.send_message(chat_id, request.message)

    async def notify_order(self, order_id: int, total: float, items: list[str]) -> dict:
        text = (
            f"<b>Новый заказ #{order_id}</b>\n"
            f"Сумма: {total:.2f} ₽\n"
            f"Товары: {', '.join(items[:5])}{'...' if len(items) > 5 else ''}"
        )
        return await self.send_message(self.manager_chat_id, text)

    async def notify_price_sync(self, updated: int) -> dict:
        text = f"<b>Синхронизация цен</b>\nОбновлено товаров: {updated}"
        return await self.send_message(self.manager_chat_id, text)

    async def close(self):
        await self.client.aclose()


telegram_notifier = TelegramNotifier()
