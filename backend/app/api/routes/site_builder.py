from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from app.db.block_store import (
    list_blocks,
    get_block,
    create_block,
    update_block,
    delete_block,
    reorder_blocks,
)

router = APIRouter(prefix="/site-builder", tags=["site-builder"])


class BlockCreate(BaseModel):
    page: str = Field(default="home", description="Страница: home, about, contacts и т.д.")
    type: str = Field(description="Тип блока: hero, text, products, categories, image, video, carousel, cta, html")
    content: dict[str, Any] = Field(default_factory=dict, description="JSON-контент блока")
    sort_order: int = Field(default=0, ge=0)


class BlockUpdate(BaseModel):
    page: str | None = None
    type: str | None = None
    content: dict[str, Any] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ReorderRequest(BaseModel):
    page: str = Field(default="home")
    ordered_ids: list[int]


BLOCK_TYPES = {
    # Шапка сайта: логотип, подпись под ним, телефон
    "header": {"logo_src": "", "logo_alt": "СТРОЙАПП", "logo_link": "/", "tagline": "", "phone": "", "phone_link": "",
               "promo_text": "Акции", "promo_link": "/#products", "promo_color": ""},
    # Видимость встроенных секций главной (true/false)
    "sections": {"hero": True, "categories": True, "solutions": True, "sale": True, "convenient": True,
                 "recommend": True, "delivery": True, "payment": True, "brands": True, "journal": True},
    "logo": {"src": "", "alt": "", "link": "/"},
    # Глобальная тема: палитра, шрифт, масштаб интерфейса, скругление
    "theme": {"primary_color": "", "accent_color": "", "bg_color": "", "text_color": "", "secondary_color": "",
              "muted_color": "", "border_color": "", "font_family": "", "font_scale": 100, "radius": 0,
              "page_width": 0},
    # Профессиональный hero: слайды (фото/видео/текст), цвета, автопрокрутка, высота
    "hero": {"title": "", "subtitle": "", "bg_image": "", "video": "", "button_text": "", "button_link": "",
             "button_color": "", "slides": [], "autoplay": 5, "height": "medium",
             "overlay": 40, "align": "left", "bg_color": "", "text_color": ""},
    "banner": {"title": "", "subtitle": "", "image": "", "link": "", "button_text": "", "bg_color": "", "text_color": ""},
    "text": {"title": "", "body": "", "bg_color": "", "text_color": ""},
    "products": {"title": "", "category_id": 0, "limit": 4},
    "categories": {"title": "", "category_ids": []},
    "image": {"src": "", "alt": "", "caption": "", "link": ""},
    "video": {"src": "", "title": "", "poster": ""},
    "carousel": {"title": "", "images": [], "slides": [], "autoplay": 0},
    "cta": {"title": "", "subtitle": "", "button_text": "", "button_link": "", "bg_color": "", "text_color": "", "button_color": ""},
    "html": {"html": ""},
    # ---- Редактируемый контент встроенных секций главной ----
    "sec_hero": {
        "eyebrow": "Собираем стройку в один клик", "h1": "", "intro": "",
        "button_text": "Начать покупать", "button_link": "#products",
        "foot1": "Цены от производителя", "foot2": "",
        "side_eyebrow": "Материалы StroiApp", "side_title": "Качество и оптимальная цена",
        "side_button_text": "Смотреть каталог", "side_button_link": "#categories",
    },
    "sec_categories": {"title": "Материалы для строительства", "link_text": "Весь каталог", "link_href": "/search", "limit": 8},
    "sec_solutions": {
        "title": "Калькуляторы и готовые решения",
        "cards": [
            {"title": "Калькулятор скатной кровли", "text": "Подобрать и рассчитать решения из гибкой черепицы и металлочерепицы", "tone": "solution-large", "bg": "linear-gradient(135deg,#5b6770,#2c3338)", "link": ""},
            {"title": "Расчёт материалов для плоской кровли", "text": "Онлайн-калькулятор систем плоских кровель для частного домостроения", "tone": "solution-large", "bg": "linear-gradient(135deg,#8fb3c9,#4a6d85)", "link": ""},
            {"title": "Расчёт фасадов", "text": "Рассчитайте сайдинг, фасадные панели и штукатурные фасады", "tone": "solution-side", "bg": "linear-gradient(135deg,#c9a27e,#8a5f3d)", "link": ""},
            {"title": "Расчёт материалов для фундамента", "text": "Гарантия на водонепроницаемость до 60 лет", "tone": "solution-small", "bg": "", "link": ""},
            {"title": "Расчёт водосточной системы", "text": "Подобрать и рассчитать пластиковую и металлическую систему", "tone": "solution-small", "bg": "", "link": ""},
        ],
        "consult_eyebrow": "Без лишних звонков", "consult_title": "Заказать расчёт материалов",
        "consult_text": "Отдел технических специалистов выполнит профессиональный расчёт по вашим чертежам",
    },
    "sec_convenient": {
        "title": "С нами удобно", "action_text": "Все сервисы", "action_link": "#services",
        "features": [
            {"eyebrow": "Для бизнеса", "title": "Покупайте на юр. лицо", "caption": "Счета, СБП и мультиаккаунт", "tone": "b2b", "link": ""},
            {"eyebrow": "Сервис", "title": "Строительный надзор StroiApp", "caption": "Кровли и фасады. Бесплатно.", "tone": "audit", "link": ""},
            {"eyebrow": "Сервис", "title": "Поможем найти подрядчика", "caption": "Для ИЖС и ПГС", "tone": "contractor", "link": ""},
        ],
        "services": [
            {"icon": "store", "title": "СБП b2b", "text": "Мгновенные платежи между юридическими лицами", "link": ""},
            {"icon": "hammer", "title": "Сопровождение монтажа", "text": "Контроль качества кровельных работ на каждом этапе", "link": ""},
            {"icon": "shield", "title": "Аппаратный поиск протечек", "text": "Найдём причину протечек на плоской кровле", "link": ""},
            {"icon": "clipboard", "title": "Сметы", "text": "Смета на материалы. Формируйте и управляйте заказом", "link": ""},
        ],
    },
    "sec_delivery": {
        "eyebrow": "StroiApp везёт", "title": "Доставка 100 за 100", "subtitle": "100 ₽ от 100 кг по Москве и области",
        "button_text": "Рассчитать доставку", "button_link": "",
        "cards": [
            {"title": "Больше брендов —", "subtitle": "больше выбор", "tone": "promo-mint", "link": "#brands"},
            {"title": "Поиск", "subtitle": "протечек на плоской кровле", "tone": "promo-roof", "link": ""},
            {"title": "Принимаем оплаты", "subtitle": "от юр. лиц", "tone": "promo-green", "link": ""},
        ],
    },
    "sec_payment": {
        "title": "Оплата и бонусы",
        "payments": [
            {"icon": "card", "title": "Наличные и карта", "text": "Оплата при получении на объекте или в пункте выдачи"},
            {"icon": "file", "title": "Безнал с НДС", "text": "Счёт для юрлиц за 5 минут, ЭДО и полный пакет документов"},
            {"icon": "phone", "title": "СБП и онлайн", "text": "Мгновенная оплата по QR-коду или ссылке без комиссии"},
        ],
        "bonus_eyebrow": "Программа лояльности", "bonus_title": "Бонусы за каждый заказ",
        "bonus_text": "5% от суммы покупки возвращается баллами — ими можно оплатить до 20% следующего заказа. Для бригад и прорабов — повышенный кэшбэк.",
        "bonus_button": "Получить бонусы", "bonus_link": "",
    },
    "sec_brands": {
        "title": "Бренды",
        "brands": [
            {"name": "ТЕХНОНИКОЛЬ", "link": ""}, {"name": "aquasystem", "link": ""}, {"name": "knauf", "link": ""},
            {"name": "Церезит", "link": ""}, {"name": "FAKRO", "link": ""}, {"name": "decover", "link": ""},
            {"name": "stroiapp", "link": ""}, {"name": "ПЕНОПЛЭКС", "link": ""}, {"name": "Изоспан", "link": ""},
        ],
    },
    "sec_journal": {
        "title": "Журнал для тех, кто строит",
        "articles": [
            {"category": "Продукт", "title": "Как подготовить поверхность перед нанесением битумной мастики", "tone": "article-dark", "link": ""},
            {"category": "Прогресс", "title": "Карьерные проекты в торговой сети StroiApp", "tone": "article-blue", "link": ""},
            {"category": "Производство", "title": "Электронный документооборот: плюсы для бизнеса", "tone": "article-grey", "link": ""},
            {"category": "Просервис", "title": "Как выбрать подрядчика и построить загородный дом", "tone": "article-warm", "link": ""},
            {"category": "Видео", "title": "Как построить дом из газоблоков: важные этапы", "tone": "article-red", "link": ""},
        ],
    },
}


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Конструктор страниц — раздел работает"}

