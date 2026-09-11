import httpx

from app.core.config import settings


class MaxNotifier:
    """Уведомления через MAX мессенджер (platform-api2.max.ru)."""

    def __init__(self) -> None:
        self.token = settings.max_bot_token
        self.chat_id = settings.max_chat_id
        self.base_url = "https://platform-api2.max.ru"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_message(self, chat_id: str | int | None = None, text: str = "") -> dict:
        if not self.token:
            return {"status": "skipped", "reason": "no MAX bot token"}
        target_chat = chat_id or self.chat_id
        if not target_chat:
            return {"status": "skipped", "reason": "no chat_id"}

        try:
            response = await self.client.post(
                f"{self.base_url}/messages",
                params={"chat_id": target_chat},
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text[:4000],
                    "format": "html",
                },
            )
            response.raise_for_status()
            return {"status": "sent", "chat_id": target_chat}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    async def notify_order(self, order_id: int, total: float, items: list[str]) -> dict:
        text = (
            f"<b>Новый заказ #{order_id}</b><br>"
            f"Сумма: {total:.2f} ₽<br>"
            f"Товары: {', '.join(items[:5])}{'...' if len(items) > 5 else ''}"
        )
        return await self.send_message(text=text)

    async def notify_price_sync(self, updated: int) -> dict:
        text = f"<b>Синхронизация цен</b><br>Обновлено товаров: {updated}"
        return await self.send_message(text=text)

    async def notify_tender(self, tender_info: dict) -> dict:
        text = (
            f"<b>📋 Новый тендер по нашим товарам</b><br><br>"
            f"Победитель: {tender_info.get('winner_name', '?')}<br>"
            f"Объект: {tender_info.get('building_type', '?')}<br>"
            f"Совпадений товаров: {tender_info.get('matched_count', 0)}<br>"
            f"Примерная смета: {tender_info.get('estimate_total', '?')} ₽"
        )
        return await self.send_message(text=text)

    async def close(self):
        await self.client.aclose()


max_notifier = MaxNotifier()
