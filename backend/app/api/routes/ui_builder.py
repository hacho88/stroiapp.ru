import json
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.deepseek_client import deepseek_client

router = APIRouter(prefix="/interfaces", tags=["ui-builder"])

ALLOWED_TYPES = {"container", "button", "text", "image", "input"}

SYSTEM_PROMPT = """Ты — генератор UI-деревьев для конструктора интерфейсов строительного маркетплейса.
Твоя задача — по описанию пользователя вернуть СТРОГО валидный JSON-массив объектов UIElement.

Схема UIElement:
{
  "id": "уникальная строка (например el-1, el-2)",
  "type": "container" | "button" | "text" | "image" | "input",
  "name": "читаемое имя слоя (например 'Карточка товара', 'Кнопка купить')",
  "props": {
    "className": "tailwind-классы (обязательно)",
    "text": "текст для type=text/button",
    "src": "url картинки для type=image",
    "placeholder": "плейсхолдер для type=input"
  },
  "children": [ UIElement ]  // только для type=container, опционально
}

Правила:
- Верни ТОЛЬКО JSON-массив. Никакого markdown, никаких ```json, никаких пояснений, комментариев или текста до/после.
- type=container — это div-обёртка, может содержать children.
- Используй реалистичные Tailwind-классы: отступы, сетки (grid/flex), скругления, тени, цвета.
- Тематика — строительный маркетплейс: карточки товаров, цены за м²/шт, артикулы, кнопки "В корзину", калькуляторы, баннеры.
- Для image используй placeholder-URL вида https://placehold.co/600x400.
- Генерируй валидную вложенную структуру. Каждый id уникален.
"""


class GenerateRequest(BaseModel):
    prompt: str
    currentElements: list = []


def clean_ai_json(raw_text: str):
    """Очищает ответ нейросети от markdown-обёрток и текстовых «хвостов»,
    возвращает распарсенный JSON или None."""
    if not raw_text:
        return None
    text = raw_text.strip()
    # снять code-fence ```json ... ```
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # если есть массив — вырезать от первой [ до последней ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
    else:
        # fallback: объект
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except Exception:
        pass
    # salvage: обрезанный массив — закрыть на последнем полном объекте
    if candidate.startswith("["):
        cut = candidate.rfind("}")
        while cut != -1:
            try:
                return json.loads(candidate[:cut + 1] + "]")
            except Exception:
                cut = candidate.rfind("}", 0, cut)
    # последняя попытка — самый широкий массив
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _normalize_element(el, counter):
    """Приводит элемент к валидному UIElement, возвращает dict или None."""
    if not isinstance(el, dict):
        return None
    etype = el.get("type")
    if etype not in ALLOWED_TYPES:
        etype = "container" if el.get("children") else "text"
    counter[0] += 1
    eid = str(el.get("id") or f"el-{counter[0]}")
    props = el.get("props") if isinstance(el.get("props"), dict) else {}
    node = {
        "id": eid,
        "type": etype,
        "name": str(el.get("name") or etype.capitalize()),
        "props": {
            "className": str(props.get("className") or ""),
            **({"text": str(props["text"])} if props.get("text") is not None else {}),
            **({"src": str(props["src"])} if props.get("src") is not None else {}),
            **({"placeholder": str(props["placeholder"])} if props.get("placeholder") is not None else {}),
        },
    }
    children = el.get("children")
    if etype == "container" and isinstance(children, list):
        node["children"] = [c for c in (_normalize_element(x, counter) for x in children) if c]
    return node


def normalize_elements(data):
    """Валидирует и нормализует массив элементов от ИИ."""
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    counter = [0]
    return [e for e in (_normalize_element(x, counter) for x in data) if e]


@router.post("/generate")
async def interfaces_generate(req: GenerateRequest):
    """Генерация/редактирование UI-дерева через DeepSeek. Возвращает UIElement[]."""
    if not deepseek_client.api_key:
        raise HTTPException(status_code=503, detail="DeepSeek API ключ не настроен на сервере")

    context = ""
    if req.currentElements:
        try:
            context = "\n\nТекущее дерево холста (измени/дополни его по запросу):\n" + json.dumps(req.currentElements, ensure_ascii=False)
        except Exception:
            context = ""

    raw = await deepseek_client.chat(
        prompt=req.prompt + context,
        model="deepseek-chat",
        max_tokens=8192,
        temperature=0.4,
        system=SYSTEM_PROMPT,
    )
    if not raw or raw.startswith("[DeepSeek error"):
        raise HTTPException(status_code=502, detail=raw or "DeepSeek вернул пустой ответ")

    data = clean_ai_json(raw)
    elements = normalize_elements(data)
    if not elements:
        raise HTTPException(status_code=422, detail="DeepSeek вернул некорректный JSON. Попробуй переформулировать запрос.")
    return {"status": "ok", "elements": elements}
