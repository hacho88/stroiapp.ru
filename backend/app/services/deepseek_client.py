import httpx
from app.core.config import settings

class DeepSeekClient:
    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.client = httpx.AsyncClient(timeout=300.0)

    async def chat(self, prompt: str, model: str = "deepseek-chat", max_tokens: int = 4096, temperature: float = 0.7, system: str = "") -> str:
        if not self.api_key:
            return ""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return f"[DeepSeek error: {type(exc).__name__}: {exc}]"

    async def generate_article(self, topic: str) -> str:
        system = "Ты — SEO-копирайтер для строительного магазина в Москве. Пиши на русском языке."
        prompt = (
            f"Напиши SEO-статью на тему: {topic}\n\n"
            f"Требования:\n"
            f"- Объём: 400-600 символов\n"
            f"- Акцент на B2B: поставки для юрлиц, опт, НДС, доставка по Москве и МО\n"
            f"- Без приветствий и служебных фраз\n"
            f"- В конце призыв к действию: заказать в StroiApp.ru"
        )
        return await self.chat(prompt, max_tokens=600, system=system)

    async def generate_blog_article(self, product_name: str, product_info: str = "") -> dict:
        """Генерация длинной SEO-статьи в стиле Дзен/Хабр для блога.
        Возвращает dict с title, content, intro, meta_title, meta_description, slug_hint."""
        system = (
            "Ты — опытный строитель-практик с 15-летним стажем, который пишет статьи для блога строительного магазина. "
            "Пиши как живой человек: от первого лица, с личным опытом, ошибками и выводами. "
            "Стиль — как Дзен или Хабр: разговорный, экспертный, с историями из практики. "
            "Без канцелярита, без рекламных клише, без 'в нашей компании'. "
            "HTML-разметка: <h2>, <h3>, <p>, <ul>, <li>, <strong>. "
            "Без изображений. Без приветствий. Без заключений типа 'итак, подводя итоги'."
        )
        prompt = (
            f"Напиши большую статью для блога строительного магазина StroiApp.ru.\n\n"
            f"Тема/товар: {product_name}\n"
            f"Доп. информация: {product_info or 'нет'}\n\n"
            f"Требования:\n"
            f"- Объём: 3000-5000 символов (это важно!)\n"
            f"- Пиши от лица строителя-практика: 'я', 'на моём опыте', 'был случай'\n"
            f"- Структура: 3-5 разделов с <h2>, подзаголовки <h3> где нужно\n"
            f"- Реальные цифры: расход на м2, цены, сроки, объёмы\n"
            f"- Сравнения с аналогами, плюсы и минусы\n"
            f"- Практические советы: как выбрать, на что смотреть, частые ошибки\n"
            f"- Упомяни применение на объектах в Москве и МО\n"
            f"- В конце 1-2 предложения: где купить с безналом и НДС, доставка\n"
            f"- НЕ пиши: 'в этой статье мы рассмотрим', 'давайте разберемся', 'итак'\n"
            f"- НЕ повторяй заголовок в первом абзаце\n\n"
            f"Ответь СТРОГО в формате JSON:\n"
            f'{{"title": "заголовок статьи (без кавычек внутри)", '
            f'"intro": "краткое описание 150-200 символов", '
            f'"content": "HTML-контент статьи", '
            f'"meta_title": "SEO title 60-70 символов", '
            f'"meta_description": "SEO description 150-160 символов"}}'
        )
        import json as _json
        try:
            raw = await self.chat(prompt, max_tokens=4096, temperature=0.8, system=system)
            # Try to parse JSON from response
            # Remove markdown code fences if present
            raw = raw.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            raw = raw.strip()
            if raw.startswith('{') and raw.endswith('}'):
                return _json.loads(raw)
            # Try to find JSON in text
            import re as _re
            match = _re.search(r'\{.*\}', raw, _re.DOTALL)
            if match:
                return _json.loads(match.group(0))
            # Fallback: return as plain content
            return {
                "title": product_name,
                "intro": raw[:200],
                "content": raw,
                "meta_title": product_name[:70],
                "meta_description": raw[:160],
            }
        except Exception as exc:
            return {
                "title": product_name,
                "intro": f"Статья о {product_name}",
                "content": f"<p>Ошибка генерации: {exc}</p>",
                "meta_title": product_name[:70],
                "meta_description": f"Статья о {product_name} — купить в StroiApp.ru"[:160],
            }

    async def generate_kp(self, competitor_name: str, issues: list[str]) -> str:
        system = "Ты — менеджер по продажам строительных материалов."
        issues_text = "\n".join(f"- {i}" for i in issues) if issues else "- нет информации"
        prompt = (
            f"Напиши короткое коммерческое предложение для клиента, который рассматривал конкурента {competitor_name}.\n\n"
            f"Негативные моменты о конкуренте:\n{issues_text}\n\n"
            f"Наши преимущества:\n"
            f"- Наличие и безнал с НДС\n"
            f"- Доставка по Москве и МО\n"
            f"- Оптовые цены\n"
            f"- Работаем с 2018 года\n\n"
            f"Текст должен быть убедительным, коротким (до 500 символов), без воды."
        )
        return await self.chat(prompt, max_tokens=500, system=system)

    async def extract_skus(self, text: str) -> list[str]:
        """DeepSeek вытаскивает SKU/артикулы из текста документа."""
        if not self.api_key:
            return []
        system = "Ты — помощник по извлечению артикулов (SKU) из документов. Отвечай только JSON-массивом строк, без пояснений."
        prompt = (
            f"Из текста ниже извлеки ВСЕ артикулы товаров (SKU). "
            f"Это может быть список, таблица, счёт, спецификация или КП. "
            f"Артикулы обычно выглядят как комбинации букв и цифр (например: ЦЕМ500, ПСБ300, 12345, AB-001). "
            f"Игнорируй единицы измерения (кг, шт, м2), цены, даты. "
            f"Ответь строго JSON-массивом строк, без форматирования markdown.\n\n"
            f"Текст документа:\n{text[:4000]}"
        )
        try:
            response = await self.chat(prompt, model="deepseek-chat", max_tokens=400, temperature=0.2, system=system)
            import json, re
            # Ищем JSON в ответе
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                skus = json.loads(match.group(0))
                if isinstance(skus, list):
                    return [str(s).strip() for s in skus if str(s).strip()]
            # Fallback: строки через запятую
            return [s.strip() for s in response.replace("'", '"').split(",") if s.strip() and len(s.strip()) >= 3]
        except Exception:
            return []

    async def close(self):
        await self.client.aclose()


deepseek_client = DeepSeekClient()
