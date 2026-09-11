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
            value = org.get("value", "")
            inn_found = org.get("data", {}).get("inn", "")
            kpp = org.get("data", {}).get("kpp", "")
            address = org.get("data", {}).get("address", {}).get("value", "")
            management = org.get("data", {}).get("management", {}).get("name", "")
            return {
                "status": "found",
                "name": value,
                "inn": inn_found,
                "kpp": kpp,
                "address": address,
                "management": management,
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

    async def close(self):
        await self.client.aclose()


dadata_api = DaDataAPI()
