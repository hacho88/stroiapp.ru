"""
Сервис массовой генерации гео-страниц.
Создаёт уникальные SEO-описания для каждого товара × каждого города.
"""

from app.data.geo_regions import GEO_CITIES
from app.services.geo_service import get_geo_service
from app.services.opencart_api import opencart_api


class GeoPagesService:
    """Генерация и сохранение гео-страниц в OpenCart."""

    async def create_table(self) -> dict:
        """Создать таблицу oc_product_geo в OpenCart."""
        sql = """
        CREATE TABLE IF NOT EXISTS `oc_product_geo` (
          `product_geo_id` INT(11) AUTO_INCREMENT PRIMARY KEY,
          `product_id` INT(11) NOT NULL,
          `city_id` VARCHAR(50) NOT NULL,
          `city_name` VARCHAR(100) NOT NULL,
          `seo_title` VARCHAR(255) NOT NULL,
          `seo_description` VARCHAR(255) NOT NULL,
          `geo_h1` VARCHAR(255) NOT NULL,
          `description` TEXT,
          `delivery_time_hours` INT(11) DEFAULT 0,
          `delivery_cost` DECIMAL(10,2) DEFAULT 0.00,
          `has_warehouse` TINYINT(1) DEFAULT 0,
          `language_id` INT(11) DEFAULT 1,
          `date_added` DATETIME DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY `unique_product_city` (`product_id`, `city_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        try:
            result = await opencart_api.post_action("db/executeSql", {"sql": sql})
            return {"status": "ok", "table": "oc_product_geo", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)[:300]}

    async def generate_for_product(self, product_id: int, product_name: str) -> dict:
        """Сгенерировать гео-страницы для одного товара (bulk insert in batches)."""
        gs = get_geo_service()

        # Pre-fetch DeepSeek AI base description in executor (avoids blocking event loop)
        import asyncio
        loop = asyncio.get_event_loop()
        base_desc = await loop.run_in_executor(None, gs._get_base_ai_description, product_name)
        is_ai = not base_desc.get("intro", "").startswith(product_name[:20])
        print(f"[GeoAI] Base description for '{product_name[:40]}': {'AI' if is_ai else 'template'} | intro: {base_desc.get('intro','')[:80]}")

        all_values = []
        for city in GEO_CITIES:
            try:
                geo = gs.generate_geo_description(product_name, city)
                esc = lambda s: s.replace("'", "\\'").replace("\\", "\\\\")
                val = f"({product_id}, '{city['id']}', '{city['name']}', '{esc(geo['seo_title'])}', '{esc(geo['seo_description'])}', '{esc(geo['geo_h1'])}', '{esc(geo['full_description'])}', {geo['delivery_time_hours']}, {geo['delivery_cost']}, {1 if geo['has_warehouse'] else 0})"
                all_values.append(val)
            except Exception:
                pass

        if not all_values:
            return {"product_id": product_id, "product_name": product_name, "generated": 0, "errors": len(GEO_CITIES)}

        # Insert in batches of 30 to avoid SQL too large
        total_inserted = 0
        batch_size = 30
        for i in range(0, len(all_values), batch_size):
            batch = all_values[i:i + batch_size]
            sql = f"""
            INSERT INTO `oc_product_geo`
            (product_id, city_id, city_name, seo_title, seo_description, geo_h1, description, delivery_time_hours, delivery_cost, has_warehouse)
            VALUES
            {','.join(batch)}
            ON DUPLICATE KEY UPDATE
            seo_title = VALUES(seo_title),
            seo_description = VALUES(seo_description),
            geo_h1 = VALUES(geo_h1),
            description = VALUES(description),
            delivery_time_hours = VALUES(delivery_time_hours),
            delivery_cost = VALUES(delivery_cost),
            has_warehouse = VALUES(has_warehouse)
            """
            try:
                await opencart_api.post_action("db/executeSql", {"sql": sql})
                total_inserted += len(batch)
            except Exception as e:
                print(f"[GeoPages ERROR] product_id={product_id} batch {i}: {str(e)[:200]}")

        return {"product_id": product_id, "product_name": product_name, "generated": total_inserted, "errors": len(all_values) - total_inserted}

    async def generate_all(self, limit: int = 0) -> dict:
        """Сгенерировать гео-страницы для товаров. limit=0 — все товары (in batches)."""
        # Получаем список товаров батчами
        all_products = []
        page = 1
        batch_size = 50
        max_products = limit if limit > 0 else 10000

        while len(all_products) < max_products:
            try:
                products_data = await opencart_api.get_action("product/list", {"limit": batch_size, "page": page})
                products = products_data.get("products", [])
                if not products:
                    break
                all_products.extend(products)
                page += 1
                if len(products) < batch_size:
                    break
            except Exception as e:
                print(f"[GeoPages] Error fetching page {page}: {str(e)[:200]}")
                break

        products = all_products[:max_products] if limit > 0 else all_products

        if not products:
            return {"status": "error", "message": "No products found"}

        # Skip products that already have all cities (213) — only regenerate incomplete ones
        try:
            id_list = ",".join(str(p["product_id"]) for p in products if p.get("product_id"))
            check_sql = f"SELECT product_id, COUNT(*) as cnt FROM oc_product_geo WHERE product_id IN ({id_list}) GROUP BY product_id HAVING cnt >= {len(GEO_CITIES)}"
            existing = await opencart_api.post_action("db/executeSql", {"sql": check_sql})
            done_ids = set()
            if isinstance(existing, dict) and "rows" in existing:
                for row in existing["rows"]:
                    done_ids.add(int(row.get("product_id", 0)))
            elif isinstance(existing, list):
                for row in existing:
                    done_ids.add(int(row.get("product_id", 0)))
            before = len(products)
            products = [p for p in products if int(p.get("product_id", 0)) not in done_ids]
            print(f"[GeoPages] Skipping {before - len(products)} already complete, {len(products)} to process")
        except Exception as e:
            print(f"[GeoPages] Skip check failed (non-critical): {str(e)[:200]}")

        total_generated = 0
        total_errors = 0
        results = []
        idx = 1
        total = len(products)

        for product in products:
            pid = product.get("product_id")
            name = product.get("name", "")
            if not pid or not name:
                continue
            print(f"[GeoPages] Processing product {idx}/{total}: {name[:50]}")
            result = await self.generate_for_product(pid, name)
            total_generated += result["generated"]
            total_errors += result["errors"]
            results.append(result)
            idx += 1

        return {
            "status": "ok",
            "total_products": len(products),
            "total_generated": total_generated,
            "total_errors": total_errors,
            "cities_per_product": len(GEO_CITIES),
            "results": results[:5],
        }

    async def get_geo_pages_for_product(self, product_id: int) -> list[dict]:
        """Получить гео-страницы товара."""
        sql = f"SELECT * FROM `oc_product_geo` WHERE product_id = {product_id}"
        try:
            result = await opencart_api.post_action("db/executeSql", {"sql": sql})
            return result
        except Exception:
            return []


_geo_pages_service = GeoPagesService()


def get_geo_pages_service() -> GeoPagesService:
    return _geo_pages_service
