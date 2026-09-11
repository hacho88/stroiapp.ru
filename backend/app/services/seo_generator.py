import httpx

from app.core.config import settings
from app.models.automation import FAQItem, SEORequest


class SEOGenerator:
    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    async def _deepseek_chat(self, prompt: str) -> str:
        if not self.api_key:
            return ""
        try:
            response = await self.client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""

    async def generate_description(self, request: SEORequest) -> dict[str, str]:
        specs = ", ".join(f"{key}: {value}" for key, value in request.specs.items()) or "характеристики уточняются"
        prompt = (
            f"Напиши SEO-описание товара '{request.name}' для интернет-магазина стройматериалов. "
            f"Технические характеристики: {specs}. "
            f"Акцент на B2B: поставки для юрлиц, опт, НДС, доставка по Москве и МО. "
            f"Длина до 800 символов. Без приветствий и служебных фраз."
        )
        ai_text = await self._deepseek_chat(prompt)
        if ai_text:
            description = ai_text[:800]
        else:
            description = (
                f"{request.name} подходит для строительных объектов, снабжения бригад и закупок оптом. "
                f"Технические параметры: {specs}. Поставляем для юрлиц с НДС, организуем доставку по Москве и МО, "
                f"помогаем быстро закрывать потребность объекта без переплаты."
            )
        return {"sku": request.sku, "description": description[:800]}

    async def auto_fill_meta(self, request: SEORequest) -> dict[str, str]:
        prompt = (
            f"Сгенерируй meta-title и meta-description для товара '{request.name}' стройматериалов. "
            f"Формат: Title: ... Description: ... Keywords: ... "
            f"Акцент: купить оптом, с НДС, доставка Москва."
        )
        ai_text = await self._deepseek_chat(prompt)
        if ai_text and "Title:" in ai_text:
            lines = ai_text.split("\n")
            title = next((l.replace("Title:", "").strip() for l in lines if l.startswith("Title:")), "")
            description = next((l.replace("Description:", "").strip() for l in lines if l.startswith("Description:")), "")
            keywords = next((l.replace("Keywords:", "").strip() for l in lines if l.startswith("Keywords:")), "")
            if title and description:
                return {"title": title, "description": description, "keywords": keywords}
        return {
            "title": f"{request.name} купить оптом в Москве с НДС",
            "description": f"{request.name}: поставка для юрлиц, оптовые цены, доставка на объект по Москве и МО.",
            "keywords": f"{request.name}, купить оптом, стройматериалы Москва, с НДС, доставка на объект",
        }

    def generate_faq(self, request: SEORequest) -> list[FAQItem]:
        return [
            FAQItem(question=f"Можно ли купить {request.name} по безналу?", answer="Да, выставляем счет для юрлиц и работаем с НДС."),
            FAQItem(question=f"Есть ли доставка на объект?", answer="Да, доставка доступна по Москве и Московской области."),
            FAQItem(question=f"Можно ли заказать оптом?", answer="Да, система рассчитывает оптовую цену и выгодные условия поставки."),
        ]

    async def bulk_generate(self, requests: list[SEORequest]) -> list[dict]:
        results = []
        for request in requests:
            desc = await self.generate_description(request)
            meta = await self.auto_fill_meta(request)
            faq = self.generate_faq(request)
            results.append({
                "sku": request.sku,
                "description": desc["description"],
                **meta,
                "faq": [f.model_dump() for f in faq],
            })
        return results


seo_generator = SEOGenerator()
