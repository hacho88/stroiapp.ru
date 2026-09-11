"""Yandex Metrika API integration.

Provides traffic stats (visits, users, pageviews) for stroiapp.ru
via Yandex Metrika API (counter 104445687).
"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrika", tags=["metrika"])

METRIKA_BASE = "https://api-metrika.yandex.net"
COUNTER_ID = "112359058"


def _headers() -> dict:
    token = settings.yandex_metrika_token or settings.yandex_webmaster_token
    if not token:
        raise HTTPException(status_code=400, detail="Yandex token не настроен в .env")
    return {
        "Authorization": f"OAuth {token}",
        "Content-Type": "application/json",
        "Accept-Language": "ru",
    }


@router.get("/status")
async def metrika_status():
    """Статус доступа к Metrika API."""
    token = settings.yandex_metrika_token or settings.yandex_webmaster_token
    info = {
        "status": "ok",
        "service": "yandex_metrika",
        "counter_id": COUNTER_ID,
        "token_configured": bool(token),
    }
    if token:
        try:
            async with httpx.AsyncClient(verify=False, timeout=15) as client:
                r = await client.get(
                    f"{METRIKA_BASE}/management/v1/counter/{COUNTER_ID}",
                    headers=_headers(),
                )
                if r.status_code == 200:
                    counter = r.json().get("counter", {})
                    info["access"] = True
                    info["counter_name"] = counter.get("name")
                    info["site"] = counter.get("site")
                elif r.status_code == 403:
                    info["access"] = False
                    info["detail"] = "Токен без прав metrika:read. Добавьте scope в OAuth-приложении и получите новый токен."
                else:
                    info["error"] = r.text[:200]
        except Exception as e:
            info["error"] = str(e)[:200]
    return info


@router.get("/traffic")
async def metrika_traffic(period: str = "month"):
    """Счётчики трафика: визиты, посетители, просмотры за период."""
    token = settings.yandex_metrika_token or settings.yandex_webmaster_token
    if not token:
        raise HTTPException(status_code=400, detail="Yandex token не настроен в .env")

    period_days = {"day": 1, "week": 7, "month": 30}.get(period, 30)
    metrics = "ym:s:visits,ym:s:users,ym:s:pageviews,ym:s:bounceRate,ym:s:avgVisitDurationSeconds"

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        try:
            r = await client.get(
                f"{METRIKA_BASE}/stat/v1/data",
                headers=_headers(),
                params={
                    "id": COUNTER_ID,
                    "metrics": metrics,
                    "period": period,
                },
            )
            if r.status_code == 403:
                return {
                    "status": "access_denied",
                    "detail": "Нет прав metrika:read. Добавьте scope в OAuth-приложении и получите новый токен.",
                }
            r.raise_for_status()
            data = r.json()
            totals = data.get("totals", [0, 0, 0, 0])
            return {
                "status": "ok",
                "period": period,
                "visits": totals[0] if len(totals) > 0 else 0,
                "users": totals[1] if len(totals) > 1 else 0,
                "pageviews": totals[2] if len(totals) > 2 else 0,
                "bounce_rate": totals[3] if len(totals) > 3 else 0,
                "avg_visit_duration": totals[4] if len(totals) > 4 else 0,
            }
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": e.response.text[:300]}
        except Exception as e:
            return {"status": "error", "detail": str(e)[:300]}


@router.get("/traffic/daily")
async def traffic_daily(days: int = 30):
    """Динамика трафика по дням для графика."""
    token = settings.yandex_metrika_token or settings.yandex_webmaster_token
    if not token:
        raise HTTPException(status_code=400, detail="Yandex token не настроен в .env")

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        try:
            r = await client.get(
                f"{METRIKA_BASE}/stat/v1/data/bytime",
                headers=_headers(),
                params={
                    "id": COUNTER_ID,
                    "metrics": "ym:s:visits,ym:s:users",
                    "period": "day",
                    "last_days": min(days, 90),
                },
            )
            if r.status_code == 403:
                return {"status": "access_denied", "detail": "Нет прав metrika:read"}
            r.raise_for_status()
            data = r.json()
            return {
                "status": "ok",
                "dates": data.get("time_intervals", []),
                "visits": data.get("data", [{}])[0].get("metrics", [[]])[0] if data.get("data") else [],
                "users": data.get("data", [{}])[0].get("metrics", [[], []])[1] if data.get("data") else [],
            }
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": e.response.text[:300]}
        except Exception as e:
            return {"status": "error", "detail": str(e)[:300]}


@router.get("/top-pages")
async def top_pages(limit: int = 10):
    """Топ страниц по просмотрам."""
    token = settings.yandex_metrika_token or settings.yandex_webmaster_token
    if not token:
        raise HTTPException(status_code=400, detail="Yandex token не настроен в .env")

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        try:
            r = await client.get(
                f"{METRIKA_BASE}/stat/v1/data",
                headers=_headers(),
                params={
                    "id": COUNTER_ID,
                    "metrics": "ym:s:pageviews",
                    "dimensions": "ym:s:URLPath",
                    "period": "month",
                    "limit": min(limit, 50),
                    "sort": "-ym:s:pageviews",
                },
            )
            if r.status_code == 403:
                return {"status": "access_denied", "detail": "Нет прав metrika:read"}
            r.raise_for_status()
            data = r.json()
            pages = []
            for row in data.get("data", []):
                dims = row.get("dimensions", [{}])
                pages.append({
                    "path": dims[0].get("name", "") if dims else "",
                    "pageviews": row.get("metrics", [0])[0],
                })
            return {"status": "ok", "pages": pages}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": e.response.text[:300]}
        except Exception as e:
            return {"status": "error", "detail": str(e)[:300]}
