from app.models.product import BudgetSelection, Product


MIN_ROI = 120
STANDARD_BUDGETS = [5000, 10000, 20000, 50000, 100000]


class DashboardService:
    def calculate(self, budget: float, products: list[Product]) -> BudgetSelection:
        ranked = sorted(products, key=lambda product: product.roi, reverse=True)
        selected: list[Product] = []
        spent = 0.0

        for product in ranked:
            if product.roi < MIN_ROI:
                break
            if spent + product.ad_budget > budget:
                continue
            selected.append(product)
            spent += product.ad_budget

        return BudgetSelection(
            budget=budget,
            spent=round(spent, 2),
            saved=round(budget - spent, 2),
            products=selected,
            expected_orders=round(sum(product.expected_orders for product in selected), 2),
            expected_profit=round(sum(product.expected_profit for product in selected), 2),
        )

    def compare(self, products: list[Product]) -> list[BudgetSelection]:
        return [self.calculate(budget, products) for budget in STANDARD_BUDGETS]


dashboard_service = DashboardService()
