from pydantic import BaseModel


class SEORequest(BaseModel):
    sku: str
    name: str
    specs: dict[str, str] = {}


class FAQItem(BaseModel):
    question: str
    answer: str


class InvoiceRequest(BaseModel):
    inn: str
    email: str
    order_id: int | None = None


class BannerRequest(BaseModel):
    title: str
    subtitle: str
    url: str | None = None


class TelegramRequest(BaseModel):
    chat_id: str | None = None
    message: str
