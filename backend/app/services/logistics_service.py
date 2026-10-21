"""
Сервис логистики: типы машин, грузоподъёмность, тарифы доставки.
Хранение: SQLite (backend/data/app.db).
"""

import json
import math
import os
import sqlite3
from datetime import datetime

import httpx

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "app.db")

# Склад: деревня Грибки, Дмитровское шоссе, д. вл58 с8
WAREHOUSE_LAT = 55.9549
WAREHOUSE_LON = 37.5367
WAREHOUSE_ADDRESS = "деревня Грибки, Дмитровское шоссе, д. вл58 с8"


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            max_weight_kg REAL NOT NULL,
            max_volume_m3 REAL NOT NULL DEFAULT 0,
            cost_per_km REAL NOT NULL DEFAULT 0,
            base_cost REAL NOT NULL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Миграции новых колонок автопарка
    for col, ddl in (
        ("max_length_mm", "REAL DEFAULT 0"),
        ("min_cost", "REAL DEFAULT 0"),
        ("vin", "TEXT DEFAULT ''"),
        ("plate_number", "TEXT DEFAULT ''"),
        ("driver_name", "TEXT DEFAULT ''"),
        ("driver_phone", "TEXT DEFAULT ''"),
        ("odometer_km", "REAL DEFAULT 0"),
        ("fuel_rate_l100km", "REAL DEFAULT 0"),
        ("vehicle_type", "TEXT DEFAULT ''"),
    ):
        try:
            conn.execute(f"ALTER TABLE vehicles ADD COLUMN {col} {ddl}")
        except sqlite3.OperationalError:
            pass
    # Бэкфилл категории по названию (только пустые; lower() в SQLite не ловит кириллицу)
    for kw, vtype in (("легков", "car"), ("фургон", "van"), ("газел", "van"),
                      ("газон", "truck"), ("фур", "semi")):
        conn.execute(
            "UPDATE vehicles SET vehicle_type = ? "
            "WHERE (vehicle_type IS NULL OR vehicle_type = '') "
            "AND (name LIKE ? OR name LIKE ?)",
            (vtype, f"%{kw}%", f"%{kw.capitalize()}%"),
        )
    # Бэкфилл макс. длины кузова по грузоподъёмности — идём ОТ БОЛЬШИХ машин,
    # иначе первый же порог 500 закроет условием >= всех (пустые значения только)
    for lo, mm in ((10000, 12500), (3000, 5000), (750, 3000), (0, 1600)):
        conn.execute(
            "UPDATE vehicles SET max_length_mm = ? "
            "WHERE (max_length_mm IS NULL OR max_length_mm = 0) AND max_weight_kg >= ?",
            (mm, lo),
        )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS warehouse (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL DEFAULT 'Склад',
            address TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delivery_tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_name TEXT NOT NULL,
            zone_type TEXT NOT NULL DEFAULT 'city',
            city_ids TEXT DEFAULT '[]',
            base_cost REAL NOT NULL DEFAULT 0,
            cost_per_km REAL NOT NULL DEFAULT 0,
            min_cost REAL NOT NULL DEFAULT 0,
            free_from REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            expense_type TEXT NOT NULL DEFAULT 'other',
            amount REAL NOT NULL DEFAULT 0,
            liters REAL DEFAULT 0,
            odometer_km REAL DEFAULT 0,
            comment TEXT DEFAULT '',
            expense_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_vehicle_expenses_vid "
        "ON vehicle_expenses (vehicle_id, expense_date)"
    )
    # Ensure warehouse record
    wh = conn.execute("SELECT COUNT(*) FROM warehouse WHERE id = 1").fetchone()[0]
    if wh == 0:
        conn.execute(
            "INSERT INTO warehouse (id, name, address, lat, lon) VALUES (1, 'Склад Грибки', ?, ?, ?)",
            (WAREHOUSE_ADDRESS, WAREHOUSE_LAT, WAREHOUSE_LON),
        )
    conn.commit()
    conn.close()


