import httpx
import re
import json
from urllib.parse import urljoin
from html.parser import HTMLParser

from app.db.competitor_store import (
    add_competitor, add_price, get_comparison, list_competitors,
    save_competitor_products, get_competitor_product_stats,
)
from app.services.product_db import product_db


class SimpleHTMLParser:
    """Минимальный HTML-парсер для извлечения товаров без BeautifulSoup."""

    def __init__(self, html: str):
        self.html = html

    def extract_json_ld(self) -> list[dict]:
        """Извлекает structured data JSON-LD (schema.org Product)."""
        products = []
        pattern = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
        for match in pattern.finditer(self.html):
            try:
                data = json.loads(match.group(1).strip())
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "Product" or "Product" in item.get("@type", []):
                            products.append(self._normalize_jsonld(item))
                elif isinstance(data, dict):
                    if data.get("@type") == "Product" or "Product" in data.get("@type", []):
                        products.append(self._normalize_jsonld(data))
                    # Graph array
                    graph = data.get("@graph", [])
                    if isinstance(graph, list):
                        for g in graph:
                            if g.get("@type") == "Product":
                                products.append(self._normalize_jsonld(g))
            except (json.JSONDecodeError, AttributeError):
                continue
        return products

    def _normalize_jsonld(self, item: dict) -> dict:
        name = item.get("name", "")
        url = item.get("url", "")
        desc = item.get("description", "")
        image = ""
        if isinstance(item.get("image"), str):
            image = item["image"]
        elif isinstance(item.get("image"), list) and item["image"]:
            image = item["image"][0]
        price = None
        offers = item.get("offers")
        if isinstance(offers, dict):
            price = offers.get("price")
        elif isinstance(offers, list) and offers:
            price = offers[0].get("price")
        return {
            "product_name": name,
            "product_url": url,
            "description": desc[:200],
            "image_url": image,
            "price": float(price) if price is not None else None,
            "category": "",
            "keywords": name,
        }

    def extract_microdata(self) -> list[dict]:
        """Извлекает товары из microdata (itemprop)."""
        products = []
        # Простой поиск блоков с itemscope и itemtype Product
        blocks = re.findall(
            r'<([a-z0-9]+)[^>]*itemscope[^>]*itemtype=["\'][^"\']*Product[^"\']*["\'][^>]*>.*?</\1>',
            self.html, re.DOTALL | re.IGNORECASE
        )
        for block in blocks[:50]:
            name = self._extract_prop(block, "name")
            price_str = self._extract_prop(block, "price")
            desc = self._extract_prop(block, "description")
            image = self._extract_prop(block, "image")
            url = self._extract_link(block)
            price = None
            if price_str:
                price = self._parse_price(price_str)
            if name and price is not None:
                products.append({
                    "product_name": name,
                    "product_url": url,
                    "description": desc[:200],
                    "image_url": image,
                    "price": price,
                    "category": "",
                    "keywords": name,
                })
        return products

    def _extract_prop(self, html_block: str, prop: str) -> str:
        match = re.search(rf'itemprop=["\']{prop}["\'][^>]*>([^<]+)', html_block, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_link(self, html_block: str) -> str:
        match = re.search(r'href=["\']([^"\']+)["\']', html_block, re.IGNORECASE)
        return match.group(1) if match else ""

    def _parse_price(self, text: str) -> float | None:
        cleaned = re.sub(r'[^\d.,]', '', text.replace(' ', ''))
        cleaned = cleaned.replace(',', '.')
        if cleaned.count('.') > 1:
            # 1.234.56 -> remove last dot? no, assume Russian: 1 234,56
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        try:
            return float(cleaned)
        except ValueError:
            return None

    def extract_heuristic(self, base_url: str) -> list[dict]:
        """Heuristic парсинг: ищем блоки с ценами и названиями."""
        products = []
        # Паттерны цен: 1 234 ₽, 1234.56 ₽, 1 234.56 руб.
        price_pattern = re.compile(r'([\d\s]{2,10}(?:[,\.]\d{2})?)\s*(?:₽|руб|RUB|р\.|р\b)', re.IGNORECASE)
        # Ищем карточки товаров по типичным классам (расширенный список)
        card_patterns = [
            r'<div[^>]*class=["\'][^"\']*(?:product|item|card|goods|offer|catalog-item|product-card|product-item|shop-item|goods-item|offer-item|cat-item|catalog-item|product-card__info)[^"\']*["\'][^>]*>(.*?)</div>(?=\s*<div|\s*$|\s*<footer)',
            r'<article[^>]*>(.*?)</article>',
            r'<li[^>]*class=["\'][^"\']*(?:product|item|card)[^"\']*["\'][^>]*>(.*?)</li>',
            r'<div[^>]*class=["\'][^"\']*(?:col|column)[^"\']*["\'][^>]*>(.*?)</div>(?=\s*<div|\s*</div>)',
        ]
        seen_names = set()
        for pattern in card_patterns:
            for match in re.finditer(pattern, self.html, re.DOTALL | re.IGNORECASE):
                block = match.group(1)
                price_match = price_pattern.search(block)
                if not price_match:
                    continue
                price = self._parse_price(price_match.group(1))
                if price is None or price < 10 or price > 10_000_000:
                    continue
                # Ищем название
                name = ""
                # Сначала h2-h4
                name_match = re.search(r'<h[2-4][^>]*>([^<]+)</h[2-4]>', block, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    # Ссылка с текстом
                    link_match = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]{10,120})</a>', block, re.IGNORECASE)
                    if link_match:
                        name = link_match.group(2).strip()
                    else:
                        # div/span с class *title* или *name*
                        title_match = re.search(r'<(?:div|span)[^>]*class=["\'][^"\']*(?:title|name)[^"\']*["\'][^>]*>([^<]{5,120})</(?:div|span)>', block, re.IGNORECASE)
                        if title_match:
                            name = title_match.group(1).strip()
                if not name or len(name) < 5 or name in seen_names:
                    continue
                seen_names.add(name)
                # URL
                url = ""
                url_match = re.search(r'href=["\']([^"\']+)["\']', block, re.IGNORECASE)
                if url_match:
                    url = url_match.group(1)
                # Изображение
                img = ""
                img_match = re.search(r'<img[^>]*src=["\']([^"\']+)["\']', block, re.IGNORECASE)
                if img_match:
                    img = img_match.group(1)
                # Описание
                desc = ""
                desc_match = re.search(r'<p[^>]*>([^<]+)</p>', block, re.IGNORECASE | re.DOTALL)
                if desc_match:
                    desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()[:200]
                products.append({
                    "product_name": name,
                    "product_url": urljoin(base_url, url) if url else "",
                    "description": desc,
                    "image_url": urljoin(base_url, img) if img else "",
                    "price": price,
                    "category": "",
                    "keywords": name,
                })
                if len(products) >= 100:
                    break
            if len(products) >= 100:
                break

        # Fallback: если карточки не найдены, ищем пары "название + цена" по всему HTML
        if not products:
            price_matches = list(price_pattern.finditer(self.html))
            for pm in price_matches[:50]:
                price = self._parse_price(pm.group(1))
                if price is None or price < 10 or price > 10_000_000:
                    continue
                # Ищем название до цены (в пределах 500 символов назад)
                start = max(0, pm.start() - 500)
                context = self.html[start:pm.start()]
                name = ""
                # Ищем h2-h4 или ссылку перед ценой
                nm = re.search(r'<h[2-4][^>]*>([^<]+)</h[2-4]>\s*$', context, re.IGNORECASE)
                if nm:
                    name = nm.group(1).strip()
                else:
                    lm = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]{10,120})</a>\s*$', context, re.IGNORECASE)
                    if lm:
                        name = lm.group(2).strip()
                        url = lm.group(1)
                if name and len(name) >= 5 and name not in seen_names:
                    seen_names.add(name)
                    products.append({
                        "product_name": name,
                        "product_url": urljoin(base_url, url) if url else "",
                        "description": "",
                        "image_url": "",
                        "price": price,
                        "category": "",
                        "keywords": name,
                    })
                if len(products) >= 50:
                    break

        return products


