from app.models.product import Product
from app.db.cost_store import get_all_costs, save_costs
from app.services.opencart_dump import load_products_from_dump


class ProductDB:
    def __init__(self) -> None:
        imported_products = load_products_from_dump(limit=500)
        if imported_products:
            self._products = {product.sku: product for product in imported_products}
        else:
            self._products: dict[str, Product] = {
                "0001": Product(sku="0001", name="Цемент М500 50 кг", cost_price_cash=360, cost_price_cashless=380, retail_price=520, wholesale_price=490, expected_orders=18, expected_profit=1980, optimal_cpc=42, optimal_position=2, traffic_share=0.85, roi=262, ad_budget=756),
                "0002": Product(sku="0002", name="Пескобетон М300 40 кг", cost_price_cash=165, cost_price_cashless=178, retail_price=260, wholesale_price=245, expected_orders=28, expected_profit=1876, optimal_cpc=31, optimal_position=2, traffic_share=0.82, roi=216, ad_budget=868),
                "0003": Product(sku="0003", name="Арматура А500С 12 мм", cost_price_cash=52, cost_price_cashless=55, retail_price=78, wholesale_price=73, expected_orders=120, expected_profit=2160, optimal_cpc=24, optimal_position=3, traffic_share=0.72, roi=75, ad_budget=2880),
            }
        self._apply_saved_costs()

    def _recalculate(self, product: Product) -> Product:
        cost = product.cost_price_cash or product.cost_price_cashless
        product.expected_profit = round(max(product.retail_price - cost, 0) * max(product.expected_orders, 1), 2)
        product.roi = round((product.expected_profit / product.ad_budget) * 100, 2) if product.ad_budget else 0
        return product

    def _apply_saved_costs(self) -> None:
        for sku, costs in get_all_costs().items():
            product = self._products.get(sku)
            if product:
                product.cost_price_cash = costs[0]
                product.cost_price_cashless = costs[1]
                if costs[2] > 0:
                    product.retail_price = costs[2]
                if costs[3] > 0:
                    product.wholesale_price = costs[3]
                self._recalculate(product)

    def list_products(self) -> list[Product]:
        return list(self._products.values())

    def list_products_filtered(
        self,
        search: str = "",
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_roi: float | None = None,
        sort_by: str = "name",
        limit: int = 500,
        offset: int = 0,
    ) -> dict:
        """Список товаров с поиском, фильтрацией, сортировкой и пагинацией."""
        items = list(self._products.values())

        # Поиск по названию/SK
        if search:
            search_lower = search.lower()
            items = [p for p in items if search_lower in (p.name or "").lower() or search_lower in p.sku.lower()]

        # Фильтр по категории
        if category_id is not None:
            items = [p for p in items if p.category_id == category_id]

        # Фильтр по цене
        if min_price is not None:
            items = [p for p in items if p.retail_price >= min_price]
        if max_price is not None:
            items = [p for p in items if p.retail_price <= max_price]

        # Фильтр по ROI
        if min_roi is not None:
            items = [p for p in items if p.roi >= min_roi]

        # Сортировка
        sort_map = {
            "name": lambda p: (p.name or "").lower(),
            "price": lambda p: p.retail_price,
            "price_desc": lambda p: -p.retail_price,
            "roi": lambda p: -p.roi,
            "profit": lambda p: -p.expected_profit,
            "sku": lambda p: p.sku,
        }
        items.sort(key=sort_map.get(sort_by, sort_map["name"]))

        total = len(items)
        items = items[offset:offset + limit]

        return {
            "products": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "returned": len(items),
        }

    def bulk_add_products(self, products_data: list[dict]) -> dict:
        """Массовое добавление товаров."""
        added = 0
        skipped = 0
        errors = []
        for i, data in enumerate(products_data):
            sku = (data.get("sku") or "").strip()
            name = (data.get("name") or "").strip()
            if not sku or not name:
                skipped += 1
                errors.append({"index": i, "error": "sku и name обязательны"})
                continue
            if sku in self._products:
                skipped += 1
                errors.append({"index": i, "sku": sku, "error": "уже существует"})
                continue
            try:
                self.add_product(sku=sku, name=name, **{k: v for k, v in data.items() if k not in ("sku", "name")})
                added += 1
            except Exception as exc:
                skipped += 1
                errors.append({"index": i, "sku": sku, "error": str(exc)})
        return {"added": added, "skipped": skipped, "errors": errors}

    def get_by_sku(self, sku: str) -> Product | None:
        return self._products.get(sku)

    def upsert_costs(self, sku: str, cost_price_cash: float, cost_price_cashless: float, retail_price: float | None = None, wholesale_price: float | None = None) -> Product:
        product = self._products.get(sku) or Product(sku=sku, name=f"Товар {sku}")
        product.cost_price_cash = cost_price_cash
        product.cost_price_cashless = cost_price_cashless
        if retail_price is not None:
            product.retail_price = retail_price
        if wholesale_price is not None:
            product.wholesale_price = wholesale_price
        self._recalculate(product)
        save_costs(sku, cost_price_cash, cost_price_cashless, product.retail_price, product.wholesale_price)
        self._products[sku] = product
        return product

    def add_product(self, sku: str, name: str, **kwargs) -> Product:
        """Добавляет новый товар в базу."""
        if sku in self._products:
            raise ValueError(f"Товар {sku} уже существует")
        product = Product(sku=sku, name=name, **kwargs)
        self._recalculate(product)
        if product.cost_price_cash or product.cost_price_cashless:
            save_costs(sku, product.cost_price_cash, product.cost_price_cashless, product.retail_price, product.wholesale_price)
        self._products[sku] = product
        return product

    def edit_product(self, sku: str, **kwargs) -> Product | None:
        """Редактирует существующий товар."""
        product = self._products.get(sku)
        if not product:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)
        self._recalculate(product)
        if product.cost_price_cash or product.cost_price_cashless:
            save_costs(sku, product.cost_price_cash, product.cost_price_cashless, product.retail_price, product.wholesale_price)
        return product

    def delete_product(self, sku: str) -> bool:
        """Удаляет товар из базы."""
        if sku not in self._products:
            return False
        del self._products[sku]
        return True

    def bulk_upsert_costs(self, rows: list[dict[str, str]]) -> dict[str, int]:
        imported = 0
        skipped = 0
        for row in rows:
            sku = (row.get("sku") or "").strip()
            if not sku:
                skipped += 1
                continue
            try:
                cost_price_cash = float((row.get("cost_price_cash") or "0").replace(",", "."))
                cost_price_cashless = float((row.get("cost_price_cashless") or "0").replace(",", "."))
                retail_price = float((row.get("retail_price") or "0").replace(",", ".")) or None
                wholesale_price = float((row.get("wholesale_price") or "0").replace(",", ".")) or None
            except ValueError:
                skipped += 1
                continue
            self.upsert_costs(sku, cost_price_cash, cost_price_cashless, retail_price, wholesale_price)
            imported += 1
        return {"imported": imported, "skipped": skipped}

    def reload_from_dump(self) -> int:
        imported_products = load_products_from_dump(limit=500)
        if imported_products:
            self._products = {product.sku: product for product in imported_products}
            self._apply_saved_costs()
        return len(imported_products)

    def calculate_prices_for_foreman(self, skus: list[str], margin_retail: float = 1.35, margin_wholesale: float = 1.25) -> list[dict]:
        """Прораб загружает список SKU — система ищет в ProductDB и считает цены."""
        results = []
        for sku in skus:
            sku_clean = sku.strip()
            product = self._products.get(sku_clean)
            if product:
                cost = product.cost_price_cash or product.cost_price_cashless or 0
                retail = product.retail_price if product.retail_price > 0 else round(cost * margin_retail, 2)
                wholesale = product.wholesale_price if product.wholesale_price > 0 else round(cost * margin_wholesale, 2)
                results.append({
                    "sku": sku_clean,
                    "name": product.name,
                    "found": True,
                    "cost_price_cash": product.cost_price_cash,
                    "cost_price_cashless": product.cost_price_cashless,
                    "retail_price": retail,
                    "wholesale_price": wholesale,
                    "expected_profit": product.expected_profit,
                    "roi": product.roi,
                })
            else:
                results.append({
                    "sku": sku_clean,
                    "name": None,
                    "found": False,
                    "cost_price_cash": None,
                    "cost_price_cashless": None,
                    "retail_price": None,
                    "wholesale_price": None,
                    "expected_profit": None,
                    "roi": None,
                })
        return results

    def sync_from_opencart(self, rows: list[dict]) -> int:
        """Наполнить/обновить каталог из живого OpenCart (product/list).

        Сохраняет уже заданные себестоимость/метрики: каталожные поля
        (название, фото, остаток, product_id) обновляются, розничная цена
        подставляется только если ещё не задана вручную.
        """
        count = 0
        for row in rows:
            try:
                pid = int(row.get("product_id") or 0)
                price = float(row.get("price") or 0)
                qty = int(float(row.get("quantity") or 0))
            except (TypeError, ValueError):
                continue
            sku = (row.get("sku") or "").strip() or (str(pid).zfill(4) if pid else "")
            if not sku:
                continue
            existing = self._products.get(sku)
            if existing:
                existing.product_id = pid or existing.product_id
                existing.name = row.get("name") or existing.name
                existing.model = row.get("model") or existing.model
                existing.image = row.get("image") or existing.image
                existing.quantity = qty
                if price > 0 and not existing.retail_price:
                    existing.retail_price = price
            else:
                self._products[sku] = Product(
                    product_id=pid,
                    sku=sku,
                    name=row.get("name") or row.get("model") or f"Товар {sku}",
                    model=row.get("model") or "",
                    image=row.get("image") or "",
                    quantity=qty,
                    retail_price=price,
                )
            count += 1
        self._apply_saved_costs()
        return count


product_db = ProductDB()
