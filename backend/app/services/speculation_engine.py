"""
Speculation Rules API Engine for Chromium Prerender.
Generates dynamic, high-probability URL rulesets based on product/category context.
"""

import json
import random
from typing import Any

from app.services.opencart_api import opencart_api


class SpeculationEngine:
    """Generates Chromium-compliant Speculation Rules JSON."""

    BASE_URL = "https://stroiapp.ru"
    _last_rules: dict[str, Any] | None = None

    async def get_top_categories(self, limit: int = 5) -> list[dict]:
        """Fetch top-viewed or best-selling categories."""
        try:
            result = await opencart_api.get_action("category/list")
            cats = result.get("categories", [])
            active = [c for c in cats if c.get("status") == "1"]
            active.sort(key=lambda x: x.get("sort_order", 0))
            return active[:limit]
        except Exception:
            return []

    async def get_top_products(self, limit: int = 10) -> list[dict]:
        """Fetch top active products."""
        try:
            result = await opencart_api.get_action("product/list", {"limit": 200})
            prods = result.get("products", [])
            active = [p for p in prods if p.get("status") == "1" and p.get("quantity", 0) > 0]
            random.shuffle(active)
            return active[:limit]
        except Exception:
            return []

    def build_rules(self, current_path: str, products: list[dict], categories: list[dict]) -> dict[str, Any]:
        """Build a Speculation Rules v1 object."""
        urls = []

        # Always prerender home
        urls.append(f"{self.BASE_URL}/")

        # High-value categories
        for cat in categories[:3]:
            cid = cat.get("category_id")
            if cid:
                urls.append(f"{self.BASE_URL}/index.php?route=product/category&path={cid}")

        # High-value products (exclude current page to avoid waste)
        for prod in products[:3]:
            pid = prod.get("product_id")
            if pid and f"product_id={pid}" not in current_path:
                urls.append(f"{self.BASE_URL}/index.php?route=product/product&product_id={pid}")

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)

        rules = {
            "prerender": [
                {
                    "source": "list",
                    "urls": unique_urls[:5]  # Chromium recommendation: max 5 prerenders
                }
            ],
            "prefetch": [
                {
                    "source": "list",
                    "urls": unique_urls[5:10]  # Next 5 as prefetch
                }
            ]
        }
        return rules

    async def generate_and_save(self, current_path: str = "/") -> dict[str, Any]:
        """Fetch data, build rules, save to OpenCart, return rules."""
        categories = await self.get_top_categories(limit=5)
        products = await self.get_top_products(limit=10)
        rules = self.build_rules(current_path, products, categories)

        # Save to OpenCart via db/executeSql (bypasses PHP BOM issues)
        json_rules = json.dumps(rules, ensure_ascii=False)
        esc = lambda s: s.replace("'", "\\'")
        sql = f"""
        DELETE FROM `oc_setting` WHERE `code` = 'speculation' AND `key` = 'speculation_active_rules';
        INSERT INTO `oc_setting` (`store_id`, `code`, `key`, `value`, `serialized`)
        VALUES ('0', 'speculation', 'speculation_active_rules', '{esc(json_rules)}', '0')
        """
        try:
            await opencart_api.post_action("db/executeSql", {"sql": sql})
        except Exception as exc:
            print(f"[SpeculationEngine] save error: {exc}")

        SpeculationEngine._last_rules = rules

        return {
            "status": "ok",
            "rules": rules,
            "categories_used": len(categories),
            "products_used": len(products)
        }

    async def get_saved_rules(self) -> dict[str, Any] | None:
        """Return in-memory cached rules (also persisted in OpenCart DB)."""
        return SpeculationEngine._last_rules


_speculation_engine = SpeculationEngine()


def get_speculation_engine() -> SpeculationEngine:
    return _speculation_engine
