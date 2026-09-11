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
    "hero": {"title": "", "subtitle": "", "bg_image": "", "button_text": "", "button_link": ""},
    "text": {"title": "", "body": ""},
    "products": {"title": "", "category_id": 0, "limit": 4},
    "categories": {"title": "", "category_ids": []},
    "image": {"src": "", "alt": "", "caption": ""},
    "video": {"src": "", "title": ""},
    "carousel": {"title": "", "images": []},
    "cta": {"title": "", "button_text": "", "button_link": ""},
    "html": {"html": ""},
}


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Конструктор страниц — раздел работает"}


@router.get("/blocks")
def get_blocks(page: str = "home"):
    return {"status": "ok", "page": page, "blocks": list_blocks(page)}


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
