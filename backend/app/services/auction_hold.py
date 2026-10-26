"""Удержание позиции #1 в аукционе Яндекс Директ по нашим товарам.

Логика:
1. Берём маржинальные товары (campaign_optimizer.get_profitable_products).
2. Для каждого строим детерминированные ключи («купить X», «X цена москва»).
3. Заливаем ключи в отдельную ОСТАНОВЛЕННУЮ «зонд»-кампанию —
   Direct API отдаёт getLiveAuctionBids только по ключам внутри аккаунта.
4. Читаем AuctionBids/SearchPrices → цена входа в верхнюю позицию блока.
5. Рекомендуемая ставка = топ + epsilon (по умолч. +1₽, но не выше потолка
   от маржи и глобального max_bid).
6. hold_top() матчит ключи по тексту с боевой кампанией и выставляет ставки.

Всё синхронное (urllib внутри) — вызывать через asyncio.to_thread.
"""
import re
import time

from app.db import auction_store
from app.services.direct_commander import DirectCommander, get_direct_commander

PROBE_CAMPAIGN_NAME = "AI-AUCTION-PROBE (не запускать)"
KW_PER_ADGROUP = 200  # лимит Директа на keywords.add за один запрос/группу
MIN_BID_RUB = 0.30    # минимальная ставка Директа


