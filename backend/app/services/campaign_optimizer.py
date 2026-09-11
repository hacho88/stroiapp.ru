import json
from app.services.direct_commander import get_direct_commander
from app.services.ad_generator import ad_generator
from app.services.deepseek_client import deepseek_client
from app.services.product_db import product_db
from app.db.competitor_store import get_all_competitor_products_for_ai


class CampaignOptimizer:
    """Оптимизация кампаний для позиции #1 в Москве и МО."""

    def get_profitable_products(self, min_roi: int = 100, limit: int = 20) -> list[dict]:
        products = product_db.list_products()
        result = []
        for p in products:
            cost = p.cost_price_cash or p.cost_price_cashless or 0
            margin = (p.retail_price - cost) if p.retail_price else 0
            if margin > 0:
                roi = round((margin / max(cost, 1)) * 100, 1)
                if roi >= min_roi:
                    result.append({
                        "sku": p.sku,
                        "name": p.name,
                        "retail_price": p.retail_price,
                        "cost_price": cost,
                        "margin": round(margin, 2),
                        "roi": roi,
                        "url": f"https://stroiapp.ru/index.php?route=product/product&product_id={p.sku}",
                    })
        return sorted(result, key=lambda x: x["margin"], reverse=True)[:limit]

    def get_competitor_prices(self, product_name: str) -> list[dict]:
        all_comp = get_all_competitor_products_for_ai(limit=500)
        matches = []
        name_lower = product_name.lower()
        for cp in all_comp:
            cp_name = (cp.get("product_name") or "").lower()
            if name_lower in cp_name or cp_name in name_lower:
                matches.append({
                    "competitor": cp.get("competitor_name", ""),
                    "price": cp.get("price", 0),
                    "product_name": cp.get("product_name", ""),
                })
        return sorted(matches, key=lambda x: x["price"])[:10]

    async def generate_top_ad(self, product: dict) -> dict:
        """AI генерирует объявление, оптимизированное для позиции #1."""
        competitors = self.get_competitor_prices(product["name"])
        comp_text = ""
        if competitors:
            cheapest = competitors[0]
            comp_text = f"Конкурент {cheapest['competitor']} продаёт за {cheapest['price']}₽. "
            if product["retail_price"] < cheapest["price"]:
                comp_text += f"Мы дешевле на {round(cheapest['price'] - product['retail_price'], 2)}₽ — используй это в тексте!"
            else:
                comp_text += f"Мы дороже на {round(product['retail_price'] - cheapest['price'], 2)}₽ — emphasируй другие преимущества."

        system = (
            "Ты — эксперт по контекстной рекламе Яндекс Директ. "
            "Цель: позиция #1 в поиске по Москве и МО. "
            "Пиши максимально кликабельные (высокий CTR) тексты. "
            "Используй цифры, цены, конкретные преимущества. "
            "Не пиши воду. Только конкретика."
        )
        prompt = (
            f"Товар: {product['name']}\n"
            f"Наша цена: {product['retail_price']}₽\n"
            f"Маржа: {product['margin']}₽\n"
            f"ROI: {product['roi']}%\n"
            f"{comp_text}\n\n"
            f"Создай объявление для позиции #1 в Яндекс Директ:\n"
            f"1. Title (до 56 символов) — максимально привлекающий внимание, с ценой\n"
            f"2. Text (до 75 символов) — УТП: доставка, опт, НДС, выгода\n"
            f"3. Keywords (10-15 фраз) — точные и фразовые, не общие\n"
            f"4. NegativeKeywords (5-10) — минус-слова для отсечения нецелевого\n\n"
            f"Формат JSON:\n"
            f'{{"title":"...","text":"...","keywords":["..."],"negative_keywords":["..."]}}\n'
            f"Только JSON."
        )

        response = await deepseek_client.chat(prompt, max_tokens=800, temperature=0.3, system=system)

        try:
            import re
            match = re.search(r'\{.*?\}', response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                parsed = json.loads(response)
        except (json.JSONDecodeError, ValueError):
            parsed = {}

        title = parsed.get("title", f"{product['name'][:40]} — {product['retail_price']}₽")[:56]
        text = parsed.get("text", f"Опт с НДС, доставка Москва и МО")[:75]
        keywords = parsed.get("keywords", [product["name"], f"купить {product['name']}"])[:200]
        negative = parsed.get("negative_keywords", ["бесплатно", "скачать", "своими руками"])[:50]

        return {
            "product": product["name"],
            "sku": product.get("sku", ""),
            "title": title,
            "text": text,
            "keywords": keywords,
            "negative_keywords": negative,
            "url": product.get("url", "https://stroiapp.ru"),
            "price": product["retail_price"],
            "margin": product["margin"],
            "competitors": competitors[:3],
        }

    async def optimize_bids_for_position_one(self, campaign_id: int, ad_group_id: int) -> dict:
        """Анализирует ставки и устанавливает максимальные для позиции #1."""
        dc = get_direct_commander()

        keywords_result = dc._request("keywords", "get", {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Id", "Keyword", "Bid"],
        })
        keywords = keywords_result.get("result", {}).get("Keywords", [])
        if not keywords:
            return {"status": "error", "reason": "no keywords found"}

        keyword_ids = [kw["Id"] for kw in keywords]
        bids = dc.get_auction_bids(keyword_ids)

        optimized = []
        for bid_info in bids:
            kw_id = bid_info.get("KeywordId")
            auction = bid_info.get("AuctionBids", {})
            # P11 — ставка для позиции #1 в гарантированных показах
            # Bids — ставки для разных позиций
            top_bid = 0
            if isinstance(auction, dict):
                # Ищем максимальную ставку из аукциона
                bid_values = []
                for key in ["P11", "P10", "P9", "P8", "P7", "BlockPosition1", "FirstPosition"]:
                    val = auction.get(key, 0)
                    if val and isinstance(val, (int, float)):
                        bid_values.append(val)
                if bid_values:
                    top_bid = max(bid_values)
                else:
                    for key, val in auction.items():
                        if isinstance(val, (int, float)) and val > top_bid:
                            top_bid = val

            if top_bid > 0:
                # Ставим на 1% выше ставки конкурента для позиции #1
                our_bid = int(top_bid * 1.01)
                dc.set_keyword_bids(kw_id, our_bid)
                optimized.append({
                    "keyword_id": kw_id,
                    "auction_top": top_bid,
                    "our_bid": our_bid,
                    "position": "P1",
                })

        return {
            "status": "optimized",
            "campaign_id": campaign_id,
            "keywords_optimized": len(optimized),
            "details": optimized[:20],
        }

    async def launch_top_campaign(self, products: list[dict] | None = None) -> dict:
        """Полный запуск: AI → кампания → группа → объявления → ключевые слова → оптимизация ставок."""
        if not products:
            products = self.get_profitable_products(min_roi=100, limit=10)
        if not products:
            return {"status": "skipped", "reason": "no profitable products"}

        dc = get_direct_commander()

        # 1. AI генерация объявлений
        ads = []
        for product in products:
            ad = await self.generate_top_ad(product)
            ads.append(ad)

        # 2. Создаём кампанию
        campaign = dc.create_campaign("StroiApp #1 Москва и МО")
        campaign_ids = campaign.get("result", {}).get("AddResults", [])
        if not campaign_ids:
            return {"status": "error", "detail": campaign, "ads": ads}
        campaign_id = campaign_ids[0].get("Id")

        # 3. Создаём группу (Москва + МО)
        ad_group = dc.create_ad_group(campaign_id, "Москва и МО — Топ товары", region_ids=[213, 1])
        ad_group_ids = ad_group.get("result", {}).get("AddResults", [])
        if not ad_group_ids:
            return {"status": "error", "detail": ad_group, "ads": ads}
        ad_group_id = ad_group_ids[0].get("Id")

        # 4. Создаём объявления
        all_keywords = []
        all_negative = set()
        for ad in ads:
            dc.create_ad(ad_group_id, ad["title"], ad["text"], ad["url"])
            all_keywords.extend(ad["keywords"])
            all_negative.update(ad.get("negative_keywords", []))

        # 5. Добавляем ключевые слова (до 200)
        unique_keywords = list(dict.fromkeys(all_keywords))[:200]
        kw_result = dc.add_keywords(ad_group_id, unique_keywords)

        # 6. Получаем ID ключевых слов и оптимизируем ставки
        kw_ids = []
        kw_add_results = kw_result.get("result", {}).get("AddResults", [])
        for r in kw_add_results:
            if r.get("Id"):
                kw_ids.append(r["Id"])

        # 7. Оптимизация ставок для позиции #1
        bid_optimization = {"status": "skipped", "reason": "no keyword ids"}
        if kw_ids:
            bid_optimization = await self.optimize_bids_for_position_one(campaign_id, ad_group_id)

        return {
            "status": "launched",
            "strategy": "position_1_moscow_mo",
            "campaign_id": campaign_id,
            "ad_group_id": ad_group_id,
            "ads_created": len(ads),
            "keywords_added": len(unique_keywords),
            "negative_keywords": list(all_negative)[:50],
            "bid_optimization": bid_optimization,
            "ads": [{"title": a["title"], "text": a["text"], "price": a["price"]} for a in ads],
        }


campaign_optimizer = CampaignOptimizer()
