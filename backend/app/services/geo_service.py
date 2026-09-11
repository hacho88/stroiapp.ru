"""
Геотаргетинг-сервис.
Определяет город посетителя по IP, генерирует гео-описания товаров.
"""

import json
import urllib.request
import ssl

from app.data.geo_regions import GEO_CITIES, find_nearest_city, get_city_by_id


class GeoService:
    """Сервис геотаргетинга."""

    def detect_city_by_ip(self, ip: str | None = None) -> dict:
        """Определить город по IP через ip-api (бесплатно, 45/min).
        Если IP не указан — определяет по IP сервера.
        """
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = f"http://ip-api.com/json/{ip or ''}?fields=status,message,city,regionName,lat,lon,country,query&lang=ru"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return self._fallback_detect()

        if data.get("status") != "success":
            return self._fallback_detect()

        city_name = data.get("city", "")
        lat = data.get("lat")
        lon = data.get("lon")

        # Ищем в нашем справочнике по имени
        for city in GEO_CITIES:
            if city["name"].lower() == city_name.lower():
                return {
                    "detected": True,
                    "city": city,
                    "method": "ip-api exact match",
                    "ip": data.get("query"),
                }

        # Если не нашли — ищем ближайший по координатам
        if lat is not None and lon is not None:
            nearest = find_nearest_city(lat, lon)
            if nearest:
                return {
                    "detected": True,
                    "city": nearest,
                    "method": "ip-api nearest by coords",
                    "distance_km": self._distance(lat, lon, nearest["lat"], nearest["lon"]),
                    "ip": data.get("query"),
                }

        return self._fallback_detect()

    def _fallback_detect(self) -> dict:
        """Москва по умолчанию."""
        moscow = get_city_by_id("moscow")
        return {
            "detected": False,
            "city": moscow,
            "method": "fallback (Moscow)",
            "ip": None,
        }

    @staticmethod
    def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        import math
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    @staticmethod
    def _to_prepositional(city_name: str) -> str:
        """Склонение названия города в предложный падеж (в + где?).
        Химки → Химках, Балашиха → Балашихе, Москва → Москве, Тверь → Твери.
        """
        # Множественные названия (районы, города во мн.ч.)
        plural_endings = {
            'ки': 'ках', 'щи': 'щах', 'цы': 'цах', 'ны': 'нах',
            'ты': 'тах', 'ги': 'гах', 'вы': 'вах', 'би': 'бах',
            'ды': 'дах', 'лы': 'лах', 'ри': 'рах', 'сы': 'сах',
            'ши': 'шах', 'чи': 'чах', 'ни': 'нах', 'мы': 'мах',
        }
        for ending, replacement in plural_endings.items():
            if city_name.endswith(ending):
                return city_name[:-2] + replacement

        # Окончание на -ец → -це (Череповец → Череповце)
        if city_name.endswith('ец') and len(city_name) > 3:
            return city_name[:-2] + 'це'

        # Составные названия (Тёплый Стан, Нагатинский Затон) — склоняем обе части
        if ' ' in city_name:
            parts = city_name.split(' ')
            declined = [GeoService._to_prepositional(p) for p in parts]
            return ' '.join(declined)

        # Окончание на -и (множ. типа Бирюлёво не подходит, но Твери-подобные)
        if city_name.endswith('и') and len(city_name) > 3:
            # Проверяем, не является ли это формой на -ие
            if not city_name.endswith('ние'):
                return city_name[:-1] + 'ах'

        # Единственное число, женский род (-а, -я)
        if city_name.endswith('а'):
            return city_name[:-1] + 'е'
        if city_name.endswith('я'):
            return city_name[:-1] + 'е'

        # Единственное число, мужской род (-ь)
        if city_name.endswith('ь'):
            return city_name[:-1] + 'и'

        # Прилагательные (-ый, -ий, -ое)
        if city_name.endswith('ый'):
            return city_name[:-2] + 'ом'
        if city_name.endswith('ий'):
            return city_name[:-2] + 'ом'
        if city_name.endswith('ое'):
            return city_name[:-2] + 'ом'

        # Неизменяемые на -ино (Марфино — не склоняется в литературном языке)
        if city_name.endswith('ино'):
            return city_name  # неизменяемое

        # Неизменяемые (-о, -е, -и)
        if city_name.endswith('о'):
            return city_name[:-1] + 'е'
        if city_name.endswith('е'):
            return city_name  # уже похож на предл. падеж
        if city_name.endswith('и'):
            return city_name  # неизменяемое

        # По умолчанию: согласный + е
        return city_name + 'е'

    def generate_geo_description(self, product_name: str, city: dict) -> dict:
        """Сгенерировать гео-описание товара для конкретного города.
        Использует DeepSeek AI для базового текста + уникализация под город.
        """
        city_name = city["name"]
        city_prep = self._to_prepositional(city_name)
        delivery_time = city["delivery_time_hours"]
        delivery_cost = city["delivery_cost"]
        has_wh = city["has_warehouse"]

        # SEO-заголовок
        seo_title = f"{product_name} — купить в {city_prep}"

        # Гео H1
        geo_h1 = f"{product_name} в {city_prep}"

        # Получаем базовое AI-описание (1 запрос на товар, кэшируется)
        base_desc = self._get_base_ai_description(product_name)

        # Уникализируем под город
        ai_description = self._customize_for_city(base_desc, product_name, city_name, city_prep, delivery_time, delivery_cost, has_wh)

        # SEO meta description
        if delivery_cost == 0:
            delivery_text = f"Бесплатная доставка в {city_prep}"
        else:
            delivery_text = f"Доставка в {city_prep} от {delivery_cost} ₽"

        if has_wh:
            delivery_text += ", пункт выдачи"

        if delivery_time <= 4:
            time_text = f"от {delivery_time} часов"
        elif delivery_time <= 24:
            time_text = f"от {delivery_time // 24} дня"
        else:
            time_text = f"от {delivery_time // 24} дней"

        seo_description = (
            f"{product_name} в {city_prep}. {delivery_text}. "
            f"Срок: {time_text}. Опт, НДС. stroiapp.ru"
        )[:160]

        return {
            "city": city_name,
            "seo_title": seo_title,
            "seo_description": seo_description,
            "geo_h1": geo_h1,
            "delivery_time_hours": delivery_time,
            "delivery_cost": delivery_cost,
            "has_warehouse": has_wh,
            "full_description": ai_description,
            "schema_org": {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": product_name,
                "offers": {
                    "@type": "Offer",
                    "availability": "https://schema.org/InStock" if has_wh else "https://schema.org/PreOrder",
                    "deliveryTime": {
                        "@type": "ShippingDeliveryTime",
                        "handlingTime": {
                            "@type": "QuantitativeValue",
                            "minValue": delivery_time,
                            "unitCode": "HUR",
                        },
                    },
                    "shippingDetails": {
                        "@type": "OfferShippingDetails",
                        "shippingRate": {
                            "@type": "MonetaryAmount",
                            "value": delivery_cost,
                            "currency": "RUB",
                        },
                        "shippingDestination": {
                            "@type": "DefinedRegion",
                            "name": city_name,
                        },
                    },
                },
            },
        }

    def _get_base_ai_description(self, product_name: str) -> dict:
        """1 запрос к DeepSeek на товар — генерирует базовые блоки описания.
        Возвращает dict с параграфами для последующей сборки под каждый город.
        """
        if not hasattr(self, '_base_cache'):
            self._base_cache = {}

        if product_name in self._base_cache:
            return self._base_cache[product_name]

        # Пытаемся DeepSeek
        try:
            from app.core.config import settings
            ds_key = settings.deepseek_api_key
            print(f"[GeoAI] DeepSeek key loaded: {'yes' if ds_key else 'no'} ({ds_key[:10]}...)")
        except Exception as e:
            print(f"[GeoAI] Failed to import settings: {e}")
            ds_key = ""

        if not ds_key:
            result = self._generate_base_template(product_name)
            self._base_cache[product_name] = result
            return result

        import json as _json
        import urllib.request as _req
        import ssl as _ssl
        import time as _time

        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE

        prompt = (
                f"Ты SEO-копирайтер для магазина стройматериалов stroiapp.ru.\n"
                f"Напиши описание товара '{product_name}' в формате JSON с полями:\n"
                f"intro - 1 предложение о товаре (профессиональное)\n"
                f"benefits - 1 предложение о преимуществах\n"
                f"application - 1 предложение о применении\n"
                f"opt - 1 предложение об оптовых ценах и НДС\n"
                f"quality - 1 предложение о качестве/сертификатах\n"
                f"order - 1 предложение о заказе\n"
                f"Все тексты на русском, без упоминания городов. Каждое поле 1-2 предложения."
        )

        payload = _json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты SEO-копирайтер. Пиши на русском. Возвращай только JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 600,
                "response_format": {"type": "json_object"},
        }).encode("utf-8")

        # Retry up to 3 times with delay
        last_error = None
        for attempt in range(3):
            try:
                req = _req.Request(
                        "https://api.deepseek.com/v1/chat/completions",
                        data=payload,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {ds_key}"},
                        method="POST",
                )
                with _req.urlopen(req, timeout=60, context=ctx) as resp:
                    result = _json.loads(resp.read().decode("utf-8-sig"))

                content = _json.loads(result["choices"][0]["message"]["content"])
                base = {
                    "intro": content.get("intro", ""),
                    "benefits": content.get("benefits", ""),
                    "application": content.get("application", ""),
                    "opt": content.get("opt", ""),
                    "quality": content.get("quality", ""),
                    "order": content.get("order", ""),
                }
                self._base_cache[product_name] = base
                return base
            except Exception as e:
                last_error = e
                print(f"[GeoAI] DeepSeek attempt {attempt+1} failed: {str(e)[:150]}")
                if attempt < 2:
                    _time.sleep(2)

        print(f"[GeoAI] DeepSeek failed after 3 attempts, using template. Last error: {str(last_error)[:200]}")
        result = self._generate_base_template(product_name)
        self._base_cache[product_name] = result
        return result

    def _generate_base_template(self, product_name: str) -> dict:
        """Шаблонные блоки (fallback если DeepSeek недоступен)."""
        return {
            "intro": f"{product_name} — профессиональное решение для строительных и ремонтных работ.",
            "benefits": "Обеспечивает надёжный результат, проверен на практике строительными бригадами.",
            "application": "Подходит для внутренних и наружных работ, соответствует техническим требованиям.",
            "opt": "Оптовые цены для юридических лиц и ИП, безналичный расчёт с НДС.",
            "quality": "Сертифицированная продукция с гарантией качества от производителя.",
            "order": "Оформите заказ на stroiapp.ru или по телефону — доставим на объект.",
        }

    def _customize_for_city(self, base: dict, product_name: str, city_name: str, city_prep: str,
                            delivery_time: int, delivery_cost: int, has_wh: bool) -> str:
        """Собрать уникальное описание из базовых блоков + городской контекст.
        Меняет порядок предложений и добавляет городские детали для уникальности.
        """
        import random

        # Городские детали
        if delivery_cost == 0:
            delivery_phrase = f"Бесплатная доставка в {city_prep}"
        else:
            delivery_phrase = f"Доставка в {city_prep} от {delivery_cost} ₽"

        if delivery_time <= 4:
            time_phrase = f"доставим в {city_prep} за {delivery_time} часов"
        elif delivery_time <= 24:
            days = delivery_time // 24
            time_phrase = f"доставка в {city_prep} — от {days} дня"
        else:
            days = delivery_time // 24
            time_phrase = f"доставка в {city_prep} — от {days} дней"

        if has_wh:
            wh_phrase = f"В {city_prep} работает пункт выдачи — заберите заказ самовывозом."
        else:
            wh_phrase = f"Доставим прямо на строительный объект в {city_prep}."

        # Варианты вступительных фраз (рандомизация)
        intro_variants = [
            f"{base['intro']}",
            f"Ищете {product_name.lower()} в {city_prep}? {base['intro']}",
            f"{base['intro']} Теперь доступен и в {city_prep}.",
        ]

        # Варианты концовки
        order_variants = [
            f"{base['order']} {delivery_phrase}, {time_phrase}.",
            f"{delivery_phrase}. {base['order']}",
            f"{time_phrase.capitalize()}. {base['order']}",
        ]

        # Случайный выбор
        idx = hash(f"{product_name}_{city_name}") % 3
        intro = intro_variants[idx]
        order = order_variants[idx]

        # Случайный порядок средних блоков
        middle_blocks = [base['benefits'], base['application'], base['opt'], base['quality']]
        seed = hash(f"{product_name}_{city_name}_order")
        rng = random.Random(seed)
        rng.shuffle(middle_blocks)

        # Сборка
        paragraphs = [
            f"<p>{intro} {middle_blocks[0]}</p>",
            f"<p>{middle_blocks[1]} {middle_blocks[2]}</p>",
            f"<p>{wh_phrase} {middle_blocks[3]}</p>",
            f"<p>{order}</p>",
        ]

        return "\n".join(paragraphs)

    def get_all_cities(self) -> list[dict]:
        """Все города из справочника."""
        return GEO_CITIES

    def get_cities_for_region(self, region: str) -> list[dict]:
        """Города конкретного региона."""
        from app.data.geo_regions import get_cities_by_region
        return get_cities_by_region(region)


_geo_service = GeoService()


def get_geo_service() -> GeoService:
    return _geo_service
