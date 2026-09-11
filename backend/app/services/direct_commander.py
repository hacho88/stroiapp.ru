import json
import urllib.request
import ssl
from datetime import datetime

from app.core.config import settings


class DirectCommander:
    def __init__(self) -> None:
        self.token = settings.yandex_direct_token
        self.sandbox = settings.yandex_direct_sandbox
        if self.sandbox:
            self.base_url = "https://api-sandbox.direct.yandex.com/json/v5"
            self.base_url_v501 = "https://api-sandbox.direct.yandex.com/json/v501"
            self.base_url_ip = "https://api-sandbox.direct.yandex.com/json/v5"
        else:
            self.base_url = "https://api.direct.yandex.com/json/v5"
            self.base_url_v501 = "https://api.direct.yandex.com/json/v501"
            self.base_url_ip = "https://87.250.250.243/json/v5"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept-Language": "ru",
            "Content-Type": "application/json",
        }

    def _request(self, service: str, method: str, params=None, use_v501: bool = False) -> dict:
        if not self.token:
            return {"status": "skipped", "reason": "no token"}
        body = {"method": method}
        if params:
            body["params"] = params

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        headers = self._headers()
        data = json.dumps(body).encode("utf-8")
        base = self.base_url_v501 if use_v501 else self.base_url

        # Try DNS first
        try:
            req = urllib.request.Request(
                f"{base}/{service}",
                data=data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

        # Fallback to IP with Host header
        req = urllib.request.Request(
            f"{self.base_url_ip}/{service}",
            data=data,
            headers={**headers, "Host": "api.direct.yandex.com"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_campaigns(self) -> list[dict]:
        if not self.token:
            return []
        result = self._request("campaigns", "get", {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status"],
        }, use_v501=True)
        if isinstance(result, dict):
            return result.get("result", {}).get("Campaigns", [])
        return []

    def create_campaign(self, name: str) -> dict:
        return self._request("campaigns", "add", {
            "Campaigns": [{
                "Name": name,
                "StartDate": datetime.now().strftime("%Y-%m-%d"),
                "TimeZone": "Europe/Moscow",
                "UnifiedCampaign": {
                    "BiddingStrategy": {
                        "Search": {
                            "BiddingStrategyType": "HIGHEST_POSITION",
                            "PlacementTypes": {
                                "SearchResults": "YES",
                                "ProductGallery": "YES",
                                "DynamicPlaces": "NO",
                                "Maps": "YES",
                                "SearchOrganizationList": "YES",
                            },
                        },
                        "Network": {
                            "BiddingStrategyType": "NETWORK_DEFAULT",
                            "PlacementTypes": {
                                "Network": "YES",
                                "Maps": "YES",
                            },
                        },
                    },
                },
            }]
        }, use_v501=True)

    def create_ad_group(self, campaign_id: int, name: str, region_ids: list[int] | None = None) -> dict:
        return self._request("adgroups", "add", {
            "AdGroups": [{
                "CampaignId": campaign_id,
                "Name": name,
                "RegionIds": region_ids or [213, 1],
            }]
        })

    def create_ad(self, ad_group_id: int, title: str, text: str, url: str) -> dict:
        return self._request("ads", "add", {
            "Ads": [{
                "AdGroupId": ad_group_id,
                "TextAd": {
                    "Title": title[:56],
                    "Text": text[:75],
                    "Href": url,
                },
            }]
        })

    def add_keywords(self, ad_group_id: int, keywords: list[str]) -> dict:
        return self._request("keywords", "add", {
            "Keywords": [
                {
                    "Keyword": kw,
                    "AdGroupId": ad_group_id,
                }
                for kw in keywords[:200]
            ]
        })

    def get_keyword_bids(self, keyword_ids: list[int]) -> list[dict]:
        result = self._request("keywordbids", "get", {
            "SelectionCriteria": {
                "KeywordIds": keyword_ids[:1000]
            },
            "FieldNames": ["KeywordId", "Bid", "ContextBid", "CompetitorsBid", "SearchPrices", "AuctionBids"],
        })
        return result.get("result", {}).get("KeywordBids", [])

    def set_keyword_bids(self, keyword_id: int, bid: int, context_bid: int | None = None) -> dict:
        params = {
            "KeywordBids": [{
                "KeywordId": keyword_id,
                "Bid": bid,
            }]
        }
        if context_bid:
            params["KeywordBids"][0]["ContextBid"] = context_bid
        return self._request("keywordbids", "set", params)

    def get_auction_bids(self, keyword_ids: list[int]) -> list[dict]:
        result = self._request("keywordbids", "get", {
            "SelectionCriteria": {
                "KeywordIds": keyword_ids[:1000]
            },
            "FieldNames": ["KeywordId", "Bid", "AuctionBids"],
        })
        return result.get("result", {}).get("KeywordBids", [])

    def get_campaign_stats(self, campaign_ids: list[int]) -> dict:
        result = self._request("campaigns", "get", {
            "SelectionCriteria": {
                "Ids": campaign_ids[:100]
            },
            "FieldNames": ["Id", "Name", "Status", "State", "Statistics"],
        }, use_v501=True)
        return result.get("result", {})

    def get_ad_stats(self, ad_ids: list[int]) -> list[dict]:
        result = self._request("ads", "get", {
            "SelectionCriteria": {
                "Ids": ad_ids[:1000]
            },
            "FieldNames": ["Id", "Status", "State", "AdGroupId"],
        })
        return result.get("result", {}).get("Ads", [])

    def get_keyword_stats(self, keyword_ids: list[int]) -> list[dict]:
        result = self._request("keywords", "get", {
            "SelectionCriteria": {
                "Ids": keyword_ids[:50]
            },
            "FieldNames": ["Id", "Keyword", "ServingStatus"],
        })
        return result.get("result", {}).get("Keywords", [])

    async def launch_campaign(self, products: list[dict]) -> dict:
        from app.services.campaign_optimizer import campaign_optimizer
        return await campaign_optimizer.launch_top_campaign(products)

    def close(self):
        pass


_direct_commander = DirectCommander()

def get_direct_commander() -> DirectCommander:
    return _direct_commander