def _ensure_default_vehicles():
    conn = _get_db()
    count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    if count == 0:
        defaults = [
            ("Легковой (до 500 кг)", 500, 2, 1600, 8, 300),
            ("Газель (до 1.5 т)", 1500, 6, 3000, 10, 500),
            ("Газон (до 5 т)", 5000, 16, 5000, 14, 800),
            ("Фура (до 20 т)", 20000, 82, 12500, 18, 1500),
        ]
        for name, w, v, mlen, ckm, base in defaults:
            conn.execute(
                "INSERT INTO vehicles (name, max_weight_kg, max_volume_m3, max_length_mm, cost_per_km, base_cost) VALUES (?,?,?,?,?,?)",
                (name, w, v, mlen, ckm, base),
            )
        conn.commit()
    conn.close()


def _ensure_default_tariffs():
    conn = _get_db()
    count = conn.execute("SELECT COUNT(*) FROM delivery_tariffs").fetchone()[0]
    if count == 0:
        defaults = [
            ("Москва", "city", "300", 300, 0, 300, 0, 50000),
            ("Московская область", "region", "[]", 500, 8, 500, 0, 100000),
            ("Другие регионы", "region", "[]", 1000, 14, 1000, 0, 0),
        ]
        for zone, ztype, city_ids, base, ckm, min_c, free_f, _ in defaults:
            conn.execute(
                "INSERT INTO delivery_tariffs (zone_name, zone_type, city_ids, base_cost, cost_per_km, min_cost, free_from) VALUES (?,?,?,?,?,?,?)",
                (zone, ztype, city_ids, base, ckm, min_c, free_f),
            )
        conn.commit()
    conn.close()


VEHICLE_FIELDS = {
    "name", "vehicle_type", "max_weight_kg", "max_volume_m3", "max_length_mm", "min_cost",
    "cost_per_km", "base_cost", "vin", "plate_number", "driver_name",
    "driver_phone", "odometer_km", "fuel_rate_l100km", "is_active",
}

# Типы расходов на авто
EXPENSE_TYPES = {"fuel", "repair", "service", "parking", "fine", "other"}


