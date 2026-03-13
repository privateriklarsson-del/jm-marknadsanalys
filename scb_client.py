"""
SCB API Client for DeSO-level demographic data.

SCB (Statistiska centralbyrån) uses a table-based REST API.
- Base URL: https://api.scb.se/OV0104/v1/doris/sv/ssd/
- Navigate a tree of table IDs, then POST a query with filters.
- Response format: JSON-stat2 or CSV.

DeSO = Demografiska statistikområden (~6,000 micro-areas in Sweden).
"""
from __future__ import annotations

import requests
import json
import time
import hashlib
from pathlib import Path
from typing import Optional
import pandas as pd

SCB_BASE_URL = "https://api.scb.se/OV0104/v1/doris/sv/ssd"

# Cache directory for API responses
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Rate limit: SCB allows ~10 requests/10 seconds
_last_request_time = 0
RATE_LIMIT_SECONDS = 1.2


def _rate_limit():
    """Respect SCB's rate limiting."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.time()


def _cache_key(table_path: str, query: dict) -> str:
    """Generate a cache filename from the query."""
    raw = f"{table_path}_{json.dumps(query, sort_keys=True)}"
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"scb_{h}.json"


def _get_cached(key: str, max_age_hours: int = 24) -> Optional[dict]:
    """Return cached response if fresh enough."""
    path = CACHE_DIR / key
    if path.exists():
        age_hours = (time.time() - path.stat().st_mtime) / 3600
        if age_hours < max_age_hours:
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _save_cache(key: str, data: dict):
    path = CACHE_DIR / key
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def get_table_metadata(table_path: str) -> Optional[dict]:
    """
    Fetch metadata (available variables, codes, values) for a SCB table.
    This tells you what filters you can apply.
    """
    url = f"{SCB_BASE_URL}/{table_path}"
    _rate_limit()
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[SCB] Metadata fetch failed for {table_path}: {e}")
        return None


def query_table(table_path: str, query_body: dict, cache_hours: int = 24) -> Optional[dict]:
    """
    POST a query to a SCB table and return the JSON-stat2 response.

    query_body example:
    {
        "query": [
            {"code": "Region", "selection": {"filter": "vs:RegionKommun07", "values": ["0180"]}},
            {"code": "Alder", "selection": {"filter": "vs:Ålder1årA", "values": ["20", "25", "30"]}},
        ],
        "response": {"format": "json"}
    }
    """
    key = _cache_key(table_path, query_body)
    cached = _get_cached(key, cache_hours)
    if cached:
        return cached

    url = f"{SCB_BASE_URL}/{table_path}"
    _rate_limit()
    try:
        resp = requests.post(url, json=query_body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _save_cache(key, data)
        return data
    except Exception as e:
        print(f"[SCB] Query failed for {table_path}: {e}")
        return None


def parse_scb_json(raw: dict) -> pd.DataFrame:
    """
    Parse SCB's JSON response format into a clean DataFrame.

    SCB returns data in a nested structure with columns[], comments[], data[].
    Each row in data[] has key[] (dimension values) and values[] (measurements).
    """
    if not raw or "columns" not in raw:
        return pd.DataFrame()

    columns = [col["text"] for col in raw["columns"]]
    rows = []
    for entry in raw.get("data", []):
        row = entry["key"] + entry["values"]
        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)

    # Try to convert numeric columns
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    return df


# ──────────────────────────────────────────────
# High-level query functions for specific tables
# ──────────────────────────────────────────────

# SCB table paths for DeSO-level data
TABLES = {
    "population_age_sex": "BE/BE0101/BE0101A/FolsijkDeSO",
    "income":             "HE/HE0110/HE0110A/SamijsInk1DeSO",
    "migration":          "BE/BE0101/BE0101J/FlyijttDeSOReg",
    "housing_stock":      "BO/BO0104/BO0104T02",
}


def fetch_population_by_age(deso_codes: list[str], years: list[str] = None) -> pd.DataFrame:
    """Fetch population by age group and sex for given DeSO areas."""
    if years is None:
        years = [str(y) for y in range(2019, 2025)]

    query = {
        "query": [
            {
                "code": "Region",
                "selection": {"filter": "item", "values": deso_codes}
            },
            {
                "code": "Tid",
                "selection": {"filter": "item", "values": years}
            }
        ],
        "response": {"format": "json"}
    }

    raw = query_table(TABLES["population_age_sex"], query)
    if raw:
        return parse_scb_json(raw)
    return pd.DataFrame()


def fetch_income(deso_codes: list[str], years: list[str] = None) -> pd.DataFrame:
    """Fetch income data for given DeSO areas."""
    if years is None:
        years = [str(y) for y in range(2019, 2023)]

    query = {
        "query": [
            {
                "code": "Region",
                "selection": {"filter": "item", "values": deso_codes}
            },
            {
                "code": "Tid",
                "selection": {"filter": "item", "values": years}
            }
        ],
        "response": {"format": "json"}
    }

    raw = query_table(TABLES["income"], query)
    if raw:
        return parse_scb_json(raw)
    return pd.DataFrame()


def fetch_migration(deso_codes: list[str], years: list[str] = None) -> pd.DataFrame:
    """Fetch in/out migration for given DeSO areas."""
    if years is None:
        years = [str(y) for y in range(2019, 2024)]

    query = {
        "query": [
            {
                "code": "Region",
                "selection": {"filter": "item", "values": deso_codes}
            },
            {
                "code": "Tid",
                "selection": {"filter": "item", "values": years}
            }
        ],
        "response": {"format": "json"}
    }

    raw = query_table(TABLES["migration"], query)
    if raw:
        return parse_scb_json(raw)
    return pd.DataFrame()


def is_api_available() -> bool:
    """Quick check if SCB API is reachable."""
    try:
        resp = requests.get(f"{SCB_BASE_URL}/BE", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
