import httpx
import json
import re
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.product_db import product_db
from app.services.deepseek_client import deepseek_client


class TenderMonitor:
    """Мониторинг выигранных тендеров по нашим товарам.
    Источники: TenderGuru API + DaMIA API + B2B-Center (парсинг).
    Находит победителей, сопоставляет позиции с нашей базой, готовит КП."""

    def __init__(self):
        self.api_code = settings.tenderguru_api_code
        self.base_url = "https://www.tenderguru.ru/api2.3/export/contracts"
        self.damia_key = settings.damia_api_key
        self.damia_url = "https://api.damia.ru/api-zakupki/v1/contracts"
        self.b2b_url = "https://www.b2b-center.ru/market/search/"
        self.client = httpx.AsyncClient(timeout=30.0)

    def _get_search_keywords(self) -> list[str]:
        """Генерирует ключевые слова из наших товаров для поиска тендеров."""
        products = product_db.list_products()
        keywords = set()
        for p in products[:100]:
            name = (p.name or "").strip()
            if not name or len(name) < 5:
                continue
            # Очищаем от артикулов, брендов в скобках
            clean = re.sub(r'\(.*?\)', '', name).strip()
            # Берём 2-3 главных слова
            words = clean.split()
            if len(words) >= 2:
                keywords.add(" ".join(words[:2]))
            if len(keywords) >= 100:
                break
        return list(keywords)[:100]

    async def find_won_tenders(self, days: int = 7, keywords: list[str] | None = None) -> list[dict]:
        """Ищет выигранные тендеры из всех источников: TenderGuru + DaMIA + B2B-Center."""
        if not keywords:
            keywords = self._get_search_keywords()

        all_contracts = []
        seen_ids = set()

        # Источник 1: TenderGuru
        if self.api_code:
            tg_contracts = await self._find_tenderguru(days, keywords)
            for c in tg_contracts:
                cid = f"tg-{c.get('id') or c.get('contract_idx')}"
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    c["_source"] = "tenderguru"
                    all_contracts.append(c)

        # Источник 2: DaMIA API
        if self.damia_key:
            dm_contracts = await self._find_damia(days, keywords)
            for c in dm_contracts:
                cid = f"dm-{c.get('id') or c.get('regnum')}"
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    c["_source"] = "damia"
                    all_contracts.append(c)

        # Источник 3: B2B-Center (парсинг)
        b2b_contracts = await self._find_b2b_center(days, keywords)
        for c in b2b_contracts:
            cid = f"b2b-{c.get('id')}"
            if cid not in seen_ids:
                seen_ids.add(cid)
                c["_source"] = "b2b-center"
                all_contracts.append(c)

        if not all_contracts:
            return [{"error": "Не найдено тендеров. Проверьте tenderguru_api_code или damia_api_key."}]

        return all_contracts[:200]

    async def _find_tenderguru(self, days: int, keywords: list[str]) -> list[dict]:
        """Поиск через TenderGuru API."""
        date_start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_end = datetime.now().strftime("%Y-%m-%d")
        contracts = []

        for kw in keywords[:50]:
            try:
                params = {
                    "kwords": kw,
                    "date_start": date_start,
                    "date_end": date_end,
                    "dtype": "json",
                    "is_actual": 1,
                    "api_code": self.api_code,
                    "fz": 44,
                }
                resp = await self.client.get(self.base_url, params=params)
                data = resp.json()

                items = data.get("contracts", data.get("data", []))
                if isinstance(items, list):
                    contracts.extend(items)
            except Exception:
                continue

        return contracts

    async def _find_damia(self, days: int, keywords: list[str]) -> list[dict]:
        """Поиск через DaMIA API (api-zakupki/v1/contracts)."""
        date_start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        contracts = []

        for kw in keywords[:30]:
            try:
                params = {
                    "key": self.damia_key,
                    "q": kw,
                    "from_date": date_start,
                    "status": "completed",
                    "fz": "44,223",
                }
                resp = await self.client.get(self.damia_url, params=params)
                data = resp.json()

                items = data.get("contracts", data.get("data", []))
                if isinstance(items, list):
                    for item in items:
                        # Нормализуем под формат TenderGuru
                        contracts.append({
                            "id": item.get("id") or item.get("regnum"),
                            "name": item.get("name") or item.get("title", ""),
                            "winner_name": item.get("winner_name") or item.get("participant_winner", ""),
                            "winner_inn": item.get("winner_inn", ""),
                            "winner_email": item.get("winner_email", ""),
                            "winner_phone": item.get("winner_phone", ""),
                            "price": item.get("price") or item.get("contract_price", 0),
                            "customer_name": item.get("customer_name") or item.get("customer", ""),
                            "region": item.get("region", ""),
                            "fz": item.get("fz", ""),
                            "notificationNumber": item.get("notificationNumber", ""),
                            "signed_date": item.get("sign_date", ""),
                            "products": item.get("products", []),
                        })
            except Exception:
                continue

        return contracts

    async def _find_b2b_center(self, days: int, keywords: list[str]) -> list[dict]:
        """Парсинг B2B-Center через HTTP (без Playwright — проще и быстрее)."""
        contracts = []
        date_start = (datetime.now() - timedelta(days=days)).strftime("%d.%m.%Y")

        for kw in keywords[:15]:
            try:
                # B2B-Center поиск через их API/search endpoint
                resp = await self.client.post(
                    "https://www.b2b-center.ru/api/v1/tenders/search",
                    json={
                        "keywords": kw,
                        "date_from": date_start,
                        "status": "completed",
                        "per_page": 20,
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json",
                    },
                    timeout=15.0,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                items = data.get("tenders", data.get("data", []))
                if not isinstance(items, list):
                    continue

                for item in items:
                    contracts.append({
                        "id": item.get("id"),
                        "name": item.get("title") or item.get("name", ""),
                        "winner_name": item.get("winner") or item.get("winner_name", ""),
                        "winner_inn": item.get("winner_inn", ""),
                        "winner_email": item.get("winner_email", ""),
                        "price": item.get("price") or item.get("budget", 0),
                        "customer_name": item.get("customer") or item.get("organizer", ""),
                        "region": item.get("region", "Москва"),
                        "fz": "коммерческий",
                        "notificationNumber": item.get("number", ""),
                        "signed_date": item.get("date_end", ""),
                        "products": item.get("items", []),
                    })
            except Exception:
                continue

        return contracts

    def extract_winner_info(self, contract: dict) -> dict:
        """Извлекает информацию о победителе из контракта."""
        return {
            "winner_name": contract.get("winner_name") or contract.get("winner") or "",
            "winner_inn": contract.get("winner_inn") or "",
            "winner_email": contract.get("winner_email") or "",
            "winner_phone": contract.get("winner_phone") or "",
            "contract_id": contract.get("id") or contract.get("contract_idx"),
            "contract_number": contract.get("num") or contract.get("regnum") or "",
            "contract_price": float(contract.get("price") or contract.get("contract_price") or 0),
            "customer_name": contract.get("customer_name") or contract.get("customer") or "",
            "fz": contract.get("fz", ""),
            "region": contract.get("region") or "",
            "tender_number": contract.get("notificationNumber") or contract.get("tend_num") or "",
            "sign_date": contract.get("signed_date") or contract.get("sign_date") or "",
        }

    def match_tender_to_products(self, contract: dict) -> dict:
        """Сопоставляет позиции тендера с нашими товарами."""
        # Извлекаем текст позиций из контракта
        items_text = ""
        products_field = contract.get("products") or contract.get("contract_products") or []
        if isinstance(products_field, list):
            items_text = " ".join(str(p.get("name", p) if isinstance(p, dict) else p) for p in products_field)
        elif isinstance(products_field, str):
            items_text = products_field

        # Также проверяем название тендера
        tender_name = contract.get("name") or contract.get("tender_name") or ""
        search_text = f"{tender_name} {items_text}".lower()

        our_products = product_db.list_products()
        matched = []
        for p in our_products:
            name = (p.name or "").lower()
            if not name or len(name) < 5:
                continue
            # Проверяем совпадение по ключевым словам товара
            name_words = name.split()
            if len(name_words) >= 2:
                key_phrase = " ".join(name_words[:2])
                if key_phrase in search_text:
                    matched.append({
                        "sku": p.sku,
                        "name": p.name,
                        "retail_price": p.retail_price,
                        "wholesale_price": getattr(p, "wholesale_price", None),
                        "cost_price": p.cost_price_cash or p.cost_price_cashless,
                        "margin": p.retail_price - (p.cost_price_cash or p.cost_price_cashless or 0),
                        "url": f"https://stroiapp.ru/index.php?route=product/product&product_id={p.sku}",
                    })

        return {
            "matched_count": len(matched),
            "matched_products": matched[:50],
            "tender_text": search_text[:500],
        }

    async def detect_building_type(self, contract: dict) -> dict:
        """DeepSeek определяет тип здания по тексту тендера."""
        tender_name = contract.get("name") or contract.get("tender_name") or ""
        items_text = ""
        products_field = contract.get("products") or contract.get("contract_products") or []
        if isinstance(products_field, list):
            items_text = " ".join(str(p.get("name", p) if isinstance(p, dict) else p) for p in products_field)
        elif isinstance(products_field, str):
            items_text = products_field
        customer = contract.get("customer_name") or contract.get("customer") or ""
        full_text = f"{tender_name} {customer} {items_text}".strip()

        if not full_text:
            return {"building_type": "неизвестно", "building_subtype": "", "area_m2": 0, "floors": 0}

        system = (
            "Ты — инженер-сметчик. Анализируешь текст тендера и определяешь тип здания, "
            "примерную площадь, этажность и какие стройматериалы нужны. "
            "Отвечай ТОЛЬКО в формате JSON."
        )
        prompt = (
            f"Текст тендера: {full_text[:1000]}\n\n"
            f"Определи:\n"
            f"1. building_type — тип здания (школа, детский сад, поликлиника, больница, "
            f"жилой дом, офисное здание, склад, торговый центр, спортивный объект, административное)\n"
            f"2. building_subtype — подтип (например: школа на 500 мест, детсад на 120 мест)\n"
            f"3. area_m2 — примерная площадь здания в м² (число)\n"
            f"4. floors — этажность (число)\n\n"
            f"Формат JSON:\n"
            f'{{"building_type":"...","building_subtype":"...","area_m2":0,"floors":0}}\n'
            f"Только JSON."
        )

        response = await deepseek_client.chat(prompt, max_tokens=400, temperature=0.2, system=system)

        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                parsed = json.loads(response)
        except (json.JSONDecodeError, ValueError):
            parsed = {"building_type": "неизвестно", "building_subtype": "", "area_m2": 0, "floors": 0}

        return parsed

    async def calculate_estimate(
        self,
        building: dict,
        matched_products: list[dict],
    ) -> dict:
        """DeepSeek рассчитывает примерную смету: количество и стоимость материалов."""
        if not matched_products:
            return {"items": [], "total": 0}

        products_text = "\n".join(
            f"- {p['name']} (цена: {p['retail_price']}₽, опт: {p.get('wholesale_price') or 'по запросу'}₽)"
            for p in matched_products[:30]
        )

        system = (
            "Ты — инженер-сметчик. Рассчитываешь примерную потребность в стройматериалах "
            "на основе типа здания, площади и этажности. "
            "Учитывай СНиП и типовые нормы расхода. "
            "Отвечай ТОЛЬКО в формате JSON."
        )
        prompt = (
            f"Тип здания: {building.get('building_type', 'неизвестно')}\n"
            f"Подтип: {building.get('building_subtype', '')}\n"
            f"Площадь: {building.get('area_m2', 0)} м²\n"
            f"Этажность: {building.get('floors', 1)}\n\n"
            f"Наши товары (нужно рассчитать количество для этого здания):\n{products_text}\n\n"
            f"Рассчитай примерное количество каждого товара для строительства/ремонта этого здания.\n"
            f"Учитывай площадь, этажность, тип помещения.\n\n"
            f"Формат JSON:\n"
            f'{{"items":[{{"name":"...","quantity":0,"unit":"шт/м²/м³","price_per_unit":0,"total_price":0}}],"total":0}}\n'
            f"Только JSON."
        )

        response = await deepseek_client.chat(prompt, max_tokens=1000, temperature=0.3, system=system)

        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                parsed = json.loads(response)
        except (json.JSONDecodeError, ValueError):
            parsed = {"items": [], "total": 0}

        return parsed

    async def generate_kp_for_winner(
        self,
        winner: dict,
        matched_products: list[dict],
        building: dict | None = None,
        estimate: dict | None = None,
    ) -> dict:
        """DeepSeek генерирует КП для победителя со сметой по типу здания."""
        if not matched_products:
            return {"error": "Нет совпадений с нашими товарами"}

        # Формируем текст товаров со сметой
        if estimate and estimate.get("items"):
            items_lines = []
            for item in estimate["items"]:
                items_lines.append(
                    f"- {item.get('name', '')}: {item.get('quantity', 0)} {item.get('unit', '')} "
                    f"× {item.get('price_per_unit', 0)}₽ = {item.get('total_price', 0)}₽"
                )
            products_text = "\n".join(items_lines)
            estimate_total = estimate.get("total", 0)
        else:
            products_text = "\n".join(
                f"- {p['name']}: {p['retail_price']}₽ (опт: {p.get('wholesale_price', 'по запросу')}₽)"
                for p in matched_products[:20]
            )
            estimate_total = sum(p["retail_price"] for p in matched_products[:20])

        building_info = ""
        if building:
            building_info = (
                f"Тип здания: {building.get('building_type', 'неизвестно')}\n"
                f"Подтип: {building.get('building_subtype', '')}\n"
                f"Площадь: {building.get('area_m2', 0)} м²\n"
                f"Этажность: {building.get('floors', 1)}\n\n"
            )

        system = (
            "Ты — менеджер по продажам строительного магазина stroiapp.ru. "
            "Пишешь коммерческое предложение поставщику, который выиграл тендер "
            "и теперь нуждается в закупке стройматериалов. "
            "Тон: профессиональный, дружелюбный, конкретный. "
            "Предлагай оптовые цены, доставку, отсрочку платежа. "
            "В КП указывай конкретное количество товаров и итоговую сумму."
        )
        prompt = (
            f"Победитель тендера: {winner.get('winner_name', '')}\n"
            f"ИНН: {winner.get('winner_inn', '')}\n"
            f"Заказчик: {winner.get('customer_name', '')}\n"
            f"Сумма контракта: {winner.get('contract_price', 0)}₽\n"
            f"Регион: {winner.get('region', 'Москва')}\n\n"
            f"{building_info}"
            f"Примерная смета по нашим товарам:\n{products_text}\n"
            f"Итого по смете: {estimate_total}₽\n\n"
            f"Напиши коммерческое предложение:\n"
            f"1. Тема письма\n"
            f"2. Обращение (Уважаемый ...)\n"
            f"3. Суть: мы поставщик стройматериалов, знаем что вы выиграли тендер "
            f"на {building.get('building_type', 'объект') if building else 'объект'}, "
            f"можем поставить материалы по оптовым ценам\n"
            f"4. Таблица товаров с количеством и ценами (из сметы)\n"
            f"5. Условия: доставка по Москве и МО, отсрочка, НДС\n"
            f"6. Призыв к действию\n"
            f"7. Подпись с контактами\n\n"
            f"Формат JSON:\n"
            f'{{"subject":"...","body":"..."}}\n'
            f"Только JSON."
        )

        response = await deepseek_client.chat(prompt, max_tokens=1500, temperature=0.4, system=system)

        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                parsed = json.loads(response)
        except (json.JSONDecodeError, ValueError):
            parsed = {"subject": "Поставка стройматериалов — StroiApp.ru", "body": response}

        return {
            "subject": parsed.get("subject", "Поставка стройматериалов — StroiApp.ru"),
            "body": parsed.get("body", ""),
            "winner": winner,
            "building": building,
            "estimate": estimate,
            "products_offered": matched_products[:20],
            "total_estimate": estimate_total,
        }

    async def send_kp_email(self, kp: dict, to_email: str) -> dict:
        """Отправляет КП на email победителя через SMTP."""
        if not settings.smtp_host or not settings.smtp_user:
            return {"status": "skipped", "reason": "SMTP не настроен"}
        if not to_email:
            return {"status": "skipped", "reason": "нет email победителя"}

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = kp.get("subject", "Поставка стройматериалов — StroiApp.ru")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
        msg["To"] = to_email

        body = kp.get("body", "")
        html_body = body.replace("\n", "<br>\n")
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(f"<html><body>{html_body}</body></html>", "html", "utf-8"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            return {"status": "sent", "to": to_email}
        except Exception as exc:
            return {"status": "error", "reason": str(exc)}

    async def monitor_and_send(self, days: int = 7, auto_send: bool = False) -> dict:
        """Полный цикл: найти выигранные тендеры → определить здание → смета → КП → отправить."""
        tenders = await self.find_won_tenders(days=days)
        if tenders and isinstance(tenders[0], dict) and "error" in tenders[0]:
            return tenders[0]

        results = []
        for contract in tenders[:100]:
            winner = self.extract_winner_info(contract)
            match = self.match_tender_to_products(contract)
            if match["matched_count"] == 0:
                continue

            # Определяем тип здания
            building = await self.detect_building_type(contract)

            # Рассчитываем смету
            estimate = await self.calculate_estimate(building, match["matched_products"])

            # Генерируем КП со сметой
            kp = await self.generate_kp_for_winner(
                winner, match["matched_products"], building=building, estimate=estimate
            )
            kp["matched_count"] = match["matched_count"]

            if auto_send and winner.get("winner_email"):
                send_result = await self.send_kp_email(kp, winner["winner_email"])
                kp["send_result"] = send_result
            else:
                kp["send_result"] = {"status": "not_sent", "reason": "auto_send=False or no email"}

            results.append(kp)

        return {
            "status": "ok",
            "tenders_scanned": len(tenders),
            "matched_tenders": len(results),
            "results": results,
        }

    async def close(self):
        await self.client.aclose()


tender_monitor = TenderMonitor()
