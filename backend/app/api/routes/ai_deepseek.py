from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.deepseek_client import deepseek_client

router = APIRouter(prefix="/ai/deepseek", tags=["ai-deepseek"])


@router.get("/status")
def deepseek_status():
    return {"status": "ok", "service": "ai_deepseek"}


class ChatRequest(BaseModel):
    prompt: str
    model: str = "deepseek-chat"
    max_tokens: int = 800
    temperature: float = 0.7
    system: str = ""


class ArticleRequest(BaseModel):
    topic: str
    count: int = 1


class KPRequest(BaseModel):
    competitor_name: str
    issues: list[str] = []


@router.post("/chat")
async def deepseek_chat(req: ChatRequest):
    """Универсальный запрос к DeepSeek API"""
    result = await deepseek_client.chat(
        prompt=req.prompt,
        model=req.model,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        system=req.system,
    )
    if result.startswith("[DeepSeek error"):
        raise HTTPException(status_code=502, detail=result)
    return {"status": "ok", "response": result}


@router.post("/generate-article")
async def generate_article(req: ArticleRequest):
    """Генерация SEO-статьи через DeepSeek"""
    articles = []
    for i in range(min(req.count, 10)):
        text = await deepseek_client.generate_article(req.topic)
        articles.append({"id": i + 1, "topic": req.topic, "text": text})
    return {"status": "ok", "articles": articles, "count": len(articles)}


@router.post("/generate-kp")
async def generate_kp(req: KPRequest):
    """Генерация коммерческого предложения через DeepSeek"""
    text = await deepseek_client.generate_kp(req.competitor_name, req.issues)
    return {"status": "ok", "kp_text": text}


@router.get("/status")
async def get_status():
    """Проверка статуса DeepSeek API"""
    key_present = bool(deepseek_client.api_key)
    return {"status": "ok", "deepseek_connected": key_present, "api_key_present": key_present}
