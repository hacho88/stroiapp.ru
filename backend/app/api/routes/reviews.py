from fastapi import APIRouter
from app.db.competitor_store import list_competitors
from app.services.deepseek_client import deepseek_client

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Отзывы и репутация — раздел работает"}


@router.post("/parse-competitors")
async def parse_competitor_reviews(payload: dict):
    """Парсинг негативных отзывов о конкурентах (Яндекс.Карты, 2ГИС) — заглушка с шаблонными данными"""
    competitors = list_competitors()
    reviews = []
    for c in competitors[:5]:
        reviews.append({
            "competitor": c["name"],
            "source": "Яндекс.Карты",
            "rating": 3.2,
            "negative_count": 4,
            "issues": ["Долгая доставка", "Высокие цены", "Нет безналичного расчёта"],
        })
    if not reviews:
        reviews = [{
            "competitor": "Пример конкурента",
            "source": "Яндекс.Карты",
            "rating": 2.8,
            "negative_count": 6,
            "issues": ["Долгая доставка", "Некомпетентные менеджеры", "Нет СНДС"],
        }]
    return {"reviews": reviews, "negative_count": sum(r["negative_count"] for r in reviews), "sources": ["Яндекс.Карты", "2ГИС"]}


@router.post("/generate-kp")
async def generate_kp(payload: dict):
    """Генерация коммерческого предложения на основе слабых сторон конкурентов"""
    target = payload.get("competitor_name", "Конкурент")
    issues = payload.get("issues", ["Долгая доставка", "Высокие цены", "Нет безналичного расчёта"])
    if deepseek_client.api_key:
        kp_text = await deepseek_client.generate_kp(target, issues)
    else:
        kp_text = f"""Коммерческое предложение — StroiApp.ru

Уважаемый клиент!

Мы проанализировали отзывы о {target} и предлагаем вам лучшие условия:

✅ Быстрая доставка по Москве и МО — от 2 часов
✅ Безналичный расчёт с НДС — для юрлиц
✅ Оптовые цены на стройматериалы
✅ Собственный склад — всё в наличии
✅ Персональный менеджер

С уважением, команда StroiApp.ru
Тел: +7 (XXX) XXX-XX-XX"""
    return {"kp_text": kp_text, "target": target}
