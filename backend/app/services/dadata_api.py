import httpx

from app.core.config import settings


class DaDataAPI:
    def __init__(self) -> None:
        self.token = settings.dadata_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def validate_inn(self, inn: str) -> dict:
        if not self.token:
            return {"status": "skipped", "reason": "no token"}
        try:
            response = await self.client.post(
                f"{self.base_url}/findById/party",
                headers=self._headers(),
                json={"query": inn},
            )
            response.raise_for_status()
            data = response.json()
            suggestions = data.get("suggestions", [])
            if not suggestions:
                return {"status": "not_found", "inn": inn}
            org = suggestions[0]
            d = org.get("data", {}) or {}
            name_obj = d.get("name", {}) or {}
            return {
                "status": "found",
                "name": name_obj.get("short_with_opf") or org.get("value", ""),
                "name_full": name_obj.get("full_with_opf") or org.get("value", ""),
                "inn": d.get("inn", ""),
                "kpp": d.get("kpp", ""),
                "ogrn": d.get("ogrn", ""),
                "type": d.get("type", ""),           # LEGAL | INDIVIDUAL
                "okved": d.get("okved", ""),
                "address": (d.get("address") or {}).get("value", ""),
                "management": (d.get("management") or {}).get("name", ""),
                "state": (d.get("state") or {}).get("status", ""),
            }
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    async def suggest_address(self, query: str) -> list[str]:
        if not self.token:
            return []
        try:
            response = await self.client.post(
                f"{self.base_url}/suggest/address",
                headers=self._headers(),
                json={"query": query, "count": 5},
            )
            response.raise_for_status()
            data = response.json()
            return [s.get("value", "") for s in data.get("suggestions", [])]
        except Exception:
            return []

    async def geolocate_address(self, lat: float, lon: float) -> str:
        """Координаты → ближайший текстовый адрес (geolocate/address)."""
        if not self.token:
            return ""
        try:
            response = await self.client.post(
                f"{self.base_url}/geolocate/address",
                headers=self._headers(),
                json={"lat": lat, "lon": lon, "count": 1, "radius_m": 1000},
            )
            response.raise_for_status()
            suggestions = response.json().get("suggestions", [])
            return suggestions[0].get("value", "") if suggestions else ""
        except Exception:
            return ""

    async def close(self):
        await self.client.aclose()


dadata_api = DaDataAPI()
