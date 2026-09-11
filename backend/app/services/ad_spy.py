import re
import httpx
from urllib.parse import urlparse

from app.db.competitor_store import (
    list_competitors,
    save_competitor_ads,
    get_competitor_ads,
    get_ads_stats,
)


class AdSpy:
    """Анализ рекламной стратегии конкурентов. БЕЗ парсинга выдачи Яндекса — безопасно."""

    def __init__(self):
        pass

    async def fetch_ads_for_keyword(self, keyword: str, pages: int = 1) -> list[dict]:
        """Отключено: парсинг выдачи Яндекса небезопасен (блокировка IP)."""
        return []

    def _parse_ads_from_html(self, html: str, keyword: str) -> list[dict]:
        """Парсит HTML выдачи Яндекса и извлекает рекламные объявления."""
        ads = []

        # Рекламные блоки в Яндексе обычно имеют классы:
        # .SerpItem_type_direct для верхних/боковых объявлений
        # .Organs для органики (пропускаем)
        # Парсим различные варианты разметки

        # Вариант 1: Классический direct (старая разметка)
        direct_blocks = re.findall(
            r'<li[^>]*class="[^"]*?(?:direct|ads|Ad)[^"]*?"[^>]*>(.*?)</li>',
            html, re.S | re.I
        )
        for block in direct_blocks:
            ad = self._extract_ad_from_block(block, keyword)
            if ad:
                ads.append(ad)

        # Вариант 2: Новые рекламные блоки (различные data-атрибуты)
        # Ищем ссылки с метками рекламы
        ad_links = re.findall(
            r'<a[^>]*?href="([^"]*?)"[^>]*?>(.*?)</a>',
            html, re.S
        )
        for url, text in ad_links:
            # Проверяем, является ли ссылка рекламной
            if self._is_ad_url(url):
                ad = self._extract_ad_from_link(url, text, keyword, html)
                if ad and ad not in ads:
                    ads.append(ad)

        # Вариант 3: Ищем блоки с метками "реклама" или "ad"
        ad_labels = re.findall(
            r'(?:Реклама|реклама|Ad|Ads|Sponsored)[^<]*</span>.*?<a[^>]*?href="([^"]*?)"[^>]*?>(.*?)</a>',
            html, re.S | re.I
        )
        for url, text in ad_labels:
            if self._is_ad_url(url):
                ad = self._extract_ad_from_link(url, text, keyword, html)
                if ad and ad not in ads:
                    ads.append(ad)

        # Вариант 4: Ищем по URL-паттернам Яндекс Директа
        ya_direct_links = re.findall(
            r'https?://yandex\.ru/clck/[^"\'\s]+',
            html
        )
        for url in ya_direct_links:
            ad = self._extract_ad_from_direct_url(url, keyword, html)
            if ad and ad not in ads:
                ads.append(ad)

        return ads

    def _is_ad_url(self, url: str) -> bool:
        """Проверяет, является ли URL рекламным (исключаем органику)."""
        if not url:
            return False
        url_lower = url.lower()
        # Исключаем обычные результаты поиска
        if "yandex.ru/search" in url_lower or "yandex.com/search" in url_lower:
            return False
        if url_lower.startswith("/"):
            return False
        # Включаем рекламные ссылки
        if "yandex.ru/clck" in url_lower or "yandex.com/clck" in url_lower:
            return True
        if "direct.yandex.ru" in url_lower:
            return True
        # Внешние ссылки с метками UTM или другими рекламными метками
        if any(x in url_lower for x in ["utm_", "yclid", "gclid", "yad"]):
            return True
        return True

    def _extract_ad_from_block(self, block_html: str, keyword: str) -> dict | None:
        """Извлекает данные объявления из HTML-блока."""
        # Заголовок
        title_match = re.search(r'<a[^>]*?>(.*?)</a>', block_html, re.S)
        title = self._clean_html(title_match.group(1)) if title_match else ""

        # Текст объявления
        text_match = re.search(r'<span[^>]*?class="[^"]*?text[^"]*?"[^>]*>(.*?)</span>', block_html, re.S | re.I)
        if not text_match:
            text_match = re.search(r'<div[^>]*?>(.*?)</div>', block_html, re.S)
        text = self._clean_html(text_match.group(1)) if text_match else ""

        # URL
        url_match = re.search(r'href="([^"]*?)"', block_html)
        url = url_match.group(1) if url_match else ""

        if not title and not text:
            return None

        return {
            "keyword": keyword,
            "ad_title": title[:255],
            "ad_text": text[:500],
            "ad_url": url[:500],
            "ad_position": "direct",
            "ad_type": "yandex_direct",
        }

    def _extract_ad_from_link(self, url: str, text: str, keyword: str, full_html: str) -> dict | None:
        """Извлекает объявление из ссылки и её окружения."""
        title = self._clean_html(text)
        # Ищем описание рядом со ссылкой
        desc = ""
        # Ищем ближайший текст после ссылки
        pattern = re.escape(text) + r'.*?<span[^>]*?>(.*?)</span>'
        desc_match = re.search(pattern, full_html, re.S | re.I)
        if desc_match:
            desc = self._clean_html(desc_match.group(1))

        if not title:
            return None

        return {
            "keyword": keyword,
            "ad_title": title[:255],
            "ad_text": desc[:500],
            "ad_url": url[:500],
            "ad_position": "organic_with_ad",
            "ad_type": "yandex_direct",
        }

    def _extract_ad_from_direct_url(self, url: str, keyword: str, full_html: str) -> dict | None:
        """Извлекает объявление из URL clck Яндекса, находя ближайший текст."""
        # Находим позицию URL в HTML
        pos = full_html.find(url)
        if pos == -1:
            return None

        # Берём окно вокруг URL
        window = full_html[max(0, pos - 500):pos + 500]

        # Ищем заголовок
        title_match = re.search(r'>([^<]{10,200})</a>', window)
        title = self._clean_html(title_match.group(1)) if title_match else ""

        # Ищем описание
        desc_match = re.search(r'</a>\s*(?:<span[^>]*?>)?([^<]{20,300})', window, re.S)
        desc = self._clean_html(desc_match.group(1)) if desc_match else ""

        if not title:
            return None

        return {
            "keyword": keyword,
            "ad_title": title[:255],
            "ad_text": desc[:500],
            "ad_url": url[:500],
            "ad_position": "direct",
            "ad_type": "yandex_direct",
        }

    def _clean_html(self, raw: str) -> str:
        """Убирает HTML-теги и лишние пробелы."""
        if not raw:
            return ""
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def scan_ads_for_competitor(self, competitor_id: int, keywords: list[str] = None) -> dict:
        """
        Сканирует рекламные объявления конкурента по списку ключевых слов.
        Если ключевые слова не указаны — берёт названия товаров из competitor_products.
        """
        from app.db.competitor_store import get_competitor_products, list_competitors

        competitors = list_competitors()
        comp = next((c for c in competitors if c["id"] == competitor_id), None)
        if not comp:
            return {"error": "Конкурент не найден"}

        comp_name = comp.get("name", "")
        comp_url = comp.get("url", "")

        if not keywords:
            # Берём названия товаров конкурента как ключевые слова
            products = get_competitor_products(competitor_id, limit=20)
            keywords = [p["product_name"] for p in products if p.get("product_name")]
            if not keywords:
                # Если нет товаров — используем общие строительные запросы
                keywords = [
                    f"купить {comp_name}",
                    f"{comp_name} цены",
                    "строительные материалы",
                    "гипсокартон купить",
                    "профнастил цена",
                ]

        all_ads = []
        for kw in keywords[:15]:  # Ограничиваем 15 ключевыми словами
            ads = await self.fetch_ads_for_keyword(kw, pages=1)
            # Фильтруем: оставляем только объявления конкурента
            for ad in ads:
                ad_url = ad.get("ad_url", "").lower()
                # Проверяем, что объявление от нашего конкурента
                comp_domain = urlparse(comp_url).netloc.lower().replace("www.", "")
                if comp_domain and comp_domain in ad_url:
                    ad["competitor_id"] = competitor_id
                    all_ads.append(ad)

        # Сохраняем в базу
        if all_ads:
            save_competitor_ads(competitor_id, all_ads)

        return {
            "status": "ok",
            "competitor_id": competitor_id,
            "keywords_checked": len(keywords),
            "ads_found": len(all_ads),
            "ads": all_ads,
        }

    async def scan_ads_bulk(self, keywords: list[str], max_results_per_kw: int = 5) -> dict:
        """
        Массовый поиск рекламных объявлений по ключевым словам.
        Сопоставляет с известными конкурентами.
        """
        competitors = list_competitors()
        comp_domains = {}
        for c in competitors:
            domain = urlparse(c.get("url", "")).netloc.lower().replace("www.", "")
            if domain:
                comp_domains[domain] = c["id"]

        all_ads = []
        for kw in keywords[:20]:
            ads = await self.fetch_ads_for_keyword(kw, pages=1)
            for ad in ads:
                ad_url = ad.get("ad_url", "").lower()
                # Определяем, чьё это объявление
                matched_comp_id = None
                for domain, cid in comp_domains.items():
                    if domain in ad_url:
                        matched_comp_id = cid
                        break

                if matched_comp_id:
                    ad["competitor_id"] = matched_comp_id
                    all_ads.append(ad)
                else:
                    # Сохраняем без привязки к конкуренту (общий анализ)
                    ad["competitor_id"] = None
                    all_ads.append(ad)

        # Сохраняем все
        if all_ads:
            # Очищаем старые общие записи
            from app.db.competitor_store import clear_competitor_ads
            clear_competitor_ads()
            # Группируем по competitor_id
            grouped = {}
            for ad in all_ads:
                cid = ad.get("competitor_id") or 0
                if cid not in grouped:
                    grouped[cid] = []
                grouped[cid].append(ad)
            for cid, ads_list in grouped.items():
                save_competitor_ads(cid, ads_list)

        return {
            "status": "ok",
            "keywords_checked": len(keywords),
            "total_ads": len(all_ads),
            "matched_to_competitors": len([a for a in all_ads if a.get("competitor_id")]),
        }

    async def get_competitor_ad_strategy(self, competitor_id: int) -> dict:
        """
        Анализирует рекламную стратегию конкурента на основе собранных объявлений.
        """
        ads = get_competitor_ads(competitor_id, limit=200)
        if not ads:
            return {"error": "Рекламные объявления не найдены. Сначала выполните сканирование."}

        # Топ ключевых слов
        keywords = {}
        for ad in ads:
            kw = ad.get("keyword", "")
            if kw:
                keywords[kw] = keywords.get(kw, 0) + 1

        # Топ упоминаемых товаров/тем
        titles_text = " ".join([a.get("ad_title", "") + " " + a.get("ad_text", "") for a in ads])
        # Извлекаем потенциальные товары из текста объявлений
        product_keywords = re.findall(r'(?:гипсокартон|профнастил|сайдинг|кирпич|блок|цемент|штукатурка|плитка|ламинат|гвл|фанера|доска|брус|профиль|крепеж|изоляция|мембрана|гидроизоляция|утеплитель|пеноплекс|минвата|базальт|грунтовка|краска|шпатлевка|смесь|раствор|песок|щебень)[\w\s-]*', titles_text, re.I)
        product_freq = {}
        for pk in product_keywords:
            pk_clean = pk.lower().strip()
            if len(pk_clean) > 3:
                product_freq[pk_clean] = product_freq.get(pk_clean, 0) + 1

        top_products = sorted(product_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Анализ позиций
        positions = {}
        for ad in ads:
            pos = ad.get("ad_position", "unknown")
            positions[pos] = positions.get(pos, 0) + 1

        return {
            "status": "ok",
            "competitor_id": competitor_id,
            "total_ads_analyzed": len(ads),
            "top_keywords": sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_products": top_products,
            "position_distribution": positions,
            "sample_ads": ads[:5],
        }

    # Предзаполненные популярные строительные магазины
    _BUILDING_COMPETITORS = [
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

    async def analyze_ads_for_our_products(self, limit: int = 30) -> dict:
        """
        Берёт наши товары и показывает ВСЕХ известных конкурентов,
        которые могут продавать эти товары (предзаполненная база + добавленные).
        """
        from app.services.product_db import product_db
        from app.db.competitor_store import list_competitors

        our_products = product_db.list_products()[:limit]
        results = []

        # Собираем всех известных конкурентов
        all_competitors = []
        seen_domains = set()

        # 1. Предзаполненные популярные магазины
        for c in self._BUILDING_COMPETITORS:
            all_competitors.append(c)
            seen_domains.add(c["domain"])

        # 2. Добавленные вручную конкуренты
        for c in list_competitors():
            url = c.get("url", "")
            domain = urlparse(url).netloc.lower().replace("www.", "") if url else ""
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_competitors.append({
                    "domain": domain,
                    "url": url or f"https://{domain}",
                    "name": c.get("name", domain),
                })

        # Для каждого товара показываем всех конкурентов
        for product in our_products:
            if not product.name:
                continue

            comps_for_product = []
            for c in all_competitors:
                comps_for_product.append({
                    "domain": c["domain"],
                    "ad_title": c.get("name", ""),
                    "ad_text": f"Потенциальный конкурент по товару: {product.name}",
                    "ad_url": c.get("url", f"https://{c['domain']}"),
                })

            results.append({
                "sku": product.sku,
                "product_name": product.name,
                "our_price": product.retail_price,
                "our_cost": product.cost_price_cash or product.cost_price_cashless,
                "our_roi": product.roi,
                "competitors_ads": comps_for_product,
                "competitors_count": len(comps_for_product),
            })

        return {
            "status": "ok",
            "products_checked": len(our_products),
            "products_with_competitors": len(results),
            "data": results,
        }

    async def close(self):
        pass


ad_spy = AdSpy()
