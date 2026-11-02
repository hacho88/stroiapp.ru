import asyncio

import httpx
from app.core.config import settings

# Транзиентные ошибки соединения — на них делаем retry
_RETRYABLE = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)

class DeepSeekClient:
    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.client = httpx.AsyncClient(timeout=300.0)

    async def chat(self, prompt: str, model: str = "deepseek-chat", max_tokens: int = 4096, temperature: float = 0.7, system: str = "", history: list | None = None) -> str:
        if not self.api_key:
            return ""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        # Память диалога: прошлые ходы вставляем между system и текущим user
        for m in (history or []):
            role = m.get("role")
            content = str(m.get("content") or "")[:1200]
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        last_exc = None
        for attempt in range(4):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except _RETRYABLE as exc:
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
            except Exception as exc:
                return f"[DeepSeek error: {type(exc).__name__}: {exc}]"
        return f"[DeepSeek error: {type(last_exc).__name__}: {last_exc}]"

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
            f"Напиши большую экспертную статью для журнала строительного магазина moscow.stroiapp.ru.\n\n"
            f"Тема/товар: {product_name}\n"
            f"Доп. информация: {product_info or 'нет'}\n\n"
            f"Требования:\n"
            f"- Объём: МИНИМУМ 10000 знаков текста в поле content (это критично, пиши развёрнуто, 6-9 разделов)\n"
            f"- Пиши от лица строителя-практика: 'я', 'на моём опыте', 'был случай'\n"
            f"- Структура: 6-9 разделов с <h2>, подзаголовки <h3>, списки <ul>/<li>\n"
            f"- Реальные цифры: расход на м2, цены, сроки, объёмы, пропорции замеса\n"
            f"- Сравнения с аналогами, плюсы и минусы, таблица-советы списками\n"
            f"- Практические блоки: как выбрать, на что смотреть при покупке, частые ошибки, хранение\n"
            f"- Упомяни применение на объектах в Москве и МО, наш автопарк (Газель/Пятитонник/Манипулятор до 10т)\n"
            f"- В конце 1-2 предложения: где купить на moscow.stroiapp.ru — наличные или безнал с НДС, доставка\n"
            f"- НЕ пиши: 'в этой статье мы рассмотрим', 'давайте разберемся', 'итак'\n"
            f"- НЕ повторяй заголовок в первом абзаце\n\n"
            f"Ответь СТРОГО в формате JSON:\n"
            f'{{"title": "заголовок статьи (без кавычек внутри)", '
            f'"category": "одна рубрика из списка: Продукт, Инструкция, Бизнес, Сервис, Видео", '
            f'"intro": "краткое описание 150-200 символов", '
            f'"content": "HTML-контент статьи на 10000+ знаков", '
            f'"meta_title": "SEO title 60-70 символов", '
            f'"meta_description": "SEO description 150-160 символов"}}'
        )
        import json as _json
        try:
            raw = await self.chat(prompt, max_tokens=8192, temperature=0.8, system=system)
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

    async def generate_category_seo(self, category_name: str, children_names: list[str] = None,
                                    sample_products: list[str] = None) -> dict:
        """SEO-пакет для страницы категории витрины: meta_title, meta_description,
        seo_text (HTML для низа страницы), faq (вопросы/ответы для FAQPage schema)."""
        children = ", ".join((children_names or [])[:10]) or "нет"
        products = ", ".join((sample_products or [])[:15]) or "нет"
        system = (
            "Ты — SEO-копирайтер строительного маркетплейса moscow.stroiapp.ru (Москва и МО). "
            "Пишешь полезные тексты для страниц категорий интернет-магазина стройматериалов. "
            "B2B+B2C: наличные и безнал с НДС, доставка по Москве и области своим автопарком "
            "(Газель/Пятитонник/Манипулятор до 10т), отгрузка со склада в день заказа. "
            "Пиши по делу, без воды и рекламных клише типа 'широкий ассортимент'."
        )
        prompt = (
            f"Категория каталога: «{category_name}».\n"
            f"Подкатегории: {children}.\n"
            f"Примеры товаров в категории: {products}.\n\n"
            f"Сделай SEO-пакет для страницы этой категории. Ответь СТРОГО валидным JSON без markdown:\n"
            f'{{"meta_title": "до 70 символов, формат «{category_name} — купить в Москве ...»", '
            f'"meta_description": "150-160 символов, с ценностью: опт/розница, НДС, доставка", '
            f'"seo_text": "HTML-текст 1200-1800 знаков: 2-3 абзаца <p> + список <ul><li>. '
            f'О чём писать: что входит в категорию, как выбрать (по каким параметрам), '
            f'типичные применения на объектах, как мы продаём (опт/розница, НДС, доставка по Москве и МО). '
            f'Не дублируй название категории в первом предложении. Только <p>, <ul>, <li>, <strong>.", '
            f'"faq": [{{"q": "вопрос покупателя", "a": "короткий конкретный ответ"}}, ... — 4 штуки: '
            f'про оплату безналом с НДС, сроки доставки по Москве/МО, минимальный заказ/опт, '
            f'что делать если нужного товара нет на сайте]}}'
        )
        import json as _json
        import re as _re
        try:
            raw = await self.chat(prompt, max_tokens=2048, temperature=0.7, system=system)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            match = _re.search(r"\{.*\}", raw, _re.DOTALL)
            data = _json.loads(match.group(0) if match else raw)
            if isinstance(data.get("faq"), list):
                data["faq"] = [
                    {"q": str(f.get("q", "")), "a": str(f.get("a", ""))}
                    for f in data["faq"][:6] if isinstance(f, dict) and f.get("q") and f.get("a")
                ]
            else:
                data["faq"] = []
            return data
        except Exception:
            return {
                "meta_title": f"{category_name} — купить в Москве | StroiApp"[:70],
                "meta_description": (
                    f"{category_name} с доставкой по Москве и МО: опт и розница, "
                    f"безнал с НДС, отгрузка со склада в день заказа."
                )[:160],
                "seo_text": "",
                "faq": [],
            }

    async def generate_product_seo(self, product_name: str, category_name: str = "",
                                   product_info: str = "") -> dict:
        """SEO-пакет для карточки товара витрины: meta_title, meta_description,
        seo_text (HTML-блок внизу страницы), faq (вопросы/ответы для FAQPage schema)."""
        system = (
            "Ты — SEO-копирайтер строительного маркетплейса moscow.stroiapp.ru (Москва и МО). "
            "Пишешь полезные тексты для карточек товаров интернет-магазина стройматериалов. "
            "B2B+B2C: наличные и безнал с НДС, доставка по Москве и области своим автопарком "
            "(Газель/Пятитонник/Манипулятор до 10т), отгрузка со склада в день заказа. "
            "Пиши по делу, без воды и рекламных клише типа 'широкий ассортимент'."
        )
        prompt = (
            f"Товар: «{product_name}».\n"
            f"Категория: {category_name or 'нет'}.\n"
            f"Данные карточки:\n{product_info or 'нет'}\n\n"
            f"Сделай SEO-пакет для страницы этого товара. Ответь СТРОГО валидным JSON без markdown:\n"
            f'{{"meta_title": "до 70 символов, формат «{product_name} — купить ... в Москве | StroiApp»", '
            f'"meta_description": "150-160 символов: ключевое свойство товара, цена/опт, НДС, доставка по Москве", '
            f'"seo_text": "HTML-текст 900-1400 знаков: 2-3 абзаца <p> + список <ul><li>. '
            f'О чём писать: что это за товар и для каких работ, как выбрать фасовку/марку/объём, '
            f'расход или нормы применения, типичные ошибки при покупке, '
            f'как продаём (опт/розница, безнал с НДС, доставка по Москве и МО, самовывоз). '
            f'Не начинай первое предложение с названия товара. Только <p>, <ul>, <li>, <strong>.", '
            f'"faq": [{{"q": "вопрос покупателя", "a": "короткий конкретный ответ"}}, ... — 3 штуки: '
            f'про доставку/сроки по Москве и МО, про безнал с НДС для юрлиц, '
            f'про расход/совместимость или что делать если нужен другой объём]}}'
        )
        import json as _json
        import re as _re
        try:
            raw = await self.chat(prompt, max_tokens=1600, temperature=0.7, system=system)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            match = _re.search(r"\{.*\}", raw, _re.DOTALL)
            data = _json.loads(match.group(0) if match else raw)
            if isinstance(data.get("faq"), list):
                data["faq"] = [
                    {"q": str(f.get("q", "")), "a": str(f.get("a", ""))}
                    for f in data["faq"][:5] if isinstance(f, dict) and f.get("q") and f.get("a")
                ]
            else:
                data["faq"] = []
            return data
        except Exception:
            return {
                "meta_title": f"{product_name} — купить в Москве | StroiApp"[:70],
                "meta_description": (
                    f"{product_name}: купить с доставкой по Москве и МО. "
                    f"Опт и розница, безнал с НДС, отгрузка со склада в день заказа."
                )[:160],
                "seo_text": "",
                "faq": [],
            }

    async def generate_oc_seo(self, name: str, kind: str = "product",
                              info: str = "") -> dict:
        """SEO-пакет для родительского OpenCart stroiapp.ru (оптовый поставщик).
        Угол — B2B/опт/НДС/объекты, чтобы тексты НЕ дублировали moscow.stroiapp.ru.
        kind: 'product' | 'category'. Возвращает поля oc_*_description."""
        thing = "товара" if kind == "product" else "категории товаров"
        system = (
            "Ты — SEO-копирайтер оптового поставщика стройматериалов stroiapp.ru "
            "(Москва и Московская область). Позиционирование: база поставок для "
            "строительных компаний, прорабов, тендерных отделов и юрлиц. "
            "Безналичный расчёт с НДС, отгрузка со склада, поставка партиями на объекты, "
            "сертификаты и паспорта качества. Пиши деловым тоном про опт, объёмы, "
            "сроки поставки и документацию — БЕЗ розничных формулировок и без "
            "упоминания розничных цен в витринном стиле."
        )
        prompt = (
            f"Сделай SEO-пакет для страницы {thing} «{name}» оптового поставщика stroiapp.ru.\n"
            f"Данные: {info or 'нет'}\n\n"
            f"Ответь СТРОГО валидным JSON без markdown:\n"
            f'{{"description": "HTML 800-1200 знаков: 2 абзаца <p> + список <ul><li>. '
            f'Пиши: что это и для каких работ, фасовки/марки/объёмы партий, '
            f'условия поставки юрлицам (безнал с НДС, накладные, сертификаты), '
            f'доставка на объекты по Москве и МО. Только <p>, <ul>, <li>, <strong>. '
            f'Не начинай первое предложение с названия.", '
            f'"meta_title": "до 65 символов, формат «{name} оптом в Москве | Stroiapp.ru»", '
            f'"meta_description": "140-160 символов: назначение, опт, НДС, поставка на объект", '
            f'"meta_keyword": "5-7 ключевых фраз через запятую с акцентом на опт/Москва"}}'
        )
        import json as _json
        import re as _re
        try:
            raw = await self.chat(prompt, max_tokens=1400, temperature=0.7, system=system)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            match = _re.search(r"\{.*\}", raw, _re.DOTALL)
            data = _json.loads(match.group(0) if match else raw)
            return {
                "description": str(data.get("description", "")),
                "meta_title": str(data.get("meta_title") or name)[:250],
                "meta_description": str(data.get("meta_description", ""))[:250],
                "meta_keyword": str(data.get("meta_keyword", ""))[:250],
            }
        except Exception:
            return {
                "description": "",
                "meta_title": f"{name} оптом в Москве | Stroiapp.ru"[:65],
                "meta_description": (
                    f"{name}: оптовые поставки для юрлиц по Москве и МО, "
                    f"безнал с НДС, отгрузка со склада на объект."
                )[:160],
                "meta_keyword": "",
            }

    async def generate_product_attributes(self, product_name: str, category_name: str = "",
                                          existing: list[dict] | None = None) -> list[dict]:
        """Полный набор технических характеристик товара (как у famarket/Петрович):
        12-20 атрибутов [{name, text}] — расход, толщина слоя, время твердения,
        адгезия, температура применения и т.п. Значения с единицами измерения.
        Уже существующие атрибуты передаются модели — она их сохраняет и дополняет."""
        if not self.api_key:
            return []
        existing_txt = "; ".join(
            f"{a.get('name')}: {a.get('text')}" for a in (existing or []) if a.get("name")
        ) or "нет"
        system = (
            "Ты — специалист по строительным материалам, заполняешь карточку товара "
            "интернет-магазина. Знаешь техпараметры популярных брендов РФ (Knauf, Волма, "
            "Эталон, Ceresit, Weber, Litokol, Основит, Perfekta и др.). "
            "Отвечаешь СТРОГО валидным JSON, без markdown и пояснений."
        )
        prompt = (
            f"Товар: «{product_name}».\n"
            f"Категория: {category_name or 'нет'}.\n"
            f"Уже известные характеристики (сохранить как есть, не дублировать по имени): {existing_txt}\n\n"
            f"Составь полный список технических характеристик товара — 12-20 штук, "
            f"как на хороших строительных маркетах (famarket.ru, Петрович). "
            f"Для смесей типичные параметры: Бренд, Тип, Назначение, Состав/основа, "
            f"Толщина слоя (мм), Расход (кг/м² на 1 мм или на мешок), Расход воды (л/кг), "
            f"Жизнеспособность раствора (мин), Время твердения/высыхания (ч), "
            f"Адгезия (МПа), Прочность на сжатие (МПа), Морозостойкость (циклы), "
            f"Температура применения (°C), Температура эксплуатации, Цвет, Фактура, "
            f"Фасовка/упаковка, Вес (кг), Срок хранения (мес). "
            f"Для других товаров — релевантные параметры этого типа изделия.\n"
            f"Правила:\n"
            f"- Числовые параметры давай с единицами («7-50», «0,9 кг/м² при 1 мм», «80»), "
            f"единицы в самом значении, не в имени\n"
            f"- Бренд, модель, фасовку бери из названия товара и известных характеристик\n"
            f"- Если точное значение производителя не знаешь — давай типичное для этого класса продукта\n"
            f"- Никаких маркетинговых текстов, только «Имя: значение»\n"
            f"- Порядок: сначала общие (Бренд, Тип, Назначение), затем техпараметры, в конце упаковка/хранение\n\n"
            f"Ответь СТРОГО JSON-массивом: "
            f'[{{"name": "Толщина слоя", "text": "7-50 мм"}}, ...]'
        )
        import json as _json
        import re as _re
        try:
            raw = await self.chat(prompt, max_tokens=1800, temperature=0.3, system=system)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            match = _re.search(r"\[.*\]", raw, _re.DOTALL)
            data = _json.loads(match.group(0) if match else raw)
            out = []
            seen = set()
            for a in data if isinstance(data, list) else []:
                if not isinstance(a, dict):
                    continue
                name = str(a.get("name") or "").strip()
                text = str(a.get("text") or "").strip()
                if not name or not text or name.lower() in seen:
                    continue
                seen.add(name.lower())
                out.append({"name": name[:60], "text": text[:250]})
            return out[:25]
        except Exception:
            return []

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
