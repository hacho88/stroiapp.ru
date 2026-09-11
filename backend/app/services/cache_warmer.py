"""
Asynchronous TTFB Cache Warmer.
Parses sitemap.xml and aggressively pre-fetches URLs with a Chrome UA
to force OpCache / Varnish / server-side page generation.
"""

import asyncio
import re
import time
from typing import Any

import httpx

from app.core.config import settings


class CacheWarmer:
    """Background worker that warms the cache by hitting sitemap URLs."""

    CHROME_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self.base_url = (settings.opencart_api_url or "https://stroiapp.ru").rstrip("/")
        self.sitemap_url = f"{self.base_url}/sitemap.xml"
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)

    async def fetch_sitemap_urls(self) -> list[str]:
        """Parse sitemap.xml and return list of <loc> URLs."""
        urls = []
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            try:
                response = await client.get(self.sitemap_url, headers={"User-Agent": self.CHROME_UA})
                response.raise_for_status()
            except Exception as exc:
                print(f"[CacheWarner] sitemap fetch error: {exc}")
                return []

        try:
            # Use regex to avoid malformed XML issues
            raw = response.text
            for match in re.finditer(r"<loc>([^<]+)</loc>", raw, re.IGNORECASE):
                url = match.group(1).strip()
                if url:
                    urls.append(url)
        except Exception as exc:
            print(f"[CacheWarner] parse error: {exc}")

        return urls

    async def warm_url(self, client: httpx.AsyncClient, url: str) -> dict[str, Any]:
        """Hit a single URL and measure TTFB."""
        start = time.time()
        try:
            response = await client.get(
                url,
                headers={
                    "User-Agent": self.CHROME_UA,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
                follow_redirects=True,
            )
            elapsed = time.time() - start
            return {
                "url": url,
                "status": response.status_code,
                "ttfb_ms": round(elapsed * 1000, 1),
                "cached": response.headers.get("X-Cache-Status", "").lower() == "hit"
                or "cf-cache-status" in response.headers,
            }
        except Exception as exc:
            elapsed = time.time() - start
            return {
                "url": url,
                "status": 0,
                "ttfb_ms": round(elapsed * 1000, 1),
                "error": str(exc)[:200],
            }

    async def run(self, max_urls: int = 200) -> dict[str, Any]:
        """Main entry: fetch sitemap, warm URLs concurrently, report stats."""
        urls = await self.fetch_sitemap_urls()
        if not urls:
            return {"status": "error", "message": "No URLs found in sitemap"}

        if max_urls > 0:
            urls = urls[:max_urls]

        results = []
        ok_count = 0
        fail_count = 0
        total_ttfb = 0.0
        ttfb_count = 0

        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            tasks = [self.warm_url(client, url) for url in urls]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                results.append(res)
                if res.get("status", 0) == 200:
                    ok_count += 1
                    ttfb = res.get("ttfb_ms", 0)
                    if ttfb > 0:
                        total_ttfb += ttfb
                        ttfb_count += 1
                else:
                    fail_count += 1

        avg_ttfb = round(total_ttfb / ttfb_count, 1) if ttfb_count else 0
        sub200 = sum(1 for r in results if r.get("ttfb_ms", 999) < 200 and r.get("status") == 200)

        return {
            "status": "ok",
            "total_urls": len(urls),
            "ok": ok_count,
            "failed": fail_count,
            "avg_ttfb_ms": avg_ttfb,
            "sub_200ms_count": sub200,
            "slowest": sorted(results, key=lambda x: x.get("ttfb_ms", 0), reverse=True)[:5],
        }


_cache_warmer = CacheWarmer()


def get_cache_warmer() -> CacheWarmer:
    return _cache_warmer