class LogisticsService:
    def __init__(self):
        _init_db()
        _ensure_default_vehicles()
        _ensure_default_tariffs()

    # ─── VEHICLES ───

    def list_vehicles(self) -> list[dict]:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM vehicles ORDER BY max_weight_kg ASC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_vehicle(self, vehicle_id: int) -> dict | None:
        conn = _get_db()
        row = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def add_vehicle(self, name: str, max_weight_kg: float, **fields) -> dict:
        """Создать машину. fields — любые колонки из VEHICLE_FIELDS."""
        data = {"name": name, "max_weight_kg": max_weight_kg,
                **{k: v for k, v in fields.items()
                   if k in VEHICLE_FIELDS and v is not None}}
        cols = ", ".join(data)
        marks = ",".join("?" * len(data))
        conn = _get_db()
        cur = conn.execute(
            f"INSERT INTO vehicles ({cols}) VALUES ({marks})", list(data.values())
        )
        conn.commit()
        vid = cur.lastrowid
        conn.close()
        return self.get_vehicle(vid)

    def update_vehicle(self, vehicle_id: int, **fields) -> dict | None:
        sets = []
        vals = []
        for k, v in fields.items():
            if k in VEHICLE_FIELDS and v is not None:
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return self.get_vehicle(vehicle_id)
        sets.append("updated_at = ?")
        vals.append(datetime.now().isoformat())
        vals.append(vehicle_id)
        conn = _get_db()
        conn.execute(f"UPDATE vehicles SET {','.join(sets)} WHERE id = ?", vals)
        conn.commit()
        conn.close()
        return self.get_vehicle(vehicle_id)

    def delete_vehicle(self, vehicle_id: int) -> bool:
        conn = _get_db()
        cur = conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # ─── FLEET: VIN + расходы + пробег ───

    def decode_vin(self, vin: str) -> dict:
        """Декодировать VIN через бесплатный NHTSA vPIC API.
        Возвращает марку/модель/год и грузоподъёмность (GVWR → max_weight_kg)."""
        vin = (vin or "").strip().upper()
        if len(vin) != 17:
            return {"status": "error", "message": "VIN должен быть 17 символов"}
        try:
            r = httpx.get(
                f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json",
                timeout=10.0,
            )
            r.raise_for_status()
            res = {i["Variable"]: i["Value"] for i in r.json().get("Results", [])
                   if i.get("Value")}
        except Exception as e:
            return {"status": "error", "message": f"vPIC недоступен: {e}"}
        if not res.get("Make"):
            return {"status": "error", "vin": vin,
                    "message": "VIN не найден в базе NHTSA (база в основном для рынка США — введите данные вручную)"}
        make, model, year = res.get("Make", ""), res.get("Model", ""), res.get("Model Year", "")
        # GVWR класс → грузоподъёмность кг (нижняя граница класса)
        gvwr_map = {
            "Class 1": 2722, "Class 2": 4536, "Class 3": 6350,
            "Class 4": 7257, "Class 5": 8845, "Class 6": 11793,
            "Class 7": 14969, "Class 8": 14970,
        }
        gvw = res.get("Gross Vehicle Weight Rating From", "")
        max_w = next((v for k, v in gvwr_map.items() if gvw.startswith(k)), 0)
        return {
            "status": "ok", "vin": vin,
            "name": " ".join(x for x in (make, model) if x).strip(),
            "year": year, "make": make, "model": model,
            "body_class": res.get("Body Class", ""),
            "engine": res.get("Engine Model", res.get("Displacement (L)", "")),
            "gvwr_class": gvw, "max_weight_kg": max_w,
            "raw": res,
        }

    def add_expense(self, vehicle_id: int, expense_type: str, amount: float,
                    liters: float = 0, odometer_km: float = 0,
                    comment: str = "", expense_date: str = "") -> dict | None:
        """Записать расход на авто. odometer_km обновляет пробег машины (берём максимум)."""
        if not self.get_vehicle(vehicle_id):
            return None
        if expense_type not in EXPENSE_TYPES:
            expense_type = "other"
        expense_date = expense_date or datetime.now().date().isoformat()
        conn = _get_db()
        cur = conn.execute(
            "INSERT INTO vehicle_expenses (vehicle_id, expense_type, amount, liters, "
            "odometer_km, comment, expense_date) VALUES (?,?,?,?,?,?,?)",
            (vehicle_id, expense_type, amount, liters, odometer_km, comment, expense_date),
        )
        if odometer_km > 0:
            conn.execute(
                "UPDATE vehicles SET odometer_km = MAX(odometer_km, ?), updated_at = ? WHERE id = ?",
                (odometer_km, datetime.now().isoformat(), vehicle_id),
            )
        conn.commit()
        eid = cur.lastrowid
        conn.close()
        row = self.get_expense(eid)
        return row

    def get_expense(self, expense_id: int) -> dict | None:
        conn = _get_db()
        row = conn.execute(
            "SELECT * FROM vehicle_expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_expenses(self, vehicle_id: int | None = None, limit: int = 200) -> list[dict]:
        conn = _get_db()
        if vehicle_id:
            rows = conn.execute(
                "SELECT * FROM vehicle_expenses WHERE vehicle_id = ? "
                "ORDER BY expense_date DESC, id DESC LIMIT ?", (vehicle_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM vehicle_expenses ORDER BY expense_date DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_expense(self, expense_id: int) -> bool:
        conn = _get_db()
        cur = conn.execute("DELETE FROM vehicle_expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    def vehicle_stats(self, vehicle_id: int) -> dict | None:
        """Стата по машине: суммы расходов, топливо, фактический расход л/100км."""
        v = self.get_vehicle(vehicle_id)
        if not v:
            return None
        conn = _get_db()
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(SUM(CASE WHEN expense_type = 'fuel' THEN amount END), 0) AS fuel_amount,
                COALESCE(SUM(CASE WHEN expense_type = 'fuel' THEN liters END), 0) AS fuel_liters,
                COALESCE(SUM(CASE WHEN expense_type = 'repair' THEN amount END), 0) AS repair_amount,
                COALESCE(SUM(CASE WHEN expense_type = 'service' THEN amount END), 0) AS service_amount,
                MIN(NULLIF(odometer_km, 0)) AS odo_first,
                MAX(odometer_km) AS odo_last,
                COUNT(*) AS records
            FROM vehicle_expenses WHERE vehicle_id = ?
            """,
            (vehicle_id,),
        ).fetchone()
        conn.close()
        s = dict(row)
        distance = (s["odo_last"] or 0) - (s["odo_first"] or 0)
        # фактический расход по заправкам, иначе паспортный
        s["actual_l100km"] = round(s["fuel_liters"] / distance * 100, 1) \
            if distance > 0 and s["fuel_liters"] else (v.get("fuel_rate_l100km") or 0)
        s["distance_km"] = distance if distance > 0 else 0
        s["vehicle"] = v
        return s

    def fleet(self) -> list[dict]:
        """Автопарк: все машины + агрегированная стата расходов."""
        return [self.vehicle_stats(v["id"]) for v in self.list_vehicles()]

    def select_vehicle_for_weight(self, total_weight_kg: float) -> dict | None:
        """Автоматически подобрать машину по весу груза."""
        return self.select_vehicle(total_weight_kg)

    def select_vehicle(self, total_weight_kg: float, total_volume_m3: float = 0,
                       max_item_mm: float = 0) -> dict | None:
        """Подобрать наименьшую машину по весу, объёму и макс. габариту позиции.
        Макс. габарит берётся с запасом ×1.05 (зазор по длине кузова)."""
        conn = _get_db()
        row = conn.execute(
            """
            SELECT * FROM vehicles
            WHERE is_active = 1
              AND max_weight_kg >= ?
              AND (max_volume_m3 <= 0 OR max_volume_m3 >= ?)
              AND (max_length_mm IS NULL OR max_length_mm <= 0 OR max_length_mm >= ?)
            ORDER BY max_weight_kg ASC LIMIT 1
            """,
            (total_weight_kg, total_volume_m3 or 0, (max_item_mm or 0) * 1.05),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    # ─── TARIFFS ───

    def list_tariffs(self) -> list[dict]:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM delivery_tariffs ORDER BY id ASC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_tariff(self, tariff_id: int) -> dict | None:
        conn = _get_db()
        row = conn.execute("SELECT * FROM delivery_tariffs WHERE id = ?", (tariff_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def add_tariff(self, zone_name: str, zone_type: str = "city", city_ids: str = "[]",
                   base_cost: float = 0, cost_per_km: float = 0,
                   min_cost: float = 0, free_from: float = 0) -> dict:
        conn = _get_db()
        cur = conn.execute(
            "INSERT INTO delivery_tariffs (zone_name, zone_type, city_ids, base_cost, cost_per_km, min_cost, free_from) VALUES (?,?,?,?,?,?,?)",
            (zone_name, zone_type, city_ids, base_cost, cost_per_km, min_cost, free_from),
        )
        conn.commit()
        tid = cur.lastrowid
        conn.close()
        return self.get_tariff(tid)

    def update_tariff(self, tariff_id: int, **fields) -> dict | None:
        allowed = {"zone_name", "zone_type", "city_ids", "base_cost", "cost_per_km", "min_cost", "free_from", "is_active"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return self.get_tariff(tariff_id)
        sets.append("updated_at = ?")
        vals.append(datetime.now().isoformat())
        vals.append(tariff_id)
        conn = _get_db()
        conn.execute(f"UPDATE delivery_tariffs SET {','.join(sets)} WHERE id = ?", vals)
        conn.commit()
        conn.close()
        return self.get_tariff(tariff_id)

    def delete_tariff(self, tariff_id: int) -> bool:
        conn = _get_db()
        cur = conn.execute("DELETE FROM delivery_tariffs WHERE id = ?", (tariff_id,))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # ─── WAREHOUSE ───

    def get_warehouse(self) -> dict:
        conn = _get_db()
        row = conn.execute("SELECT * FROM warehouse WHERE id = 1").fetchone()
        conn.close()
        return dict(row) if row else {
            "id": 1, "name": "Склад Грибки",
            "address": WAREHOUSE_ADDRESS,
            "lat": WAREHOUSE_LAT, "lon": WAREHOUSE_LON,
        }

    def update_warehouse(self, name: str, address: str, lat: float, lon: float) -> dict:
        conn = _get_db()
        conn.execute(
            "UPDATE warehouse SET name=?, address=?, lat=?, lon=?, updated_at=? WHERE id=1",
            (name, address, lat, lon, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return self.get_warehouse()

    def calculate_distance(self, lat: float, lon: float) -> float:
        """Расстояние от склада до точки (км, формула гаверсинуса)."""
        wh = self.get_warehouse()
        R = 6371
        phi1 = math.radians(wh["lat"])
        phi2 = math.radians(lat)
        dphi = math.radians(lat - wh["lat"])
        dlambda = math.radians(lon - wh["lon"])
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    # ─── CALCULATE ───

    def _items_volume(self, items: list) -> tuple[float, float, float]:
        """(общий_объём_м³, макс_габарит_мм, суммарный_вес_кг) позиций по product_dims."""
        from app.db import learn_store
        items = items or []
        dims_map = learn_store.get_dims_many([i.get("sku") for i in items])
        vol_m3 = max_mm = w_kg = 0.0
        for i in items:
            qty = float(i.get("qty") or i.get("quantity") or 1)
            d = dims_map.get(str(i.get("sku") or ""))
            if not d:
                continue
            l, w, h = (d.get("length_mm") or 0), (d.get("width_mm") or 0), (d.get("height_mm") or 0)
            if l and w and h:
                vol_m3 += l * w * h * qty / 1e9
            vol_m3 += (d.get("volume_l") or 0) * qty / 1000
            w_kg += (d.get("weight_kg") or 0) * qty
            max_mm = max(max_mm, l)
        return vol_m3, max_mm, w_kg

    def calculate_delivery(self, total_weight_kg: float, distance_km: float,
                           zone_type: str = "city", order_amount: float = 0,
                           items: list | None = None) -> dict:
        """Рассчитать стоимость доставки: подбор машины + тариф по зоне.
        Если переданы items (sku/qty) — учитываем объём и габарит из product_dims."""
        total_volume_m3 = max_item_mm = 0.0
        if items:
            total_volume_m3, max_item_mm, dims_weight = self._items_volume(items)
            if dims_weight > total_weight_kg:
                total_weight_kg = dims_weight
        vehicle = self.select_vehicle(total_weight_kg, total_volume_m3, max_item_mm)
        if not vehicle:
            return {"status": "error",
                    "message": "Нет подходящей машины для данного веса/объёма/габаритов"}

        conn = _get_db()
        tariff = conn.execute(
            "SELECT * FROM delivery_tariffs WHERE is_active = 1 AND zone_type = ? ORDER BY id ASC LIMIT 1",
            (zone_type,),
        ).fetchone()
        conn.close()

        if not tariff:
            base_cost = vehicle["base_cost"]
            cost_per_km = vehicle["cost_per_km"]
            min_cost = vehicle.get("min_cost") or 0
            free_from = 0
        else:
            tariff = dict(tariff)
            base_cost = tariff["base_cost"]
            cost_per_km = tariff["cost_per_km"]
            min_cost = tariff["min_cost"]
            free_from = tariff["free_from"]

        transport_cost = base_cost + (cost_per_km * distance_km)
        total = max(transport_cost, min_cost)

        if free_from > 0 and order_amount >= free_from:
            total = 0

        return {
            "status": "ok",
            "vehicle": vehicle,
            "distance_km": distance_km,
            "weight_kg": total_weight_kg,
            "volume_m3": round(total_volume_m3, 3),
            "max_item_mm": max_item_mm,
            "base_cost": base_cost,
            "cost_per_km": cost_per_km,
            "transport_cost": round(transport_cost, 2),
            "min_cost": min_cost,
            "total_delivery": round(total, 2),
            "free_from": free_from,
            "order_amount": order_amount,
            "is_free": total == 0,
        }


_svc = None

def get_logistics_service() -> LogisticsService:
    global _svc
    if _svc is None:
        _svc = LogisticsService()
    return _svc