@router.get("/blocks")
def get_blocks(page: str = "home", all: bool = True):
    return {"status": "ok", "page": page, "blocks": list_blocks(page, include_inactive=all)}


@router.get("/public/blocks")
def get_public_blocks(page: str = "home"):
    """Публичный endpoint для stroiapp.ru (без авторизации)"""
    return {"status": "ok", "page": page, "blocks": list_blocks(page)}


@router.get("/block-types")
def get_block_types():
    return {"status": "ok", "types": BLOCK_TYPES}


@router.post("/blocks")
def create(payload: BlockCreate):
    block_id = create_block(payload.page, payload.type, payload.content, payload.sort_order)
    return {"status": "ok", "id": block_id}


@router.get("/blocks/{block_id}")
def read(block_id: int):
    block = get_block(block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Блок не найден")
    return {"status": "ok", "block": block}


@router.put("/blocks/{block_id}")
def update(block_id: int, payload: BlockUpdate):
    ok = update_block(
        block_id,
        page=payload.page,
        type=payload.type,
        content=payload.content,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Блок не найден или нечего обновлять")
    return {"status": "ok", "id": block_id}


@router.delete("/blocks/{block_id}")
def remove(block_id: int):
    ok = delete_block(block_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Блок не найден")
    return {"status": "ok", "id": block_id}


@router.post("/reorder")
def reorder(payload: ReorderRequest):
    reorder_blocks(payload.page, payload.ordered_ids)
    return {"status": "ok", "page": payload.page}