def _clean_product_name(name: str) -> str:
    """Чистит название товара для ключевой фразы."""
    name = re.sub(r"[()\"'«»]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:70]


def build_keywords(product: dict) -> list[str]:
    """Детерминированные ключи по товару — без AI, мгновенно и бесплатно."""
    base = _clean_product_name(product.get("name", ""))
    if not base:
        return []
    # короткая форма: первые 4 слова — для «купить …» вариантов
    short = " ".join(base.split()[:4])
    keys = {
        base.lower(),
        f"{short.lower()} цена",
        f"купить {short.lower()}",
        f"{short.lower()} купить москва",
    }
    return [k for k in keys if 3 <= len(k) <= 400]


def _extract_top_auction(auction_raw) -> tuple[float, float, int]:
    """Из AuctionBids достаёт (ставка_топ_позиции_₽, цена_списания_₽, число_участников).

    Структура v5: {"AuctionBids":[{"Bid":micro,"Price":micro,"Position":"P11"..},..]}
    либо словарь {P11: micro,...} — обрабатываем оба варианта.
    """
    if not auction_raw:
        return 0.0, 0.0, 0
    items = []
    if isinstance(auction_raw, list):
        items = auction_raw
    elif isinstance(auction_raw, dict):
        items = auction_raw.get("AuctionBids") or auction_raw.get("AuctionBidItems") or []
        if not items:
            # плоский словарь {P11: micro}
            nums = [v for v in auction_raw.values() if isinstance(v, (int, float))]
            top = max(nums) if nums else 0
            return (DirectCommander.micro_to_rub(top), 0.0, len(nums))
    if not isinstance(items, list):
        return 0.0, 0.0, 0

    top_bid = top_price = 0.0
    # ищем именно верхнюю премиум-позицию (P11/PREMIUM1/первая в списке)
    for entry in items:
        if not isinstance(entry, dict):
            continue
        bid = DirectCommander.micro_to_rub(entry.get("Bid"))
        price = DirectCommander.micro_to_rub(entry.get("Price") or entry.get("PriceInSearch"))
        pos = str(entry.get("Position", ""))
        is_top = pos.upper() in ("P11", "PREMIUM1", "P1", "FIRST", "TOP1")
        if is_top:
            return bid, price, len(items)
        if bid > top_bid:
            top_bid, top_price = bid, price
    return top_bid, top_price, len(items)


class AuctionHold:
    """Сканирует аукцион и удерживает верхнюю позицию по нашим ключам."""

    def __init__(self) -> None:
        self.dc: DirectCommander = get_direct_commander()

    # ---------- зонд-кампания ----------

    def _find_probe_campaign(self) -> int | None:
        for c in self.dc.get_campaigns():
            if c.get("Name") == PROBE_CAMPAIGN_NAME:
                return c.get("Id")
        return None

    def _ensure_probe(self) -> tuple[int | None, str]:
        """Возвращает (campaign_id, error). Создаёт+останавливает зонд при нужде."""
        cid = self._find_probe_campaign()
        if cid:
            return cid, ""
        created = self.dc.create_probe_campaign(PROBE_CAMPAIGN_NAME)
        ids = created.get("result", {}).get("AddResults", [])
        if not ids or not ids[0].get("Id"):
            return None, f"probe create failed: {created}"
        cid = ids[0]["Id"]
        self.dc.suspend_campaign(cid)  # зонд никогда не крутится
        return cid, ""

    def _ensure_adgroup(self, campaign_id: int, name: str) -> int | None:
        for g in self.dc.get_ad_groups(campaign_id):
            if g.get("Name") == name:
                return g.get("Id")
        res = self.dc.create_ad_group(campaign_id, name, region_ids=[213, 1])
        ids = res.get("result", {}).get("AddResults", [])
        return ids[0].get("Id") if ids else None

    def _sync_probe_keywords(self, campaign_id: int, keywords: list[str]) -> dict[int, str]:
        """Полная синхронизация: удаляет старые ключи зонда, заливает новые.
        Возвращает {keyword_id: keyword_text}."""
        existing = self.dc.get_keywords_by_campaign(campaign_id)
        old_ids = [k["Id"] for k in existing if k.get("Id")]
        for i in range(0, len(old_ids), 1000):
            self.dc.delete_keywords(old_ids[i:i + 1000])

        kw_map: dict[int, str] = {}
        chunks = [keywords[i:i + KW_PER_ADGROUP] for i in range(0, len(keywords), KW_PER_ADGROUP)]
        for idx, chunk in enumerate(chunks, start=1):
            gid = self._ensure_adgroup(campaign_id, f"scan-{idx}")
            if not gid:
                continue
            self._ensure_probe_ad(gid)
            res = self.dc.add_keywords(gid, chunk)
            add_results = res.get("result", {}).get("AddResults", [])
            for kw_text, r in zip(chunk, add_results):
                if r.get("Id"):
                    kw_map[r["Id"]] = kw_text
        return kw_map

    def _ensure_probe_ad(self, ad_group_id: int) -> None:
        """AuctionBids считается только для групп с объявлением (цена входа
        зависит от качества объявления). Зонд-объявление служебное и никогда
        не показывается — кампания-черновик/остановлена."""
        if self.dc.get_ads_by_group(ad_group_id):
            return
        self.dc.create_ad(
            ad_group_id,
            "Стройматериалы StroiApp",
            "Стройматериалы с доставкой по Москве и области. Склад, низкие цены.",
            "https://stroiapp.ru",
        )

    # ---------- сканирование ----------

    def scan(self, min_roi: int = 50, product_limit: int = 30,
             epsilon_rub: float = 1.0, max_bid_rub: float = 0,
             margin_cap_pct: float = 10.0) -> dict:
        """Полный цикл: товары → ключи → зонд → auction bids → сохранение."""
        from app.services.campaign_optimizer import campaign_optimizer

        if not self.dc.token:
            return {"status": "no_token",
                    "message": "YANDEX_DIRECT_TOKEN не настроен в .env"}

        products = campaign_optimizer.get_profitable_products(
            min_roi=min_roi, limit=product_limit)
        if not products:
            return {"status": "error", "message": "Нет маржинальных товаров"}

        # ключи: продукт → список фраз, глобальная дедупликация
        kw_products: dict[str, dict] = {}
        for p in products:
            for kw in build_keywords(p):
                kw_products.setdefault(kw, p)
        keywords = list(kw_products.keys())

        cid, err = self._ensure_probe()
        if not cid:
            return {"status": "error", "message": err}

        kw_map = self._sync_probe_keywords(cid, keywords)
        if not kw_map:
            return {"status": "error",
                    "message": "Не удалось добавить ключи в зонд-кампанию"}

        # Директ пересчитывает аукцион с задержкой (~1–2 мин): свежим ключам
        # и новому объявлению нужно время. Поллим до появления данных.
        rows: list[dict] = []
        kw_ids = list(kw_map.keys())
        for attempt in range(5):
            time.sleep(30)
            rows = self.dc.get_auction_full(kw_ids)
            have = sum(1 for r in rows
                       if (r.get("Search") or {}).get("AuctionBids"))
            if have >= max(1, len(rows) // 2):
                break

        scan_id = auction_store.create_scan(
            probe_campaign_id=cid,
            keywords_total=len(kw_map),
            products_total=len(products),
        )

        items, with_data = [], 0
        for row in rows:
            kw_id = row.get("KeywordId")
            kw_text = kw_map.get(kw_id, "")
            product = kw_products.get(kw_text, {})
            # Ответ keywordbids/get: row["Search"]["AuctionBids"]["AuctionBidItems"]
            search = row.get("Search") or {}
            auction = search.get("AuctionBids") or row.get("AuctionBids")
            if isinstance(auction, dict):
                auction = auction.get("AuctionBidItems") or auction.get("AuctionBids") or auction
            top_bid, top_price, n_comp = _extract_top_auction(auction)

            # потолок ставки: max_bid_rub и/или % от маржи товара
            cap = float(max_bid_rub or 0)
            margin = float(product.get("margin") or 0)
            margin_cap = margin * margin_cap_pct / 100 if margin > 0 else 0
            caps = [c for c in (cap, margin_cap) if c > 0]

            recommended = 0.0
            if top_bid > 0:
                recommended = round(top_bid + max(epsilon_rub, top_bid * 0.01), 2)
                recommended = max(MIN_BID_RUB, recommended)
                if caps:
                    recommended = min(recommended, min(caps))
            if top_bid > 0:
                with_data += 1

            items.append({
                "keyword": kw_text,
                "keyword_id": kw_id,
                "product_name": product.get("name", ""),
                "product_sku": product.get("sku", ""),
                "product_margin": margin,
                "top_bid_rub": top_bid,
                "top_price_rub": top_price,
                "recommended_rub": recommended,
                "competitors_count": n_comp,
            })

        auction_store.save_items(scan_id, items)
        auction_store.update_scan_counts(scan_id, with_data)

        return {
            "status": "ok",
            "scan_id": scan_id,
            "probe_campaign_id": cid,
            "products": len(products),
            "keywords": len(kw_map),
            "with_auction_data": with_data,
            "items": sorted(items, key=lambda x: -x["recommended_rub"]),
        }

    # ---------- удержание топа ----------

    def hold_top(self, target_campaign_id: int | None = None) -> dict:
        """Выставляет рекомендованные ставки в боевой кампании по тексту ключа."""
        if not self.dc.token:
            return {"status": "no_token",
                    "message": "YANDEX_DIRECT_TOKEN не настроен в .env"}

        items = auction_store.latest_scan_items()
        items = [i for i in items if i["recommended_rub"] > 0]
        if not items:
            return {"status": "error",
                    "message": "Нет данных сканирования — запустите /auction-scan"}

        if not target_campaign_id:
            saved = auction_store.get_setting("target_campaign_id")
            target_campaign_id = int(saved) if saved.isdigit() else None
        if not target_campaign_id:
            # первая НЕ-зондовая кампания
            for c in self.dc.get_campaigns():
                if c.get("Name") != PROBE_CAMPAIGN_NAME:
                    target_campaign_id = c.get("Id")
                    break
        if not target_campaign_id:
            return {"status": "error",
                    "message": "Нет боевой кампании — укажите target_campaign_id"}

        battle_kw = self.dc.get_keywords_by_campaign(target_campaign_id)
        text_to_id = {k.get("Keyword", "").strip().lower(): k["Id"]
                      for k in battle_kw if k.get("Id")}

        to_set, missing = [], []
        for it in items:
            kid = text_to_id.get(it["keyword"].strip().lower())
            if kid:
                to_set.append({
                    "keyword_id": kid,
                    "bid_micro": DirectCommander.rub_to_micro(it["recommended_rub"]),
                    "_keyword": it["keyword"],
                })
            else:
                missing.append(it["keyword"])

        applied = 0
        errors = []
        for i in range(0, len(to_set), 1000):
            res = self.dc.set_keyword_bids_bulk(to_set[i:i + 1000])
            if res.get("error"):
                errors.append(res["error"])
            else:
                for it in to_set[i:i + 1000]:
                    auction_store.mark_applied(it["_keyword"])
                    applied += 1

        return {
            "status": "ok" if applied else "error",
            "campaign_id": target_campaign_id,
            "applied": applied,
            "missing_in_campaign": missing[:50],
            "errors": errors,
        }

    def status(self) -> dict:
        scan = auction_store.latest_scan()
        items = auction_store.latest_scan_items(limit=100) if scan else []
        return {
            "auto_hold": auction_store.get_setting("auto_hold") == "1",
            "target_campaign_id": auction_store.get_setting("target_campaign_id"),
            "last_scan": scan,
            "items": items,
        }


auction_hold = AuctionHold()


async def auto_hold_loop():
    """Фоновой цикл: каждые 4ч переснимает аукцион и держит топ, если включено."""
    import asyncio
    while True:
        try:
            if auction_store.get_setting("auto_hold") == "1":
                import asyncio as _a
                res = await _a.to_thread(auction_hold.scan)
                if res.get("status") == "ok":
                    await _a.to_thread(auction_hold.hold_top)
        except Exception as exc:
            print("[auction_hold] loop error:", exc)
        await asyncio.sleep(4 * 3600)
