"""Yandex Webmaster API integration.

Provides endpoints for monitoring site indexing, sitemap management,
and requesting page re-crawling via Yandex Webmaster API v4.
"""
import logging
import urllib.parse
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webmaster", tags=["webmaster"])

WM_API = "https://api.webmaster.yandex.net/v4"
SITE_URL = "https://stroiapp.ru/"


def _headers() -> dict:
    token = settings.yandex_webmaster_token
    if not token:
        raise HTTPException(status_code=400, detail="YANDEX_WEBMASTER_TOKEN не настроен в .env")
    return {
        "Authorization": f"OAuth {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json",
    }


WM_BASE = "https://api.webmaster.yandex.net/v4"
_uid_cache: Optional[int] = None


async def _ensure_user_id() -> int:
    global _uid_cache
    if _uid_cache is None:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            r = await client.get(f"{WM_BASE}/user", headers=_headers())
            r.raise_for_status()
            _uid_cache = r.json()["user_id"]
    return _uid_cache


def _host_id_enc() -> str:
    return urllib.parse.quote("https:stroiapp.ru:443", safe="")


@router.get("/status")
async def webmaster_status():
    """Статус подключения к Yandex Webmaster API."""
    token_set = bool(settings.yandex_webmaster_token)
    info = {"status": "ok", "service": "yandex_webmaster", "token_configured": token_set}
    if token_set:
        try:
            uid = await _ensure_user_id()
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                r = await client.get(f"{WM_BASE}/user/{uid}/hosts", headers=_headers())
                r.raise_for_status()
                hosts = r.json().get("hosts", [])
                info["hosts"] = [
                    {
                        "host_id": h.get("host_id"),
                        "url": h.get("unicode_host_url"),
                        "verified": h.get("verified"),
                    }
                    for h in hosts
                ]
        except Exception as e:
            info["error"] = str(e)[:200]
    return info


@router.get("/host/summary")
async def host_summary():
    """Общая информация о сайте: количество страниц в индексе, статус."""
    uid = await _ensure_user_id()
    url = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}/summary"
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(url, headers=_headers())
        if r.status_code == 404:
            return {"status": "host_not_loaded", "detail": "Хост ещё загружается в Вебмастер. Подождите несколько часов."}
        r.raise_for_status()
        return r.json()


@router.get("/sitemaps")
async def get_sitemaps(limit: int = 50):
    """Список sitemap файлов со статусом индексации."""
    uid = await _ensure_user_id()
    url = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}/sitemaps"
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(url, headers=_headers(), params={"limit": min(limit, 100)})
        if r.status_code == 404:
            return {"sitemaps": [], "detail": "Хост ещё не загружен в Вебмастер"}
        r.raise_for_status()
        return r.json()


@router.post("/sitemaps/add")
async def add_sitemap(payload: dict):
    """Добавить sitemap в Яндекс.Вебмастер."""
    sitemap_url = payload.get("url", "https://stroiapp.ru/sitemap.xml")
    uid = await _ensure_user_id()
    url = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}/user-added-sitemaps"
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.post(url, headers=_headers(), json={"url": sitemap_url})
        if r.status_code == 409:
            return {"status": "already_added", "detail": "Sitemap уже добавлен"}
        r.raise_for_status()
        return r.json()


@router.get("/sitemaps/{sitemap_id}")
async def sitemap_details(sitemap_id: str):
    """Детальная информация о sitemap: статус, количество URL, ошибки."""
    uid = await _ensure_user_id()
    url = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}/sitemaps/{urllib.parse.quote(sitemap_id, safe='')}"
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(url, headers=_headers())
        if r.status_code == 404:
            return {"status": "not_found", "detail": "Хост или sitemap ещё не загружены"}
        r.raise_for_status()
        return r.json()


