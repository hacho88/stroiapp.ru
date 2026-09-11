"""
Автоматическая генерация гео-страниц для новых товаров.
Запускается как фоновая задача при старте бэкенда.
Проверяет каждые 30 минут — есть ли товары без гео-страниц.
Если есть — генерирует их автоматически.
"""

import asyncio

from app.services.geo_pages_service import get_geo_pages_service
from app.services.opencart_api import opencart_api
from app.data.geo_regions import GEO_CITIES


class GeoAutoGenerator:
    def __init__(self):
        self._running = False
        self._check_interval = 1800  # 30 minutes
        self._last_run = None
        self._last_result = None

    async def _find_products_without_geo(self) -> list[dict]:
        """Найти товары, у которых ещё нет гео-страниц."""
        try:
            # Get all products (paginate through all pages)
            all_products = []
            page = 1
            while True:
                products_data = await opencart_api.get_action("product/list", {"limit": 100, "page": page})
                products = products_data.get("products", [])
                if not products:
                    break
                all_products.extend(products)
                if len(products) < 100:
                    break
                page += 1

            if not all_products:
                return []

            # Check which ones already have geo pages
            product_ids = [p["product_id"] for p in all_products if p.get("product_id")]
            if not product_ids:
                return []

            # Query in chunks to avoid SQL too long
            existing_ids = set()
            chunk_size = 200
            for i in range(0, len(product_ids), chunk_size):
                chunk = product_ids[i:i+chunk_size]
                id_list = ",".join(str(pid) for pid in chunk)
                check_sql = f"SELECT DISTINCT product_id FROM oc_product_geo WHERE product_id IN ({id_list})"
                result = await opencart_api.post_action("db/executeSql", {"sql": check_sql})

                if isinstance(result, dict) and "rows" in result:
                    for row in result["rows"]:
                        existing_ids.add(int(row.get("product_id", 0)))
                elif isinstance(result, list):
                    for row in result:
                        existing_ids.add(int(row.get("product_id", 0)))

            # Return products without geo pages
            new_products = [p for p in all_products if p.get("product_id") and int(p["product_id"]) not in existing_ids]
            return new_products
        except Exception as e:
            print(f"[GeoAuto] Error finding new products: {str(e)[:200]}")
            return []

    async def _run_cycle(self):
        """Один цикл проверки и генерации."""
        print("[GeoAuto] Checking for new products without geo pages...")
        new_products = await self._find_products_without_geo()

        if not new_products:
            print("[GeoAuto] All products have geo pages. Nothing to do.")
            self._last_result = {"status": "ok", "new_products": 0, "generated": 0}
            return

        print(f"[GeoAuto] Found {len(new_products)} new products. Generating geo pages...")

        # Create table if not exists
        gps = get_geo_pages_service()
        await gps.create_table()

        total_generated = 0
        for product in new_products:
            pid = product.get("product_id")
            name = product.get("name", "")
            if not pid or not name:
                continue
            print(f"[GeoAuto] Generating for product {pid}: {name[:50]}")
            result = await gps.generate_for_product(pid, name)
            total_generated += result.get("generated", 0)

        print(f"[GeoAuto] Done. Generated {total_generated} geo pages for {len(new_products)} products.")

        # Regenerate sitemap after adding new pages
        try:
            await opencart_api.post_action("site/generateSitemap", {})
            print("[GeoAuto] Sitemap regenerated.")
        except Exception:
            pass

        self._last_result = {
            "status": "ok",
            "new_products": len(new_products),
            "generated": total_generated,
        }

    async def start(self):
        """Запустить фоновый цикл."""
        if self._running:
            return
        self._running = True
        print("[GeoAuto] Background geo-page generator started (checks every 30 min)")

        # Wait 60s after startup before first check
        await asyncio.sleep(60)

        while self._running:
            try:
                import datetime
                self._last_run = datetime.datetime.now().isoformat()
                await self._run_cycle()
            except Exception as e:
                print(f"[GeoAuto] Error: {str(e)[:200]}")

            await asyncio.sleep(self._check_interval)

    def stop(self):
        self._running = False

    def status(self) -> dict:
        return {
            "running": self._running,
            "check_interval_seconds": self._check_interval,
            "last_run": self._last_run,
            "last_result": self._last_result,
            "cities_count": len(GEO_CITIES),
        }


_geo_auto = GeoAutoGenerator()


def get_geo_auto_generator() -> GeoAutoGenerator:
    return _geo_auto
