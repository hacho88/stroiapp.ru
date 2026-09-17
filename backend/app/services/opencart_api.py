import httpx
import ssl
import json as _json
import urllib.request
import urllib.parse
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from app.core.config import settings


class OpenCartAPI:
    def __init__(self) -> None:
        self.base_url = settings.opencart_api_url.rstrip("/")
        self.token = settings.opencart_api_token
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.check_hostname = False
        self._ssl_context.verify_mode = ssl.CERT_NONE
        self._executor = ThreadPoolExecutor(max_workers=10)
        # Pre-resolve hostname to IP to avoid DNS issues in uvicorn threads
        self._hostname = ""
        self._ip_url = ""
        parsed = urlparse(self.base_url)
        if parsed.hostname:
            self._hostname = parsed.hostname
            try:
                ip = socket.gethostbyname(parsed.hostname)
                port = f":{parsed.port}" if parsed.port else ""
                self._ip_url = f"{parsed.scheme}://{ip}{port}"
            except Exception:
                self._ip_url = self.base_url
        else:
            self._ip_url = self.base_url

    def _reresolve_dns(self):
        """Re-resolve hostname to IP to avoid stale DNS cache."""
        if not self._hostname:
            return
        try:
            ip = socket.gethostbyname(self._hostname)
            parsed = urlparse(self.base_url)
            port = f":{parsed.port}" if parsed.port else ""
            self._ip_url = f"{parsed.scheme}://{ip}{port}"
        except Exception:
            self._ip_url = self.base_url

    def _url(self, route: str) -> str:
        return f"{self._ip_url}/index.php?route=api/ai_manager&action={route}"

    def _direct_url(self, route: str) -> str:
        return f"{self._ip_url}/index.php?route={route}"

    def _headers(self) -> dict[str, str]:
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-StroiApp-Manager/1.0"}
        if self.token:
            h["X-AI-Token"] = self.token
        if self._hostname and self._ip_url != self.base_url:
            h["Host"] = self._hostname
        return h

    def _sync_get(self, url: str, params: dict | None = None) -> dict:
        if params:
            qs = urllib.parse.urlencode(params)
            url = f"{url}&{qs}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60, context=self._ssl_context) as resp:
                data = resp.read().decode("utf-8-sig")
                return _json.loads(data)
        except Exception:
            # Re-resolve DNS and retry once
            self._reresolve_dns()
            req = urllib.request.Request(url, headers=self._headers(), method="GET")
            with urllib.request.urlopen(req, timeout=60, context=self._ssl_context) as resp:
                data = resp.read().decode("utf-8-sig")
                return _json.loads(data)

    def _sync_post(self, url: str, payload: dict | None = None, timeout: int = 120) -> dict:
        data = _json.dumps(payload or {}).encode("utf-8")
        headers = {**self._headers(), "Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=self._ssl_context) as resp:
                resp_data = resp.read().decode("utf-8-sig")
                return _json.loads(resp_data)
        except Exception:
            # Re-resolve DNS and retry once
            self._reresolve_dns()
            headers = {**self._headers(), "Content-Type": "application/json"}
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout, context=self._ssl_context) as resp:
                resp_data = resp.read().decode("utf-8-sig")
                return _json.loads(resp_data)

    async def get_action(self, action: str, params: dict | None = None):
        if not self.base_url:
            return {"status": "error", "detail": "OpenCart API URL не настроен"}
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(self._executor, self._sync_get, self._url(action), params)
        except Exception as exc:
            return {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}

    async def post_action(self, action: str, payload: dict | None = None):
        if not self.base_url:
            return {"status": "error", "detail": "OpenCart API URL не настроен"}
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(self._executor, self._sync_post, self._url(action), payload)
        except Exception as exc:
            return {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}

    async def post_direct(self, route: str, payload: dict | None = None):
        """POST to a direct OpenCart route (not via ai_manager action dispatcher)."""
        if not self.base_url:
            return {"status": "error", "detail": "OpenCart API URL не настроен"}
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(self._executor, self._sync_post, self._direct_url(route), payload)
        except Exception as exc:
            return {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}

    async def product_list(self, limit: int = 0):
        params = {}
        if limit > 0:
            params["limit"] = limit
        return await self.get_action("product/list", params if params else None)

    async def product_get(self, product_id: int):
        return await self.get_action("product/get", {"product_id": product_id})

    async def product_update(self, product_id: int, data: dict):
        return await self.post_action("product/update", {"product_id": product_id, **data})

    async def product_add(self, data: dict):
        return await self.post_action("product/add", data)

    async def product_edit(self, product_id: int, data: dict):
        return await self.post_action("product/edit", {"product_id": product_id, **data})

    async def product_delete(self, product_id: int):
        return await self.post_action("product/delete", {"product_id": product_id})

    async def bulk_update_prices(self, items: list[dict]):
        return await self.post_action("product/bulkUpdatePrices", {"items": items})

    async def seo_update_meta(self, product_id: int, meta_title: str = "", meta_description: str = "", meta_keyword: str = "", language_id: int = 1):
        payload = {
            "product_id": product_id,
            "language_id": language_id,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "meta_keyword": meta_keyword,
        }
        return await self.post_action("seo/updateMeta", payload)

    async def upload_image(self, file_bytes: bytes, filename: str, content_type: str = "image/jpeg"):
        import asyncio
        loop = asyncio.get_event_loop()

        def _upload():
            boundary = "----FormBoundaryAIStroiApp"
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
            headers = {**self._headers(), "Content-Type": f"multipart/form-data; boundary={boundary}"}
            req = urllib.request.Request(self._url("image/upload"), data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60, context=self._ssl_context) as resp:
                return _json.loads(resp.read().decode("utf-8-sig"))

        try:
            return await loop.run_in_executor(self._executor, _upload)
        except Exception as exc:
            return {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}


opencart_api = OpenCartAPI()