@router.post("/recrawl")
async def request_recrawl(payload: dict):
    """Запрос переобхода страницы (до 100 URL за раз)."""
    urls = payload.get("urls", [])
    if not urls:
        raise HTTPException(status_code=400, detail="urls обязателен")
    if len(urls) > 100:
        raise HTTPException(status_code=400, detail="Максимум 100 URL за раз")

    uid = await _ensure_user_id()
    url = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}/recrawl"
    results = []
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        for u in urls:
            try:
                r = await client.post(url, headers=_headers(), json={"url": u})
                if r.status_code == 200:
                    result = {"url": u, "status": "queued"}
                else:
                    result = {"url": u, "status": "error", "detail": r.text[:200]}
                results.append(result)
            except httpx.HTTPStatusError as e:
                results.append({"url": u, "status": "error", "detail": str(e.response.text)[:200]})
            except Exception as e:
                results.append({"url": u, "status": "error", "detail": str(e)[:200]})
    return {"results": results, "count": len(results)}


@router.get("/indexing/stats")
async def indexing_stats():
    """Статистика индексации: страницы в поиске, исключённые страницы."""
    uid = await _ensure_user_id()
    base = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}"
    result = {}
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        for name, endpoint in [
            ("summary", "/summary"),
            ("indexing", "/indexing-summary"),
            ("search_issues", "/search-issues"),
        ]:
            try:
                r = await client.get(base + endpoint, headers=_headers())
                r.raise_for_status()
                result[name] = r.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    result[name] = {"status": "not_available_yet"}
                else:
                    result[name] = {"error": e.response.text[:200]}
            except Exception as e:
                result[name] = {"error": str(e)[:200]}
    return result


@router.get("/counters")
async def counters():
    """Счётчики для дашборда: страницы в поиске, в индексе, исключённые, проблемы, sitemap."""
    if not settings.yandex_webmaster_token:
        return {"available": False, "detail": "Токен не настроен"}
    uid = await _ensure_user_id()
    base = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}"

    counters = {
        "available": True,
        "searchable_pages": None,
        "downloaded_pages": None,
        "excluded_pages": None,
        "site_problems": None,
        "sitemaps_count": None,
        "sitemaps_urls": None,
        "sitemap_errors": 0,
        "host_loaded": True,
    }

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        # Summary: pages in search
        try:
            r = await client.get(f"{base}/summary", headers=_headers())
            r.raise_for_status()
            data = r.json()
            counters["searchable_pages"] = data.get("searchable_pages_count")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                counters["host_not_loaded"] = True
            else:
                counters["summary_error"] = e.response.text[:200]
        except Exception as e:
            counters["summary_error"] = str(e)[:200]

        # Indexing summary: downloaded / excluded pages
        try:
            r = await client.get(f"{base}/indexing-summary", headers=_headers())
            r.raise_for_status()
            idx = r.json()
            indicators = {i.get("indicator"): i for i in idx.get("indicators", []) if isinstance(i, dict)}
            counters["downloaded_pages"] = (indicators.get("DOWNLOADED_PAGES") or {}).get("value")
            counters["searched_pages"] = (indicators.get("SEARCHED_PAGES") or {}).get("value")
            counters["excluded_pages"] = (indicators.get("EXCLUDED_PAGES") or {}).get("value")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                counters["indexing_error"] = e.response.text[:200]
        except Exception as e:
            counters["indexing_error"] = str(e)[:200]

        # Sitemaps
        try:
            r = await client.get(f"{base}/sitemaps", headers=_headers(), params={"limit": 100})
            r.raise_for_status()
            sm_list = r.json().get("sitemaps", [])
            counters["sitemaps_count"] = len(sm_list)
            counters["sitemaps_urls"] = sum(s.get("urls_count") or 0 for s in sm_list)
            counters["sitemap_errors"] = sum(s.get("errors_count") or 0 for s in sm_list)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                counters["host_not_loaded"] = True
        except Exception as e:
            counters["sitemaps_error"] = str(e)[:200]

    counters["available"] = not counters.get("host_not_loaded")
    return counters


@router.get("/search-queries")
async def search_queries(limit: int = 20):
    """Популярные поисковые запросы, по которым сайт показывается."""
    uid = await _ensure_user_id()
    url = f"{WM_BASE}/user/{uid}/hosts/{_host_id_enc()}/search-queries"
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        try:
            r = await client.get(url, headers=_headers(), params={"limit": min(limit, 100)})
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"queries": [], "status": "not_available_yet", "detail": "Данные появятся после индексации"}
            raise
