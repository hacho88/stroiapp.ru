from fastapi import APIRouter, HTTPException

from app.db import user_store
from app.services.catalog_core import catalog_core, parse_qty
from app.services.opencart_api import opencart_api

router = APIRouter(prefix="/promotions", tags=["promotions"])

# Раздел «Акции» админки управляет строго витриной moscow.stroiapp.ru.
SITE_OWNER = "moscow"
PAYMENT_INVOICE = "Безналичный счёт ООО «МИКС СТРОЙ»"
PAYMENT_CASH = "Наличные"


@router.get("/status")
def get_status():
    return {"status": "ok", "message": "Акции moscow.stroiapp.ru — раздел работает",
            "site_owner": SITE_OWNER}


@router.post("/find-bundles")
async def find_bundles(payload: dict):
    """Поиск товаров-связок (локомотивы + вагоны) по категориям"""
    try:
        products = await opencart_api.get_action("product/list", {"limit": 200})
        items = products.get("products", []) if isinstance(products, dict) else (products if isinstance(products, list) else [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Группировка по категории (если есть category_id)
    by_cat = {}
    for p in items:
        cat = p.get("category_id", 0)
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(p)

    bundles = []
    for cat_id, prods in by_cat.items():
        if len(prods) < 2:
            continue
        # Локомотив — самый дорогой, вагон — следующий по цене
        sorted_prods = sorted(prods, key=lambda x: float(x.get("price", 0) or 0), reverse=True)
        locomotive = sorted_prods[0]
        wagon = sorted_prods[1]
        locomotive_price = float(locomotive.get("price", 0) or 0)
        wagon_price = float(wagon.get("price", 0) or 0)
        discount = round(wagon_price * 0.1, 2)  # 10% скидка на вагон
        bundles.append({
            "category_id": cat_id,
            "locomotive": {
                "product_id": locomotive.get("product_id"),
                "name": locomotive.get("name", ""),
                "price": locomotive_price,
            },
            "wagon": {
                "product_id": wagon.get("product_id"),
                "name": wagon.get("name", ""),
                "price": wagon_price,
            },
            "discount": discount,
            "bundle_price": round(locomotive_price + wagon_price - discount, 2),
            "savings": discount,
        })

    return {"bundles": bundles[:10], "total_found": len(bundles)}


# ---------- Акции/скидки (БД app.db, site_owner = moscow) ----------

@router.post("/create")
def create_promotion(payload: dict):
    """Создание акции/скидки — site_owner жёстко moscow."""
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название акции обязательно")
    pid = user_store.add_promotion({
        "site_owner": SITE_OWNER,           # игнорируем payload — всегда moscow
        "name": name,
        "type": payload.get("type") or "bundle",
        "discount_pct": payload.get("discount_pct") or 0,
        "items": payload.get("items") or payload.get("products") or [],
        "status": payload.get("status") or "active",
    })
    return {"status": "created", "promotion_id": pid, "site_owner": SITE_OWNER}


@router.get("/list")
def list_promotions(site_owner: str = ""):
    """Акции витрины. По умолчанию — только moscow."""
    owner = site_owner or SITE_OWNER
    return {"promotions": user_store.list_promotions(owner), "site_owner": owner}


@router.post("/update/{pid}")
def update_promotion(pid: int, payload: dict):
    """Правка акции (название/скидка/статус/товары). site_owner не меняется."""
    payload = dict(payload or {})
    payload.pop("site_owner", None)
    if not user_store.update_promotion(pid, payload):
        raise HTTPException(status_code=404, detail="Акция не найдена")
    return {"status": "updated", "promotion_id": pid, "site_owner": SITE_OWNER}


@router.post("/delete/{pid}")
def delete_promotion(pid: int):
    if not user_store.delete_promotion(pid):
        raise HTTPException(status_code=404, detail="Акция не найдена")
    return {"status": "deleted", "promotion_id": pid}


# ---------- Комплекты (карусель /storefront/kits на moscow) ----------

@router.get("/kits/list")
def kits_list(site_owner: str = ""):
    """Комплекты витрины из БД (админка). По умолчанию — moscow."""
    owner = site_owner or SITE_OWNER
    return {"kits": user_store.list_kits(owner), "site_owner": owner}


@router.post("/kits/create")
def kit_create(payload: dict):
    """Комплект для карусели moscow.stroiapp.ru.
    items: [{keys: ["штукатурк", ...], qty: 5}] — ключевые слова для подбора товара."""
    title = (payload.get("title") or "").strip()
    items = payload.get("items") or []
    if not title or not items:
        raise HTTPException(status_code=400, detail="Нужны title и items")
    kid = user_store.add_kit({
        "site_owner": SITE_OWNER,
        "title": title,
        "note": payload.get("note") or "",
        "items": items,
        "status": payload.get("status") or "active",
    })
    return {"status": "created", "kit_id": kid, "site_owner": SITE_OWNER}


@router.post("/kits/update/{kit_id}")
def kit_update(kit_id: int, payload: dict):
    payload = dict(payload or {})
    payload.pop("site_owner", None)
    if not user_store.update_kit(kit_id, payload):
        raise HTTPException(status_code=404, detail="Комплект не найден")
    return {"status": "updated", "kit_id": kit_id, "site_owner": SITE_OWNER}


@router.post("/kits/delete/{kit_id}")
def kit_delete(kit_id: int):
    if not user_store.delete_kit(kit_id):
        raise HTTPException(status_code=404, detail="Комплект не найден")
    return {"status": "deleted", "kit_id": kit_id}


# ---------- Сводка заказов для админки (защищено middleware) ----------

def _payment_kind(raw: str) -> str:
    """Нормализуем способ оплаты: 'invoice' | 'cash'."""
    s = (raw or "").lower()
    if any(w in s for w in ("безнал", "счёт", "счет", "invoice", "юрлиц", "б/н")):
        return "invoice"
    return "cash"


def _mass_kg(text: str) -> float:
    """Первая масса из строки через онтологию ядра: '2,5 т'→2500, '500 г'→0.5."""
    for q in parse_qty(text or ""):
        if q.get("dim") == "mass":
            return round(float(q.get("base_value") or 0), 3)
    return 0.0


def _item_weight_kg(item: dict) -> float:
    """Вес единицы позиции: явный weight → фасет 'вес' карточки → фасовка
    pack из каталога по SKU → масса из названия позиции."""
    w = float(item.get("weight") or 0)
    if w:
        return w
    sku = str(item.get("sku") or "")
    if sku:
        f = catalog_core.facets(sku)
        w = float(f.get("weight_kg") or 0)
        if not w:
            w = _mass_kg(str(f.get("weight") or ""))
        if not w:
            w = next((m for pk in (f.get("pack") or []) if (m := _mass_kg(pk))), 0.0)
        if w:
            return w
    return _mass_kg(item.get("name") or "")


@router.get("/orders")
async def admin_orders(limit: int = 200):
    """Сводная таблица заказов обеих витрин для раздела «Заказы».
    moscow — из app.db (storefront_orders), основной домен — из OpenCart."""
    out = []

    # 1) moscow.stroiapp.ru — локальная БД
    msk = user_store.list_orders(source="moscow.stroiapp.ru", limit=limit)
    for o in msk:
        kind = _payment_kind(o.get("payment", ""))
        # Позиции заказа хранятся без веса — ядро достаёт вес по SKU/названию
        items = [dict(i, weight=_item_weight_kg(i)) for i in (o.get("items") or [])]
        out.append({
            "id": f"msk-{o['id']}",
            "order_id": o["id"],
            "source": "moscow.stroiapp.ru",
            "date": o.get("created_at", ""),
            "customer": o.get("name") or o.get("inn") or "—",
            "phone": o.get("phone", ""),
            "address": o.get("address", ""),
            "inn": o.get("inn", ""),
            "total": round(float(o.get("total") or 0), 2),
            "status": o.get("status", "new"),
            "payment": PAYMENT_INVOICE if kind == "invoice" else PAYMENT_CASH,
            "payment_kind": kind,
            "items": items,
        })

    # 2) stroiapp.ru — заказы OpenCart
    try:
        res = await opencart_api.get_action("order/list", {"limit": limit, "page": 1})
        for o in (res.get("orders") or res.get("data") or []):
            raw_pay = str(o.get("payment_method") or o.get("payment") or "")
            kind = _payment_kind(raw_pay)
            customer = " ".join(filter(None, [o.get("firstname"), o.get("lastname")])) \
                or o.get("customer") or o.get("name") or "—"
            out.append({
                "id": f"oc-{o.get('order_id')}",
                "order_id": o.get("order_id"),
                "source": "stroiapp.ru",
                "date": o.get("date_added") or o.get("date_modified") or "",
                "customer": customer,
                "phone": o.get("telephone") or o.get("phone") or "",
                "address": o.get("payment_address_1") or o.get("shipping_address_1") or "",
                "inn": "",
                "total": round(float(o.get("total") or 0), 2),
                "status": o.get("order_status") or o.get("status") or "",
                "payment": PAYMENT_INVOICE if kind == "invoice" else (raw_pay or PAYMENT_CASH),
                "payment_kind": kind,
                "items": o.get("products") or o.get("items") or [],
            })
    except Exception as exc:
        return {"status": "partial", "orders": out, "error": f"OpenCart: {exc}"}

    # Дневная нумерация: порядковый № заказа внутри своих суток (с 00:00).
    by_day = {}
    for o in out:
        by_day.setdefault(str(o.get("date") or "")[:10], []).append(o)
    for day_orders in by_day.values():
        day_orders.sort(key=lambda x: str(x.get("date") or ""))
        for i, o in enumerate(day_orders, 1):
            o["daily_no"] = i

    out.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    return {"status": "ok", "orders": out, "total": len(out)}


@router.post("/orders/status/{order_id}")
async def admin_order_status(order_id: int, payload: dict):
    """Смена статуса заказа витрины moscow (строка БД storefront_orders)."""
    status = (payload.get("status") or "new").strip()
    if not user_store.set_order_status(order_id, status):
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return {"status": "updated", "order_id": order_id}


# ---------- Счёт 1C PDF из админки (без записи заказа/уведомлений) ----------

class _Obj:
    def __init__(self, d):
        for k, v in (d or {}).items():
            setattr(self, k, v)


@router.post("/orders/invoice-pdf")
def admin_invoice_pdf(payload: dict):
    """PDF-счёт 1C-макета по данным заказа из админки.

    Работает и для moscow-заказов, и для заказов OpenCart — состав передаёт
    фронт. Ничего не пишет в БД и не шлёт уведомлений (в отличие от
    /storefront/invoice)."""
    from fastapi.responses import Response
    from app.services.invoice_generator import render_invoice_pdf

    raw_items = payload.get("items") or []
    items = []
    for it in raw_items:
        qty = int(it.get("qty") or it.get("quantity") or 0)
        price = float(it.get("price") or 0)
        name = str(it.get("name") or it.get("product") or it.get("model") or "").strip()
        if name and qty > 0 and price > 0:
            items.append(_Obj({"name": name, "qty": qty, "price": price}))
    if not items:
        raise HTTPException(status_code=400, detail="Нет позиций для счёта")

    req = _Obj({
        "inn": str(payload.get("inn") or ""),
        "kpp": str(payload.get("kpp") or ""),
        "name": str(payload.get("customer") or payload.get("name") or ""),
        "address": str(payload.get("address") or ""),
        "phone": str(payload.get("phone") or ""),
    })
    pdf = render_invoice_pdf(req, items)
    fname = f"invoice-{payload.get('order_id') or 'order'}.pdf"
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
