import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_costs (
                sku TEXT PRIMARY KEY,
                cost_price_cash REAL NOT NULL DEFAULT 0,
                cost_price_cashless REAL NOT NULL DEFAULT 0,
                retail_price REAL NOT NULL DEFAULT 0,
                wholesale_price REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(product_costs)").fetchall()}
        if "retail_price" not in columns:
            connection.execute("ALTER TABLE product_costs ADD COLUMN retail_price REAL NOT NULL DEFAULT 0")
        if "wholesale_price" not in columns:
            connection.execute("ALTER TABLE product_costs ADD COLUMN wholesale_price REAL NOT NULL DEFAULT 0")


def get_all_costs() -> dict[str, tuple[float, float, float, float]]:
    init_db()
    with _connect() as connection:
        rows = connection.execute("SELECT sku, cost_price_cash, cost_price_cashless, retail_price, wholesale_price FROM product_costs").fetchall()
    return {row["sku"]: (float(row["cost_price_cash"]), float(row["cost_price_cashless"]), float(row["retail_price"]), float(row["wholesale_price"])) for row in rows}


def save_costs(sku: str, cost_price_cash: float, cost_price_cashless: float, retail_price: float, wholesale_price: float) -> None:
    init_db()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO product_costs (sku, cost_price_cash, cost_price_cashless, retail_price, wholesale_price, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sku) DO UPDATE SET
                cost_price_cash = excluded.cost_price_cash,
                cost_price_cashless = excluded.cost_price_cashless,
                retail_price = excluded.retail_price,
                wholesale_price = excluded.wholesale_price,
                updated_at = CURRENT_TIMESTAMP
            """,
            (sku, cost_price_cash, cost_price_cashless, retail_price, wholesale_price),
        )
