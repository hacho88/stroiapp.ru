"""
Сервис логистики: типы машин, грузоподъёмность, тарифы доставки.
Хранение: SQLite (backend/data/app.db).
"""

import json
import math
import os
import sqlite3
from datetime import datetime

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
            ("Легковой (до 500 кг)", 500, 2, 8, 300),
            ("Газель (до 1.5 т)", 1500, 6, 10, 500),
            ("Газон (до 5 т)", 5000, 16, 14, 800),
            ("Фура (до 20 т)", 20000, 82, 18, 1500),
        ]
        for name, w, v, ckm, base in defaults:
            conn.execute(
                "INSERT INTO vehicles (name, max_weight_kg, max_volume_m3, cost_per_km, base_cost) VALUES (?,?,?,?,?)",
                (name, w, v, ckm, base),
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

    def add_vehicle(self, name: str, max_weight_kg: float, max_volume_m3: float = 0,
                    cost_per_km: float = 0, base_cost: float = 0) -> dict:
        conn = _get_db()
        cur = conn.execute(
            "INSERT INTO vehicles (name, max_weight_kg, max_volume_m3, cost_per_km, base_cost) VALUES (?,?,?,?,?)",
            (name, max_weight_kg, max_volume_m3, cost_per_km, base_cost),
        )
        conn.commit()
        vid = cur.lastrowid
        conn.close()
        return self.get_vehicle(vid)

    def update_vehicle(self, vehicle_id: int, **fields) -> dict | None:
        allowed = {"name", "max_weight_kg", "max_volume_m3", "cost_per_km", "base_cost", "is_active"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k in allowed and v is not None:
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

    def select_vehicle_for_weight(self, total_weight_kg: float) -> dict | None:
        """Автоматически подобрать машину по весу груза."""
        conn = _get_db()
        row = conn.execute(
            "SELECT * FROM vehicles WHERE is_active = 1 AND max_weight_kg >= ? ORDER BY max_weight_kg ASC LIMIT 1",
            (total_weight_kg,),
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

    def calculate_delivery(self, total_weight_kg: float, distance_km: float,
                           zone_type: str = "city", order_amount: float = 0) -> dict:
        """Рассчитать стоимость доставки: подбор машины + тариф по зоне."""
        vehicle = self.select_vehicle_for_weight(total_weight_kg)
        if not vehicle:
            return {"status": "error", "message": "Нет подходящей машины для данного веса"}

        conn = _get_db()
        tariff = conn.execute(
            "SELECT * FROM delivery_tariffs WHERE is_active = 1 AND zone_type = ? ORDER BY id ASC LIMIT 1",
            (zone_type,),
        ).fetchone()
        conn.close()

        if not tariff:
            base_cost = vehicle["base_cost"]
            cost_per_km = vehicle["cost_per_km"]
            min_cost = 0
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
