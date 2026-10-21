"""
API роуты для логистики: типы машин, тарифы, расчёт доставки.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.logistics_service import get_logistics_service

router = APIRouter(prefix="/logistics", tags=["logistics"])


# ─── MODELS ───

class VehicleCreate(BaseModel):
    name: str
    vehicle_type: str = ""  # car|van|truck|semi
    max_weight_kg: float
    max_volume_m3: float = 0
    max_length_mm: float = 0
    min_cost: float = 0
    cost_per_km: float = 0
    base_cost: float = 0
    vin: str = ""
    plate_number: str = ""
    driver_name: str = ""
    driver_phone: str = ""
    odometer_km: float = 0
    fuel_rate_l100km: float = 0

class VehicleUpdate(BaseModel):
    name: str | None = None
    vehicle_type: str | None = None
    max_weight_kg: float | None = None
    max_volume_m3: float | None = None
    max_length_mm: float | None = None
    min_cost: float | None = None
    cost_per_km: float | None = None
    base_cost: float | None = None
    vin: str | None = None
    plate_number: str | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    odometer_km: float | None = None
    fuel_rate_l100km: float | None = None
    is_active: int | None = None

class VinRequest(BaseModel):
    vin: str

class ExpenseCreate(BaseModel):
    expense_type: str = "other"  # fuel|repair|service|parking|fine|other
    amount: float = 0
    liters: float = 0            # для fuel — литров заправлено
    odometer_km: float = 0       # показание одометра → обновит пробег машины
    comment: str = ""
    expense_date: str = ""       # YYYY-MM-DD, пусто = сегодня

class TariffCreate(BaseModel):
    zone_name: str
    zone_type: str = "city"
    city_ids: str = "[]"
    base_cost: float = 0
    cost_per_km: float = 0
    min_cost: float = 0
    free_from: float = 0

class TariffUpdate(BaseModel):
    zone_name: str | None = None
    zone_type: str | None = None
    city_ids: str | None = None
    base_cost: float | None = None
    cost_per_km: float | None = None
    min_cost: float | None = None
    free_from: float | None = None
    is_active: int | None = None

class CalculateItem(BaseModel):
    sku: str
    qty: float = 1

class CalculateRequest(BaseModel):
    total_weight_kg: float
    distance_km: float
    zone_type: str = "city"
    order_amount: float = 0
    items: list[CalculateItem] | None = None

class CalculateByCoordsRequest(BaseModel):
    total_weight_kg: float
    lat: float
    lon: float
    zone_type: str = "city"
    order_amount: float = 0
    items: list[CalculateItem] | None = None

class WarehouseUpdate(BaseModel):
    name: str
    address: str
    lat: float
    lon: float


# ─── VEHICLES ───

@router.get("/vehicles")
def list_vehicles():
    svc = get_logistics_service()
    return {"status": "ok", "vehicles": svc.list_vehicles()}

@router.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: int):
    svc = get_logistics_service()
    v = svc.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return {"status": "ok", "vehicle": v}

@router.get("/fleet")
def fleet():
    """Автопарк: все машины + агрегированная стата расходов/пробега/расхода топлива."""
    svc = get_logistics_service()
    return {"status": "ok", "fleet": svc.fleet()}

@router.post("/vehicles")
def create_vehicle(body: VehicleCreate):
    svc = get_logistics_service()
    v = svc.add_vehicle(body.name, body.max_weight_kg, **body.model_dump(
        exclude={"name", "max_weight_kg"}))
    return {"status": "ok", "vehicle": v}

@router.post("/vehicles/decode-vin")
def decode_vin(body: VinRequest):
    """Декодировать VIN (NHTSA vPIC) → марка/модель/год/грузоподъёмность. Не создаёт машину."""
    svc = get_logistics_service()
    return svc.decode_vin(body.vin)

@router.post("/vehicles/from-vin")
def vehicle_from_vin(body: VinRequest):
    """Создать машину по VIN: декодирует и заполняет карточку (вес можно поправить позже)."""
    svc = get_logistics_service()
    d = svc.decode_vin(body.vin)
    if d.get("status") != "ok":
        return d
    v = svc.add_vehicle(
        name=d["name"] or f"Авто {d['vin']}",
        max_weight_kg=d["max_weight_kg"] or 1000,
        vin=d["vin"],
    )
    return {"status": "ok", "vehicle": v, "decoded": {k: d[k] for k in (
        "year", "make", "model", "body_class", "engine", "gvwr_class", "max_weight_kg")}}

@router.post("/vehicles/{vehicle_id}/expenses")
def add_expense(vehicle_id: int, body: ExpenseCreate):
    """Добавить расход на авто (бензин/ремонт/ТО/штраф…). Пробег обновляется по odometer_km."""
    svc = get_logistics_service()
    e = svc.add_expense(vehicle_id, body.expense_type, body.amount, body.liters,
                        body.odometer_km, body.comment, body.expense_date)
    if not e:
        raise HTTPException(404, "Vehicle not found")
    return {"status": "ok", "expense": e}

@router.get("/vehicles/{vehicle_id}/expenses")
def list_expenses(vehicle_id: int, limit: int = 200):
    svc = get_logistics_service()
    return {"status": "ok", "expenses": svc.list_expenses(vehicle_id, limit)}

@router.get("/vehicles/{vehicle_id}/stats")
def vehicle_stats(vehicle_id: int):
    """Стата машины: суммы расходов, топливо, фактический расход л/100км, пробег."""
    svc = get_logistics_service()
    s = svc.vehicle_stats(vehicle_id)
    if not s:
        raise HTTPException(404, "Vehicle not found")
    return {"status": "ok", "stats": s}

@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    svc = get_logistics_service()
    if not svc.delete_expense(expense_id):
        raise HTTPException(404, "Expense not found")
    return {"status": "ok", "deleted": True}

@router.put("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, body: VehicleUpdate):
    svc = get_logistics_service()
    v = svc.update_vehicle(vehicle_id, **body.model_dump())
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return {"status": "ok", "vehicle": v}

@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    svc = get_logistics_service()
    ok = svc.delete_vehicle(vehicle_id)
    if not ok:
        raise HTTPException(404, "Vehicle not found")
    return {"status": "ok", "deleted": True}


# ─── TARIFFS ───

@router.get("/tariffs")
def list_tariffs():
    svc = get_logistics_service()
    return {"status": "ok", "tariffs": svc.list_tariffs()}

@router.post("/tariffs")
def create_tariff(body: TariffCreate):
    svc = get_logistics_service()
    t = svc.add_tariff(body.zone_name, body.zone_type, body.city_ids, body.base_cost, body.cost_per_km, body.min_cost, body.free_from)
    return {"status": "ok", "tariff": t}

@router.put("/tariffs/{tariff_id}")
def update_tariff(tariff_id: int, body: TariffUpdate):
    svc = get_logistics_service()
    t = svc.update_tariff(tariff_id, **body.model_dump())
    if not t:
        raise HTTPException(404, "Tariff not found")
    return {"status": "ok", "tariff": t}

@router.delete("/tariffs/{tariff_id}")
def delete_tariff(tariff_id: int):
    svc = get_logistics_service()
    ok = svc.delete_tariff(tariff_id)
    if not ok:
        raise HTTPException(404, "Tariff not found")
    return {"status": "ok", "deleted": True}


# ─── CALCULATE ───

@router.post("/calculate")
def calculate_delivery(body: CalculateRequest):
    """Рассчитать доставку: вес → машина → тариф → стоимость."""
    svc = get_logistics_service()
    result = svc.calculate_delivery(body.total_weight_kg, body.distance_km, body.zone_type,
                                    body.order_amount, items=body.items)
    return result

@router.post("/calculate-by-coords")
def calculate_by_coords(body: CalculateByCoordsRequest):
    """Рассчитать доставку по координатам клиента: расстояние от склада → машина → стоимость."""
    svc = get_logistics_service()
    distance = svc.calculate_distance(body.lat, body.lon)
    result = svc.calculate_delivery(body.total_weight_kg, distance, body.zone_type,
                                    body.order_amount, items=body.items)
    result["warehouse"] = svc.get_warehouse()
    result["client_coords"] = {"lat": body.lat, "lon": body.lon}
    return result


# ─── WAREHOUSE ───

@router.get("/warehouse")
def get_warehouse():
    svc = get_logistics_service()
    return {"status": "ok", "warehouse": svc.get_warehouse()}

@router.put("/warehouse")
def update_warehouse(body: WarehouseUpdate):
    svc = get_logistics_service()
    wh = svc.update_warehouse(body.name, body.address, body.lat, body.lon)
    return {"status": "ok", "warehouse": wh}

@router.get("/distance")
def get_distance(lat: float, lon: float):
    """Расстояние от склада до точки (км)."""
    svc = get_logistics_service()
    dist = svc.calculate_distance(lat, lon)
    wh = svc.get_warehouse()
    return {"status": "ok", "distance_km": dist, "warehouse": wh, "point": {"lat": lat, "lon": lon}}
