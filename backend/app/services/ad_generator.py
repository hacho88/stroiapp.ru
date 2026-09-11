import json
import re

from app.services.deepseek_client import deepseek_client


class AdGenerator:
    """Генерирует тексты объявлений и ключевые слова через DeepSeek для Яндекс.Директа."""

    async def generate_ad_content(self, product: dict) -> dict:
        """Генерирует заголовок, текст объявления и ключевые слова для товара."""
        name = product.get("name", "")
        price = product.get("retail_price", "")
        category = product.get("category_name", "стройматериалы")
        specs = product.get("specs", {})

        specs_text = ", ".join(f"{k}: {v}" for k, v in specs.items()) if specs else ""

        system = (
            "Ты — специалист по контекстной рекламе Яндекс Директ для строительного магазина stroiapp.ru. "
            "Пиши на русском. Давай конкретные, продающие тексты. Не пиши воду."
        )
        prompt = (
            f"Товар: {name}\n"
            f"Категория: {category}\n"
            f"Цена: {price}₽\n"
            f"Характеристики: {specs_text}\n\n"
            f"Сгенерируй рекламное объявление для Яндекс Директ:\n"
            f"1. Title — заголовок до 56 символов, продающий, с названием товара\n"
            f"2. Text — текст до 75 символов, с УТП (доставка, опт, НДС, цена)\n"
            f"3. Keywords — 7-10 ключевых фраз (точные, 2-5 слов)\n\n"
            f"Формат ответа — строго JSON:\n"
            f'{{"title":"...","text":"...","keywords":["...","..."]}}\n'
            f"Только JSON, без текста до или после."
        )

        response = await deepseek_client.chat(prompt, max_tokens=600, temperature=0.4, system=system)
        parsed = self._parse_json(response)

        title = parsed.get("title", name[:56]) if parsed else name[:56]
        text = parsed.get("text", f"{name} — оптом с НДС, доставка Москва") if parsed else f"{name} — оптом с НДС, доставка Москва"
        keywords = parsed.get("keywords", [name, f"купить {name}", f"{name} цена"]) if parsed else [name, f"купить {name}", f"{name} цена"]

        title = title[:56]
        text = text[:75]
        keywords = [kw for kw in keywords if kw and len(kw) <= 80][:50]

        return {
            "product": name,
            "title": title,
            "text": text,
            "keywords": keywords,
            "url": product.get("url", "https://stroiapp.ru"),
        }

    async def generate_batch(self, products: list[dict]) -> list[dict]:
        """Генерирует рекламные материалы для списка товаров."""
        results = []
        for product in products[:20]:
            ad = await self.generate_ad_content(product)
            results.append(ad)
        return results

    def _parse_json(self, text: str) -> dict | None:
        try:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            match = re.search(r'(\{.*?\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None


ad_generator = AdGenerator()
