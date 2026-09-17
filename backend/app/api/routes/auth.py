import hashlib
import hmac

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def expected_token() -> str:
    raw = f"{settings.admin_login}:{settings.admin_password}:{settings.auth_secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_token(token: str) -> bool:
    return hmac.compare_digest(token or "", expected_token())


class LoginPayload(BaseModel):
    login: str
    password: str


@router.post("/login")
async def login(payload: LoginPayload):
    if payload.login == settings.admin_login and payload.password == settings.admin_password:
        return {"token": expected_token(), "login": settings.admin_login}
    return JSONResponse(status_code=401, content={"error": "Неверный логин или пароль"})


@router.get("/check")
async def check(token: str = ""):
    if verify_token(token):
        return {"ok": True}
    return JSONResponse(status_code=401, content={"error": "unauthorized"})