class CompetitorSpy:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    def add(self, name: str, url: str = "") -> int:
        return add_competitor(name, url)

    def list(self) -> list[dict]:
        return list_competitors()

    async def scan_url(self, url: str) -> list[dict]:
        """Сканирует сайт конкурента и возвращает список товаров."""
        # Проверяем URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            # Увеличиваем таймаут и добавляем retry
            for attempt in range(2):
                try:
                    response = await self.client.get(url, timeout=30)
                    response.raise_for_status()
                    break
                except (httpx.ConnectTimeout, httpx.ReadTimeout):
                    if attempt == 0:
                        await __import__('asyncio').sleep(1)
                        continue
                    return [{"error": "Сайт не отвечает (таймаут). Возможно, сайт недоступен или защищён от ботов."}]
                except httpx.ConnectError:
                    return [{"error": f"Не удалось подключиться к сайту {url}. Проверьте URL или попробуйте позже."}]
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 403:
                        return [{"error": "Сайт блокирует доступ (403 Forbidden). Возможно, требуется защита от ботов."}]
                    if exc.response.status_code == 404:
                        return [{"error": "Страница не найдена (404). Проверьте URL сайта."}]
                    if exc.response.status_code >= 500:
                        return [{"error": f"Сервер конкурента временно недоступен ({exc.response.status_code})."}]
                    return [{"error": f"HTTP ошибка {exc.response.status_code} при запросе к сайту."}]
            else:
                return [{"error": "Не удалось получить ответ от сайта после повторных попыток."}]

            html = response.text
            base_url = str(response.url)
            parser = SimpleHTMLParser(html)
            # Пробуем JSON-LD (самый точный)
            products = parser.extract_json_ld()
            if not products:
                products = parser.extract_microdata()
            if not products:
                products = parser.extract_heuristic(base_url)
            # Дедупликация
            seen = set()
            unique = []
            for p in products:
                key = (p.get("product_name", ""), p.get("price"))
                if key not in seen:
                    seen.add(key)
                    unique.append(p)
            return unique[:100]
        except Exception as exc:
            return [{"error": f"Ошибка при сканировании: {str(exc)[:200]}"}]

    async def scan_competitor(self, competitor_id: int, url: str) -> dict:
        """Полное сканирование конкурента: товары + статистика."""
        products = await self.scan_url(url)
        if products and "error" in products[0]:
            return {"error": products[0]["error"]}
        imported = save_competitor_products(competitor_id, products)
        stats = get_competitor_product_stats(competitor_id)
        return {
            "status": "ok",
            "items_found": len(products),
            "imported": imported,
            "stats": stats,
        }

    def add_manual_prices(self, competitor_id: int, prices: list[dict]) -> dict:
        imported = 0
        for item in prices:
            sku = item.get("sku", "").strip()
            if not sku:
                continue
            add_price(competitor_id, sku, item.get("name", ""), float(item.get("price", 0)))
            imported += 1
        return {"imported": imported}

    def compare(self) -> list[dict]:
        our_products = {p.sku: p for p in product_db.list_products()}
        comp_data = get_comparison()
        results = []
        for row in comp_data:
            sku = row["sku"]
            our = our_products.get(sku)
            if our:
                diff = round(row["competitor_price"] - our.retail_price, 2)
                diff_pct = round((diff / our.retail_price) * 100, 1) if our.retail_price else 0
                results.append({
                    "sku": sku,
                    "name": our.name,
                    "our_price": our.retail_price,
                    "competitor_price": row["competitor_price"],
                    "competitor_name": row["competitor_name"],
                    "diff": diff,
                    "diff_pct": diff_pct,
                })
        return sorted(results, key=lambda x: x["diff_pct"], reverse=True)

    POPULAR_BUILDING_STORES = [
        {"domain": "stroimaterialy.ru", "url": "https://stroimaterialy.ru", "name": "Стройматериалы.ру"},
        {"domain": "vseinstrumenti.ru", "url": "https://vseinstrumenti.ru", "name": "ВсеИнструменты"},
        {"domain": "220-volt.ru", "url": "https://220-volt.ru", "name": "220 Вольт"},
        {"domain": "leroymerlin.ru", "url": "https://leroymerlin.ru", "name": "Леруа Мерлен"},
        {"domain": "obi.ru", "url": "https://obi.ru", "name": "OBI"},
        {"domain": "petrovich.ru", "url": "https://petrovich.ru", "name": "Петрович"},
        {"domain": "maxidom.ru", "url": "https://maxidom.ru", "name": "Максидом"},
        {"domain": "stroybaza.ru", "url": "https://stroybaza.ru", "name": "СтройБаза"},
        {"domain": "stms.ru", "url": "https://stms.ru", "name": "Стройматериалы СТМС"},
        {"domain": "1001materik.ru", "url": "https://1001materik.ru", "name": "1001 Материк"},
        {"domain": "moscowbuilder.ru", "url": "https://moscowbuilder.ru", "name": "Московский строитель"},
        {"domain": "tdkm.ru", "url": "https://tdkm.ru", "name": "ТД Кирпич и Материалы"},
        {"domain": "kirpich.ru", "url": "https://kirpich.ru", "name": "Кирпич.ру"},
        {"domain": "santeh-import.ru", "url": "https://santeh-import.ru", "name": "СантехИмпорт"},
        {"domain": "stroypark.su", "url": "https://stroypark.su", "name": "СтройПарк"},
        {"domain": "master-dom.ru", "url": "https://master-dom.ru", "name": "Мастер Дом"},
        {"domain": "domstroy.pro", "url": "https://domstroy.pro", "name": "ДомСтрой"},
        {"domain": "moskva-sbm.ru", "url": "https://moskva-sbm.ru", "name": "СБМ Москва"},
        {"domain": "tool.ru", "url": "https://tool.ru", "name": "Tool.ru"},
        {"domain": "instrument-msk.ru", "url": "https://instrument-msk.ru", "name": "Инструменты Москва"},
        {"domain": "gipsokarton.ru", "url": "https://gipsokarton.ru", "name": "Гипсокартон.ру"},
        {"domain": "profnastil-msk.ru", "url": "https://profnastil-msk.ru", "name": "Профнастил Москва"},
        {"domain": "siding-msk.ru", "url": "https://siding-msk.ru", "name": "Сайдинг Москва"},
        {"domain": "krovlya.ru", "url": "https://krovlya.ru", "name": "Кровля.ру"},
        {"domain": "teplodom.ru", "url": "https://teplodom.ru", "name": "ТеплоДом"},
        {"domain": "shtukaturka.ru", "url": "https://shtukaturka.ru", "name": "Штукатурка.ру"},
    ]

    async def discover_competitors(self, query: str, max_results: int = 30) -> list[dict]:
        """Возвращает конкурентов из предзаполненного списка (без парсинга Яндекса — безопасно)."""
        all_domains = []
        seen = set()

        for store in self.POPULAR_BUILDING_STORES[:max_results]:
            if store["domain"] not in seen:
                seen.add(store["domain"])
                all_domains.append(store)

        return all_domains

    async def auto_discover_and_scan(self, query: str, max_competitors: int = 5) -> dict:
        """Автоматически находит конкурентов, добавляет их в базу и сканирует."""
        discovered = await self.discover_competitors(query, max_results=max_competitors + 5)
        if discovered and "error" in discovered[0]:
            return {"error": discovered[0]["error"]}

        added = []
        scanned = []
        for item in discovered[:max_competitors]:
            domain = item["domain"]
            url = item["url"]
            # Проверяем, есть ли уже
            existing = [c for c in list_competitors() if c.get("url", "").replace("www.", "").replace("https://", "").replace("http://", "").startswith(domain)]
            if existing:
                continue
            comp_id = add_competitor(domain, url)
            added.append({"id": comp_id, "name": domain, "url": url})
            # Сканируем товары
            scan_result = await self.scan_competitor(comp_id, url)
            scanned.append({"id": comp_id, "name": domain, "scan": scan_result})

        return {
            "status": "ok",
            "query": query,
            "found": len(discovered),
            "added": len(added),
            "competitors": added,
            "scanned": scanned,
        }

    async def close(self):
        await self.client.aclose()


competitor_spy = CompetitorSpy()
