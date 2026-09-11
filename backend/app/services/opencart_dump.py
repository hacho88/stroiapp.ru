import csv
import re
from pathlib import Path
from typing import Iterable

from app.models.product import Product

DUMP_PATH = Path(__file__).resolve().parents[4] / "ct45965_open.sql"
PRODUCT_TABLE = "oc_openproduct"
DESCRIPTION_TABLE = "oc_openproduct_description"



def _find_statement_end(sql: str, start: int) -> int:
    in_quote = False
    escaped = False
    for index in range(start, len(sql)):
        char = sql[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_quote:
            escaped = True
            continue
        if char == "'":
            in_quote = not in_quote
            continue
        if char == ";" and not in_quote:
            return index
    return len(sql)

def _iter_insert_blocks(sql: str, table: str) -> Iterable[tuple[list[str], str]]:
    marker = f"INSERT INTO `{table}`"
    start = 0
    while True:
        index = sql.find(marker, start)
        if index == -1:
            break
        columns_start = sql.find("(", index)
        columns_end = sql.find(") VALUES", columns_start)
        values_start = columns_end + len(") VALUES")
        values_end = _find_statement_end(sql, values_start)
        columns = [column.strip().strip("`") for column in sql[columns_start + 1:columns_end].split(",")]
        yield columns, sql[values_start:values_end].strip()
        start = values_end + 1


def _iter_tuples(values_sql: str) -> Iterable[str]:
    current: list[str] = []
    in_quote = False
    escaped = False
    depth = 0

    for char in values_sql:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote:
            current.append(char)
            escaped = True
            continue
        if char == "'":
            in_quote = not in_quote
            current.append(char)
            continue
        if char == "(" and not in_quote:
            depth += 1
            if depth == 1:
                current = []
                continue
        if char == ")" and not in_quote:
            depth -= 1
            if depth == 0:
                yield "".join(current)
                current = []
                continue
        if depth > 0:
            current.append(char)


def _parse_tuple(tuple_sql: str) -> list[str]:
    normalized = tuple_sql.replace("\\'", "''")
    reader = csv.reader([normalized], delimiter=",", quotechar="'", escapechar="\\")
    return [_clean_value(value) for value in next(reader)]




def _clean_value(value: str) -> str:
    value = value.strip()
    if value.upper() == "NULL":
        return ""
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        value = value[1:-1]
    return value.replace("''", "'")

def _rows(sql: str, table: str) -> Iterable[dict[str, str]]:
    for columns, values_sql in _iter_insert_blocks(sql, table):
        for tuple_sql in _iter_tuples(values_sql):
            values = _parse_tuple(tuple_sql)
            if len(values) == len(columns):
                yield dict(zip(columns, values))



def _extract_product_names(sql: str) -> dict[int, str]:
    names: dict[int, str] = {}
    pattern = re.compile(r"\((\d+),\s*1,\s*'((?:\\'|[^'])*)'", re.MULTILINE)
    start = 0
    marker = "INSERT INTO `oc_openproduct_description`"
    while True:
        index = sql.find(marker, start)
        if index == -1:
            break
        end = _find_statement_end(sql, index)
        block = sql[index:end]
        for match in pattern.finditer(block):
            product_id = int(match.group(1))
            name = match.group(2).replace("\\'", "'").replace("''", "'").strip()
            names[product_id] = name
        start = end + 1
    return names

def load_products_from_dump(limit: int | None = None) -> list[Product]:
    if not DUMP_PATH.exists():
        return []

    sql = DUMP_PATH.read_text(encoding="utf-8")
    names = _extract_product_names(sql)

    products: list[Product] = []
    for row in _rows(sql, PRODUCT_TABLE):
        try:
            product_id = int(row["product_id"])
            price = float(row.get("price") or 0)
            quantity = int(float(row.get("quantity") or 0))
            viewed = int(float(row.get("viewed") or 0))
        except (KeyError, ValueError):
            continue

        sku = row.get("sku") or str(product_id).zfill(4)
        name = names.get(product_id) or row.get("model") or f"Товар {sku}"
        expected_orders = max(1, round(min(viewed / 25, 40), 2))
        expected_profit = round(price * 0.18 * expected_orders, 2)
        ad_budget = round(max(300, min(price * 1.8, 3500)), 2)
        roi = round((expected_profit / ad_budget) * 100, 2) if ad_budget else 0

        products.append(Product(
            product_id=product_id,
            sku=sku,
            name=name,
            retail_price=price,
            wholesale_price=float(row.get("non_cash_price") or 0) or price,
            expected_orders=expected_orders,
            expected_profit=expected_profit,
            optimal_cpc=round(max(15, min(price * 0.08, 95)), 2),
            optimal_position=2,
            traffic_share=0.85,
            roi=roi,
            ad_budget=ad_budget,
            quantity=quantity,
            model=row.get("model") or "",
            image=row.get("image") or "",
        ))
        if limit and len(products) >= limit:
            break

    return products
