"""
Playwright Scanner — сканирование рекламы Яндекс Директ и SPA-сайтов конкурентов.
Использует установленный Chrome/Edge через channel (не требует отдельного Chromium).
"""

import asyncio
import json
import re
from urllib.parse import urlparse

from playwright.async_api import async_playwright


class PlaywrightScanner:
    """Сканер на базе Playwright для сайтов и поисковой выдачи."""

    def __init__(self, headless: bool = True, channel: str = "chrome"):
        self.headless = headless
        self.channel = channel  # "chrome" | "msedge" | None
        self._playwright = None
        self._browser = None

    async def _start(self):
        """Запускает браузер, если ещё не запущен."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            launch_kwargs = {"headless": self.headless}
            if self.channel:
                launch_kwargs["channel"] = self.channel
            self._browser = await self._playwright.chromium.launch(**launch_kwargs)

    async def _close(self):
        """Закрывает браузер."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    # ═══════════════════════════════════════════════════════════════════════
    # 1. Сканирование рекламы Яндекс Директ (поисковая выдача)
    # ═══════════════════════════════════════════════════════════════════════

    async def scan_yandex_ads(self, query: str, lr: int = 1, max_ads: int = 10) -> list[dict]:
        """
        Открывает yandex.ru/search?text=..., парсит блоки рекламы Яндекс Директ.
        Возвращает список объявлений: title, text, url, position, domain.
        """
        await self._start()
        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        search_url = f"https://yandex.ru/search/?text={query.replace(' ', '+')}&lr={lr}"
        ads = []

        try:
            print(f"[Playwright] Открываем: {search_url}")
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                # Если domcontentloaded не успел, просто ждём загрузки страницы
                pass
            await asyncio.sleep(3)  # даём рекламе и JS догрузиться

            # Проверяем, не показалась ли каптча
            captcha = await page.query_selector('input[name="rep"], .CheckboxCaptcha, .captcha__image')
            if captcha:
                print("[Playwright] Каптча! Сохраняем скриншот.")
                await page.screenshot(path="yandex_captcha.png")
                return []

            # Стратегия 1: data-cid блоки с data-type="ad"
            ad_blocks = await page.query_selector_all('div[data-cid]')
            print(f"[Playwright] data-cid блоков: {len(ad_blocks)}")

            for idx, block in enumerate(ad_blocks[:max_ads]):
                try:
                    is_ad = await block.evaluate('el => el.getAttribute("data-type") === "ad" || el.innerText.includes("Реклама") || el.innerText.includes("Ya.Direct")')
                    if not is_ad:
                        continue

                    link = await block.query_selector('a[href]')
                    if not link:
                        continue

                    title = await link.inner_text()
                    href = await link.get_attribute('href')

                    text_el = await block.query_selector('div[class*="text"], p, span[class*="desc"]')
                    text = await text_el.inner_text() if text_el else ""

                    # Разрешаем yandex-редирект
                    real_url = href or ""
                    if real_url.startswith("/"):
                        real_url = f"https://yandex.ru{real_url}"

                    domain = urlparse(real_url).netloc.replace("www.", "") if real_url else ""

                    ads.append({
                        "position": idx + 1,
                        "title": title.strip(),
                        "text": text.strip(),
                        "url": real_url,
                        "domain": domain,
                        "query": query,
                        "source": "yandex_direct",
                    })
                except Exception as exc:
                    print(f"  [Playwright] Ошибка блока #{idx}: {exc}")
                    continue

            # Стратегия 2: ищем по label "Реклама" / "Ya.Direct"
            if not ads:
                print("[Playwright] Fallback: ищем по label 'Реклама'...")
                labels = await page.query_selector_all('span, div, li')
                for label in labels:
                    try:
                        txt = await label.inner_text()
                        if "реклама" not in txt.lower() and "ya.direct" not in txt.lower():
                            continue
                        # Ищем ближайшую ссылку
                        link = await label.evaluate_handle('el => { let p=el.parentElement; for(let i=0;i<5;i++){ if(!p) break; let a=p.querySelector("a[href]"); if(a) return a; p=p.parentElement } return null }')
                        if link and not await link.evaluate('el => el === null'):
                            href = await link.get_attribute('href') or ""
                            title = await link.inner_text()
                            if href and title and len(title) > 3:
                                dom = urlparse(href).netloc.replace("www.", "")
                                if dom and "yandex" not in dom:
                                    ads.append({
                                        "position": len(ads) + 1,
                                        "title": title.strip(),
                                        "text": txt.strip(),
                                        "url": href,
                                        "domain": dom,
                                        "query": query,
                                        "source": "yandex_direct_fallback",
                                    })
                                    if len(ads) >= max_ads:
                                        break
                    except Exception:
                        continue

        except Exception as exc:
            print(f"[Playwright] Ошибка сканирования: {exc}")
        finally:
            await context.close()

        print(f"[Playwright] Найдено объявлений: {len(ads)}")
        return ads

    # ═══════════════════════════════════════════════════════════════════════
    # 2. Сканирование сайта конкурента (SPA-friendly)
    # ═══════════════════════════════════════════════════════════════════════

    async def scan_website(self, url: str, max_wait_ms: int = 15000) -> dict:
        """
        Открывает сайт конкурента, ждёт загрузки JS, парсит товары.
        Возвращает: {domain, products: [{name, price, url, image}], error}.
        """
        await self._start()
        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        result = {"domain": urlparse(url).netloc.replace("www.", ""), "products": [], "error": None}

        try:
            print(f"[Playwright] Сканируем сайт: {url}")
            # Перехватываем финальный URL после редиректов
            final_url = url
            def handle_nav(frame):
                nonlocal final_url
                if frame == page.main_frame:
                    final_url = frame.url
            page.on("framenavigated", handle_nav)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=max_wait_ms)
            except Exception:
                pass  # даже если domcontentloaded не дождались, продолжаем
            await asyncio.sleep(3)  # даём подгрузиться lazy-content и JS

            # Стратегия 1: JSON-LD (Schema.org Product) — после рендеринга может появиться
            jsonld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
            for script in jsonld_scripts:
                try:
                    raw = await script.inner_text()
                    data = json.loads(raw)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") == "Product":
                            offers = item.get("offers", {})
                            if isinstance(offers, list) and offers:
                                offers = offers[0]
                            result["products"].append({
                                "name": item.get("name", ""),
                                "price": self._extract_price(offers.get("price", "")),
                                "currency": offers.get("priceCurrency", "RUB"),
                                "url": item.get("url", ""),
                                "image": item.get("image", ""),
                                "sku": item.get("sku", ""),
                                "source": "jsonld",
                            })
                except Exception:
                    continue

            # Стратегия 2: Microdata (itemprop)
            if not result["products"]:
                product_blocks = await page.query_selector_all('[itemtype*="Product"]')
                for block in product_blocks[:50]:
                    try:
                        name_el = await block.query_selector('[itemprop="name"]')
                        price_el = await block.query_selector('[itemprop="price"]')
                        url_el = await block.query_selector('[itemprop="url"]')
                        img_el = await block.query_selector('[itemprop="image"]')

                        name = await name_el.inner_text() if name_el else ""
                        price = self._extract_price(await price_el.get_attribute("content") if price_el else "")
                        purl = await url_el.get_attribute("href") if url_el else ""
                        img = await img_el.get_attribute("src") if img_el else ""

                        if name:
                            result["products"].append({
                                "name": name.strip(),
                                "price": price,
                                "currency": "RUB",
                                "url": purl,
                                "image": img,
                                "sku": "",
                                "source": "microdata",
                            })
                    except Exception:
                        continue

            # Стратегия 3: Эвристики — карточки товаров
            if not result["products"]:
                skip_words = ('меню', 'каталог', 'главная', 'о нас', 'контакты', 'доставка', 'оплата', 'акции', 'новости', 'блог', 'вакансии', 'партнёрам')
                heuristics = [
                    'h3', 'h2', '.product-title', '.product-name', '[class*="product"]', '[class*="item-title"]',
                ]
                for selector in heuristics:
                    elems = await page.query_selector_all(selector)
                    for el in elems[:30]:
                        try:
                            text = (await el.inner_text()).strip().lower()
                            if len(text) < 5 or len(text) > 150 or any(sw in text for sw in skip_words):
                                continue
                            # Ищем цену рядом
                            parent = await el.evaluate('node => { let p = node.parentElement; for(let i=0;i<6;i++){ if(!p) break; let m = p.innerText.match(/(?:^|[^\\d])(\\d[\\s\\u00A0\\d]{3,})(?:\\s*₽|руб|RUB)/); if(m) return m[1]; p=p.parentElement } return null }')
                            price = self._extract_price(parent) if parent else 0
                            if price <= 0:
                                sibling = await el.evaluate('node => { let s = node.nextElementSibling; for(let i=0;i<3;i++){ if(!s) break; let m = s.innerText.match(/(?:^|[^\\d])(\\d[\\s\\u00A0\\d]{3,})(?:\\s*₽|руб|RUB)/); if(m) return m[1]; s = s.nextElementSibling } return null }')
                                price = self._extract_price(sibling) if sibling else 0
                            if price > 0:
                                result["products"].append({
                                    "name": text.strip().title(),
                                    "price": price,
                                    "currency": "RUB",
                                    "url": "",
                                    "image": "",
                                    "sku": "",
                                    "source": f"heuristic:{selector}",
                                })
                        except Exception:
                            continue
                    if result["products"]:
                        break

        except Exception as exc:
            result["error"] = str(exc)
            print(f"[Playwright] Ошибка сканирования сайта {url}: {exc}")
        finally:
            await context.close()

        print(f"[Playwright] Найдено товаров на {url}: {len(result['products'])}")
        return result

    # ═══════════════════════════════════════════════════════════════════════
    # Утилиты
    # ═══════════════════════════════════════════════════════════════════════

    def _extract_price(self, value) -> float:
        """Извлекает числовую цену из строки/числа."""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value)
        # Удаляем всё кроме цифр, точек, запятых
        cleaned = re.sub(r"[^\d.,]", "", text)
        # Заменяем запятую на точку
        cleaned = cleaned.replace(",", ".")
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                return 0
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton для backend
# ═══════════════════════════════════════════════════════════════════════════════

_playwright_scanner = None


async def get_scanner() -> PlaywrightScanner:
    """Возвращает (или создаёт) singleton сканер."""
    global _playwright_scanner
    if _playwright_scanner is None:
        _playwright_scanner = PlaywrightScanner(headless=True, channel="chrome")
    return _playwright_scanner


async def close_scanner():
    """Закрывает сканер при завершении приложения."""
    global _playwright_scanner
    if _playwright_scanner:
        await _playwright_scanner._close()
        _playwright_scanner = None
