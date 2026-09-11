from fastapi import APIRouter, HTTPException
from app.services.opencart_api import opencart_api
from app.services.product_db import product_db

router = APIRouter(prefix="/budget-roi", tags=["budget-roi"])

MARKUP = 1.285


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Бюджет и окупаемость — раздел работает"}


@router.post("/calculate")
async def calculate_budget(payload: dict):
    """ИИ подбирает товары для рекламы по заданному бюджету"""
    budget = payload.get("budget", 0)
    if budget <= 0:
        raise HTTPException(status_code=400, detail="Бюджет должен быть больше 0")

    try:
        products = await opencart_api.get_action("product/list", {"limit": 500})
        items = products.get("products", []) if isinstance(products, dict) else []
        if not items:
            items = products if isinstance(products, list) else []
    except Exception:
        items = []

    # Fallback: используем локальную базу товаров если OpenCart недоступен
    if not items:
        items = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "price": p.retail_price,
                "cash_price": p.cost_price_cash,
                "non_cash_price": p.cost_price_cashless,
            }
            for p in product_db.list_products() if p.retail_price > 0
        ]

    # Рассчитаем прибыльность каждого товара: margin = price - cash_price
    scored = []
    for p in items:
        price = float(p.get("price", 0) or 0)
        cash = float(p.get("cash_price", 0) or 0)
        non_cash = float(p.get("non_cash_price", 0) or 0)
        price_non_cash = price * MARKUP if price > 0 else float(p.get("price_non_cash", 0) or 0)
        margin_nal = price - cash if cash > 0 else price * 0.25
        margin_beznal = price_non_cash - non_cash if non_cash > 0 else price_non_cash * 0.25
        # Средняя маржа
        margin = (margin_nal + margin_beznal) / 2
        margin_pct = round((margin / price) * 100, 1) if price > 0 else 0
        scored.append({
            "product_id": p.get("product_id"),
            "name": p.get("name", ""),
            "price": price,
            "price_non_cash": round(price_non_cash, 2),
            "cash_price": cash,
            "non_cash_price": non_cash,
            "margin": round(margin, 2),
            "margin_pct": margin_pct,
        })

    # Сортируем по марже (прибыльность)
    scored.sort(key=lambda x: x["margin"], reverse=True)

    # Подбираем товары под бюджет (budget = сумма рекламных расходов ≈ 20% от выручки)
    # Для упрощения: бюджет делим на стоимость товаров (закуп)
    selected = []
    total_cost = 0
    for s in scored:
        cost = s["cash_price"] if s["cash_price"] > 0 else s["price"] * 0.6
        if total_cost + cost <= budget:
            selected.append(s)
            total_cost += cost
        if len(selected) >= 20:
            break

    estimated_revenue = sum(p["price"] for p in selected)
    estimated_profit = sum(p["margin"] for p in selected)
    roi = round((estimated_profit / budget) * 100, 1) if budget > 0 else 0
    break_even_days = int(budget / (estimated_profit / 30)) if estimated_profit > 0 else 0

    return {
        "budget": budget,
        "selected_products": selected,
        "selected_count": len(selected),
        "total_cost": round(total_cost, 2),
        "estimated_revenue": round(estimated_revenue, 2),
        "estimated_profit": round(estimated_profit, 2),
        "estimated_roi": roi,
        "break_even_days": break_even_days,
    }


@router.get("/forecast")
async def get_forecast(days: int = 30):
    """Прогноз прибыли и график окупаемости"""
    forecast = []
    daily_profit = 5000  # placeholder
    cumulative = 0
    for d in range(1, days + 1):
        cumulative += daily_profit
        forecast.append({"day": d, "profit": daily_profit, "cumulative": cumulative})
    return {
        "forecast": forecast,
        "total_revenue": daily_profit * days * 3,
        "total_cost": daily_profit * days * 2,
        "profit": daily_profit * days,
    }
