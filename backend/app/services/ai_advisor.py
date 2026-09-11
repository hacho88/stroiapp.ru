import json
import re

from app.db.competitor_store import get_all_competitor_products_for_ai
from app.services.product_db import product_db
from app.services.deepseek_client import deepseek_client


class AIAdvisor:
    """AI-советник по рекламе: анализирует конкурентов и рекомендует товары/ключи/ставки."""

    def __init__(self) -> None:
        pass

    def get_our_profitable_products(self, min_roi: int = 100) -> list[dict]:
        """Возвращает наши товары с ROI >= min_roi, отсортированные по прибыли."""
        products = product_db.list_products()
        result = []
        for p in products:
            cost = p.cost_price_cash or p.cost_price_cashless or 0
            margin = (p.retail_price - cost) if p.retail_price else 0
            if margin > 0:
                roi = round((margin / max(cost, 1)) * 100, 1)
                if roi >= min_roi:
                    result.append({
                        "sku": p.sku,
                        "name": p.name,
                        "retail_price": p.retail_price,
                        "cost_price": cost,
                        "margin": round(margin, 2),
                        "roi": roi,
                        "wholesale_price": p.wholesale_price,
                    })
        return sorted(result, key=lambda x: x["margin"], reverse=True)

    def get_competitor_hot_products(self, limit: int = 100) -> list[dict]:
        """Возвращает товары конкурентов, которые чаще всего встречаются (потенциально ходовые)."""
        products = get_all_competitor_products_for_ai(limit=limit)
        # Группируем по похожим названиям
        groups = {}
        for p in products:
            name = p.get("product_name", "")
            key = self._normalize_name(name)
            if key not in groups:
                groups[key] = {"names": [], "prices": [], "competitors": set()}
            groups[key]["names"].append(name)
            if p.get("price"):
                groups[key]["prices"].append(p["price"])
            groups[key]["competitors"].add(p.get("competitor_name", ""))
        result = []
        for key, data in groups.items():
            if len(data["names"]) >= 2:  # Хотя бы 2 упоминания
                avg_price = round(sum(data["prices"]) / len(data["prices"]), 2) if data["prices"] else None
                result.append({
                    "product_key": key,
                    "mentions": len(data["names"]),
                    "competitors_count": len(data["competitors"]),
                    "sample_names": list(set(data["names"]))[:3],
                    "avg_competitor_price": avg_price,
                })
        return sorted(result, key=lambda x: x["mentions"], reverse=True)[:50]

    def _normalize_name(self, name: str) -> str:
        """Нормализует название товара для группировки."""
        lowered = name.lower()
        # Убираем размеры, объёмы, числа
        lowered = re.sub(r'\b\d+[\.,]?\d*\s*(мм|м|кг|л|шт|м2|м³|г|т)\b', '', lowered)
        lowered = re.sub(r'\b\d+[\.,]?\d*\b', '', lowered)
        # Убираем марки в скобках
        lowered = re.sub(r'\([^)]*\)', '', lowered)
        # Убираем частые слова
        for word in ["купить", "цена", "москва", "оптом", "в", "и", "с", "для", "по"]:
            lowered = lowered.replace(word, "")
        # Берём первые 2-3 значимых слова
        words = [w for w in lowered.split() if len(w) > 3]
        return " ".join(words[:3]).strip()

    async def generate_ad_recommendations(self, top_n: int = 10) -> dict:
        """Генерирует AI-рекомендации по рекламе на основе анализа конкурентов и наших товаров."""
        our_products = self.get_our_profitable_products(min_roi=80)[:30]
        comp_hot = self.get_competitor_hot_products(limit=200)

        if not our_products:
            return {"error": "Нет данных о наших товарах"}

        # Формируем промпт для DeepSeek
        our_text = "\n".join(
            f"- {p['name']} (SKU: {p['sku']}), розница {p['retail_price']}₽, себестоимость {p['cost_price']}₽, маржа {p['margin']}₽"
            for p in our_products[:15]
        )
        comp_text = "\n".join(
            f"- {h['product_key']}, упоминается у {h['mentions']} конкурентов, средняя цена конкурентов {h['avg_competitor_price']}₽"
            for h in comp_hot[:15]
        )

        system = (
            "Ты — эксперт по контекстной рекламе Яндекс Директ для строительного магазина в Москве. "
            "Давай только конкретные, actionable рекомендации. Не пиши воду."
        )
        prompt = (
            f"Проанализируй наши товары и товары конкурентов. Рекомендуй, на что запускать рекламу в Яндекс Директ.\n\n"
            f"НАШИ ПРИБЫЛЬНЫЕ ТОВАРЫ (розничная цена, себестоимость, маржа):\n{our_text}\n\n"
            f"ХОДОВЫЕ ТОВАРЫ КОНКУРЕНТОВ (часто встречаются на их сайтах):\n{comp_text}\n\n"
            f"Задача:\n"
            f"1. Выбери ТОП-{top_n} товаров для рекламы — те, где у нас ВЫСОКАЯ маржа И конкуренты тоже продают (значит есть спрос).\n"
            f"2. Для каждого товара подбери 3-5 нишевых ключевых фраз (не общие 'гипсокартон', а точные 'гипсокартон кнауф 12.5 мм 2500х1200 цена').\n"
            f"3. Оцени рекомендуемую ставку CPC (₽) для каждой фразы — основываясь на марже товара (чем выше маржа, тем выше можем ставить).\n"
            f"4. Посчитай ожидаемый ROI для каждого товара при ставке CPC.\n"
            f"5. Укажи, если наш товар дешевле конкурентов — это аргумент для объявления.\n\n"
            f"Формат ответа — строго JSON массив объектов:\n"
            f'[{{"sku":"...","product_name":"...","keywords":["...","..."],"recommended_cpc":45,"expected_roi":180,"why":"..."}}]\n'
            f"Только JSON, без текста до или после."
        )

        response = await deepseek_client.chat(prompt, max_tokens=1200, temperature=0.3, system=system)
        recommendations = self._parse_json_response(response)
        return {
            "status": "ok",
            "recommendations": recommendations,
            "our_products_count": len(our_products),
            "competitor_hot_count": len(comp_hot),
            "raw_ai": response[:500],
        }

    async def analyze_keywords(self, product_name: str) -> dict:
        """AI анализирует название товара и предлагает ключевые слова для рекламы."""
        system = "Ты — специалист по семантике Яндекс Директ. Давай ключевые слова для строительных материалов."
        prompt = (
            f"Товар: {product_name}\n\n"
            f"Подбери ключевые фразы для Яндекс Директ:\n"
            f"1. Точные фразы (3-5 слов) — низкая конкуренция, дешёвый клик\n"
            f"2. Широкие фразы (1-2 слова) — высокий спрос, дорогой клик\n"
            f"3. Минус-слова (что исключить)\n\n"
            f"Формат JSON: {{'exact':['...'], 'broad':['...'], 'negative':['...']}}"
        )
        response = await deepseek_client.chat(prompt, max_tokens=400, temperature=0.3, system=system)
        return {"product": product_name, "keywords": self._parse_json_response(response), "raw": response[:300]}

    def _parse_json_response(self, text: str) -> list | dict:
        """Парсит JSON из ответа AI, обрабатывает markdown-блоки."""
        try:
            # Пробуем найти JSON в markdown
            match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Пробуем найти JSON напрямую
            match = re.search(r'(\[.*?\]|\{.*?\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Fallback
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return []


ai_advisor = AIAdvisor()
