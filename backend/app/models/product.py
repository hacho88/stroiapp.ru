from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: int | None = None
    sku: str = Field(..., examples=["0001"])
    name: str
    model: str = ""
    image: str = ""
    quantity: int = 0
    cost_price_cash: float = 0
    cost_price_cashless: float = 0
    retail_price: float = 0
    wholesale_price: float = 0
    expected_orders: float = 0
    expected_profit: float = 0
    optimal_cpc: float = 0
    optimal_position: int = 2
    traffic_share: float = 0
    roi: float = 0
    ad_budget: float = 0
    description: str = ""
    meta_title: str = ""
    meta_description: str = ""
    meta_keyword: str = ""
    category_id: int = 0


class ProductCreate(BaseModel):
    sku: str
    name: str
    model: str = ""
    quantity: int = 0
    cost_price_cash: float = 0
    cost_price_cashless: float = 0
    retail_price: float = 0
    wholesale_price: float = 0
    category_id: int = 0
    description: str = ""
    image: str = ""
    generate_ai: bool = False


class ProductUpdate(BaseModel):
    name: str | None = None
    model: str | None = None
    quantity: int | None = None
    cost_price_cash: float | None = None
    cost_price_cashless: float | None = None
    retail_price: float | None = None
    wholesale_price: float | None = None
    category_id: int | None = None
    description: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keyword: str | None = None
    image: str | None = None


class ProductPriceInput(BaseModel):
    sku: str
    cost_price_cash: float
    cost_price_cashless: float
    retail_price: float | None = None
    wholesale_price: float | None = None


class BudgetRequest(BaseModel):
    budget: float


class BudgetSelection(BaseModel):
    budget: float
    spent: float
    saved: float
    products: list[Product]
    expected_orders: float
    expected_profit: float
