"""
Demo data & DeSO area configuration.

Provides realistic sample data for JM's key markets when SCB API is unreachable.
Also contains DeSO code mappings for areas where JM typically operates.

NOTE: When running against live SCB, the app fetches the real DeSO list.
This file is a curated subset for fast selection UX.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import hashlib

# ──────────────────────────────────────────────
# DeSO areas grouped by kommun — JM's key markets
# Format: {display_name: deso_code}
# ──────────────────────────────────────────────

DESO_AREAS = {
    "Stockholm": {
        "Norrmalm (centrum)":        "0180A0010",
        "Södermalm (västra)":        "0180A0210",
        "Kungsholmen (östra)":       "0180A0310",
        "Vasastan (norra)":          "0180A0130",
        "Hammarby Sjöstad":          "0180A0850",
        "Liljeholmen":               "0180A0710",
        "Hägersten (östra)":         "0180A0730",
        "Bromma Kyrka":              "0180A0430",
        "Solna centrum":             "0184A0020",
        "Sundbyberg centrum":        "0183A0010",
    },
    "Nacka / Värmdö": {
        "Nacka Strand":              "0182A0020",
        "Saltsjöbaden":              "0182A0060",
        "Boo (centrala)":            "0182A0080",
    },
    "Täby / Danderyd / Lidingö": {
        "Täby centrum":              "0160A0010",
        "Djursholm":                 "0162A0010",
        "Lidingö centrum":           "0186A0010",
    },
    "Uppsala": {
        "Uppsala centrum":           "0380A0010",
        "Luthagen":                  "0380A0030",
        "Rosendal":                  "0380A0050",
    },
    "Göteborg": {
        "Centrum (Inom Vallgraven)": "1480A0010",
        "Majorna":                   "1480A0210",
        "Haga":                      "1480A0050",
        "Kvillebäcken":              "1480A0810",
        "Örgryte":                   "1480A0310",
    },
    "Malmö": {
        "Malmö centrum":             "1280A0010",
        "Västra Hamnen":             "1280A0030",
        "Limhamn":                   "1280A0210",
    },
    "Linköping": {
        "Linköping centrum":         "0580A0010",
        "Lambohov":                  "0580A0060",
    },
    "Lund": {
        "Lund centrum":              "1281A0010",
        "Brunnshög":                 "1281A0040",
    },
}

# Approximate center coordinates for each DeSO area (lat, lon)
DESO_COORDS = {
    # Stockholm
    "0180A0010": (59.3345, 18.0632),   # Norrmalm
    "0180A0210": (59.3150, 18.0600),   # Södermalm
    "0180A0310": (59.3320, 18.0380),   # Kungsholmen
    "0180A0130": (59.3440, 18.0510),   # Vasastan
    "0180A0850": (59.3040, 18.0950),   # Hammarby Sjöstad
    "0180A0710": (59.3100, 18.0200),   # Liljeholmen
    "0180A0730": (59.3000, 18.0050),   # Hägersten
    "0180A0430": (59.3380, 17.9400),   # Bromma Kyrka
    "0184A0020": (59.3600, 18.0000),   # Solna centrum
    "0183A0010": (59.3610, 17.9720),   # Sundbyberg centrum
    # Nacka / Värmdö
    "0182A0020": (59.3180, 18.1350),   # Nacka Strand
    "0182A0060": (59.2800, 18.2100),   # Saltsjöbaden
    "0182A0080": (59.3100, 18.2500),   # Boo
    # Täby / Danderyd / Lidingö
    "0160A0010": (59.4440, 18.0680),   # Täby centrum
    "0162A0010": (59.3970, 18.0900),   # Djursholm
    "0186A0010": (59.3630, 18.1480),   # Lidingö centrum
    # Uppsala
    "0380A0010": (59.8586, 17.6389),   # Uppsala centrum
    "0380A0030": (59.8620, 17.6200),   # Luthagen
    "0380A0050": (59.8480, 17.6500),   # Rosendal
    # Göteborg
    "1480A0010": (57.7089, 11.9746),   # Centrum
    "1480A0210": (57.6900, 11.9350),   # Majorna
    "1480A0050": (57.6980, 11.9580),   # Haga
    "1480A0810": (57.7200, 11.9500),   # Kvillebäcken
    "1480A0310": (57.6950, 12.0050),   # Örgryte
    # Malmö
    "1280A0010": (55.6050, 13.0038),   # Malmö centrum
    "1280A0030": (55.6130, 12.9780),   # Västra Hamnen
    "1280A0210": (55.5830, 12.9350),   # Limhamn
    # Linköping
    "0580A0010": (58.4108, 15.6214),   # Linköping centrum
    "0580A0060": (58.3880, 15.6500),   # Lambohov
    # Lund
    "1281A0010": (55.7047, 13.1910),   # Lund centrum
    "1281A0040": (55.7200, 13.2100),   # Brunnshög
}


def get_all_deso_flat() -> dict[str, str]:
    """Return flat dict {display_label: deso_code} for all areas."""
    flat = {}
    for kommun, areas in DESO_AREAS.items():
        for name, code in areas.items():
            flat[f"{name} ({kommun})"] = code
    return flat


# ──────────────────────────────────────────────
# Demo data generators (realistic synthetic data)
# ──────────────────────────────────────────────

def _seed_for_code(deso_code: str) -> int:
    """Deterministic seed from DeSO code so same area always gives same data."""
    return int(hashlib.md5(deso_code.encode()).hexdigest()[:8], 16) % (2**31)



AGE_GROUPS = ["0-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def generate_demo_population(deso_codes: list[str], labels: dict[str, str] = None) -> pd.DataFrame:
    """
    Generate realistic population data by age group for given DeSO areas.
    A DeSO typically has 700–2700 people.
    """
    rows = []
    for code in deso_codes:
        rng = np.random.RandomState(_seed_for_code(code))
        base_pop = rng.randint(800, 2500)
        label = labels.get(code, code) if labels else code

        # Age distribution (urban Swedish profile)
        age_weights = np.array([0.12, 0.10, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08])
        age_weights = age_weights * (1 + rng.uniform(-0.15, 0.15, len(age_weights)))
        age_weights /= age_weights.sum()

        for year in YEARS:
            # Slight annual growth
            year_pop = int(base_pop * (1 + 0.008 * (year - 2019)) + rng.randint(-20, 20))
            for ag, weight in zip(AGE_GROUPS, age_weights):
                count = max(1, int(year_pop * weight + rng.randint(-5, 5)))
                rows.append({
                    "DeSO": code,
                    "Område": label,
                    "Åldersgrupp": ag,
                    "År": year,
                    "Antal": count,
                })

    return pd.DataFrame(rows)


def generate_demo_income(deso_codes: list[str], labels: dict[str, str] = None) -> pd.DataFrame:
    """
    Generate median disposable income (tkr) per DeSO area.
    Swedish DeSO median income typically ranges 200–450 tkr.
    """
    rows = []
    for code in deso_codes:
        rng = np.random.RandomState(_seed_for_code(code))
        base_income = rng.randint(220, 420)
        label = labels.get(code, code) if labels else code

        for year in [2019, 2020, 2021, 2022, 2023]:
            income = int(base_income * (1 + 0.025 * (year - 2019)) + rng.randint(-8, 8))
            rows.append({
                "DeSO": code,
                "Område": label,
                "År": year,
                "Medianinkomst (tkr)": income,
            })

    return pd.DataFrame(rows)


def generate_demo_migration(deso_codes: list[str], labels: dict[str, str] = None) -> pd.DataFrame:
    """
    Generate in/out migration flows per DeSO area.
    """
    rows = []
    for code in deso_codes:
        rng = np.random.RandomState(_seed_for_code(code))
        base_in = rng.randint(40, 200)
        base_out = rng.randint(35, 180)
        label = labels.get(code, code) if labels else code

        for year in YEARS:
            influx = max(5, int(base_in + rng.randint(-25, 25)))
            outflux = max(5, int(base_out + rng.randint(-25, 25)))
            rows.append({
                "DeSO": code,
                "Område": label,
                "År": year,
                "Inflyttade": influx,
                "Utflyttade": outflux,
                "Nettomigration": influx - outflux,
            })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# DeSO → Kommun mapping (for distributing kommun forecasts)
# First 4 digits of DeSO code = kommun code
# ──────────────────────────────────────────────

KOMMUN_NAMES = {
    "0180": "Stockholm",
    "0183": "Sundbyberg",
    "0184": "Solna",
    "0182": "Nacka",
    "0160": "Täby",
    "0162": "Danderyd",
    "0186": "Lidingö",
    "0380": "Uppsala",
    "1480": "Göteborg",
    "1280": "Malmö",
    "0580": "Linköping",
    "1281": "Lund",
}


def deso_to_kommun(deso_code: str) -> str:
    """Extract kommun code from DeSO code (first 4 digits)."""
    return deso_code[:4]


def generate_demo_kommun_forecast(kommun_codes: list[str]) -> pd.DataFrame:
    """
    Generate demo kommun-level population forecasts (mimics SCB BE0401).
    SCB publishes these annually with 10+ year horizon.
    We generate 2025–2027 (3-year prognosis).
    """
    rows = []
    for kcode in kommun_codes:
        rng = np.random.RandomState(int(kcode) + 42)
        kommun_name = KOMMUN_NAMES.get(kcode, kcode)

        # Base kommun population (realistic sizes)
        kommun_pops = {
            "0180": 990_000, "0183": 55_000, "0184": 85_000, "0182": 105_000,
            "0160": 75_000, "0162": 33_000, "0186": 48_000, "0380": 235_000,
            "1480": 590_000, "1280": 350_000, "0580": 165_000, "1281": 130_000,
        }
        base = kommun_pops.get(kcode, 50_000)

        # Annual growth rate varies by kommun (0.3% – 1.5%)
        growth_rate = 0.003 + rng.uniform(0, 0.012)

        for year in [2025, 2026, 2027]:
            offset = year - 2024
            pop = int(base * (1 + growth_rate) ** offset)
            rows.append({
                "Kommun": kommun_name,
                "Kommunkod": kcode,
                "År": year,
                "Prognos befolkning": pop,
            })

    return pd.DataFrame(rows)


def generate_demo_forecast_deso(
    deso_codes: list[str],
    pop_df: pd.DataFrame,
    labels: dict[str, str] = None,
) -> pd.DataFrame:
    """
    Distribute kommun-level forecast to DeSO level.

    Method: Each DeSO's share of its kommun's population (from latest historical year)
    is applied to the kommun forecast. This assumes the area's relative weight stays stable.

    This is the standard approach when sub-municipal forecasts aren't available.
    """
    if pop_df.empty:
        return pd.DataFrame()

    latest_year = pop_df["År"].max()
    latest_pop = pop_df[pop_df["År"] == latest_year].groupby("DeSO")["Antal"].sum().reset_index()
    latest_pop.columns = ["DeSO", "DeSO_pop"]

    # Get unique kommun codes
    kommun_codes = list(set(deso_to_kommun(c) for c in deso_codes))
    kommun_forecast = generate_demo_kommun_forecast(kommun_codes)

    # Calculate each DeSO's share of its kommun
    latest_pop["Kommunkod"] = latest_pop["DeSO"].apply(deso_to_kommun)

    # Use known kommun populations (not just sum of selected DeSOs)
    kommun_pops_known = {
        "0180": 990_000, "0183": 55_000, "0184": 85_000, "0182": 105_000,
        "0160": 75_000, "0162": 33_000, "0186": 48_000, "0380": 235_000,
        "1480": 590_000, "1280": 350_000, "0580": 165_000, "1281": 130_000,
    }
    latest_pop["Kommun_total"] = latest_pop["Kommunkod"].map(kommun_pops_known)
    latest_pop["Kommun_total"] = latest_pop["Kommun_total"].fillna(
        latest_pop.groupby("Kommunkod")["DeSO_pop"].transform("sum")
    )
    latest_pop["DeSO_share"] = latest_pop["DeSO_pop"] / latest_pop["Kommun_total"]

    # Distribute forecast
    rows = []
    for _, deso_row in latest_pop.iterrows():
        code = deso_row["DeSO"]
        kcode = deso_row["Kommunkod"]
        share = deso_row["DeSO_share"]
        label = labels.get(code, code) if labels else code

        area_forecast = kommun_forecast[kommun_forecast["Kommunkod"] == kcode]
        for _, fc_row in area_forecast.iterrows():
            rows.append({
                "DeSO": code,
                "Område": label,
                "År": fc_row["År"],
                "Prognos befolkning": int(fc_row["Prognos befolkning"] * share),
                "Kommun": fc_row["Kommun"],
            })

    return pd.DataFrame(rows)


def calculate_absorption_capacity(
    pop_df: pd.DataFrame,
    income_df: pd.DataFrame,
    migration_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    mobility_rate: float = 0.06,
    new_pref_share: float = 0.20,
    household_size: float = 1.8,
    labels: dict[str, str] = None,
) -> pd.DataFrame:
    """
    Estimate annual absorption capacity (new apartments/year) per DeSO area.

    Model:
    1. Target population = people aged 25-44 (prime home-buying demographic)
    2. Households = target_pop / household_size
    3. Annual movers = households × mobility_rate
    4. New construction demand = movers × new_construction_preference
    5. Migration bonus = net_migration × new_pref_share / household_size
    6. Total absorption = base demand + migration bonus

    Parameters are adjustable by the user via sliders.
    """
    if pop_df.empty:
        return pd.DataFrame()

    latest_year = pop_df["År"].max()
    pop_latest = pop_df[pop_df["År"] == latest_year]

    rows = []
    for area in pop_latest["Område"].unique():
        area_pop = pop_latest[pop_latest["Område"] == area]
        deso_code = area_pop["DeSO"].iloc[0] if "DeSO" in area_pop.columns else ""

        # Total population
        total_pop = area_pop["Antal"].sum()

        # Buying-age population (25-44)
        buying_age_pop = area_pop[
            area_pop["Åldersgrupp"].isin(["25-34", "35-44"])
        ]["Antal"].sum()

        # Households in target group
        target_households = buying_age_pop / household_size

        # Base demand from mobility
        base_demand = target_households * mobility_rate * new_pref_share

        # Migration bonus
        net_mig = 0
        if not migration_df.empty:
            mig_latest = migration_df[
                (migration_df["Område"] == area) &
                (migration_df["År"] == migration_df["År"].max())
            ]
            if not mig_latest.empty:
                net_mig = mig_latest["Nettomigration"].values[0]

        migration_bonus = max(0, net_mig * new_pref_share / household_size)

        # Income factor (higher income = higher willingness to buy new)
        income_factor = 1.0
        if not income_df.empty:
            inc_latest = income_df[
                (income_df["Område"] == area) &
                (income_df["År"] == income_df["År"].max())
            ]
            if not inc_latest.empty:
                median_inc = inc_latest["Medianinkomst (tkr)"].values[0]
                # Scale: 250 tkr = 0.8x, 350 tkr = 1.0x, 450 tkr = 1.2x
                income_factor = 0.5 + (median_inc / 350) * 0.5
                income_factor = max(0.6, min(1.5, income_factor))

        # Total absorption
        total_absorption = (base_demand + migration_bonus) * income_factor

        # Forecast growth bonus (if area is expected to grow)
        forecast_bonus = 0
        if not forecast_df.empty:
            fc_area = forecast_df[forecast_df["Område"] == area]
            if not fc_area.empty and len(fc_area) >= 2:
                first_fc = fc_area["Prognos befolkning"].iloc[0]
                last_fc = fc_area["Prognos befolkning"].iloc[-1]
                annual_growth = (last_fc - first_fc) / len(fc_area)
                forecast_bonus = max(0, annual_growth * new_pref_share / household_size)

        total_absorption += forecast_bonus

        rows.append({
            "Område": area,
            "DeSO": deso_code,
            "Befolkning": total_pop,
            "Köpålder (25-44)": buying_age_pop,
            "Målhushåll": int(target_households),
            "Basefterfrågan (lgh/år)": round(base_demand, 1),
            "Migrationsbonus": round(migration_bonus, 1),
            "Tillväxtbonus": round(forecast_bonus, 1),
            "Inkomstfaktor": round(income_factor, 2),
            "Nettomigration": net_mig,
            "Absorptionskapacitet (lgh/år)": round(total_absorption, 0),
        })

    return pd.DataFrame(rows)


def generate_demo_age_pyramid(deso_codes: list[str], labels: dict[str, str] = None) -> pd.DataFrame:
    """Generate data for a population pyramid (by sex)."""
    rows = []
    for code in deso_codes:
        rng = np.random.RandomState(_seed_for_code(code))
        base_pop = rng.randint(800, 2500)
        label = labels.get(code, code) if labels else code

        age_weights = np.array([0.12, 0.10, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08])
        age_weights = age_weights * (1 + rng.uniform(-0.15, 0.15, len(age_weights)))
        age_weights /= age_weights.sum()

        for ag, weight in zip(AGE_GROUPS, age_weights):
            total = max(2, int(base_pop * weight))
            male_share = 0.48 + rng.uniform(-0.03, 0.03)
            rows.append({"Område": label, "Åldersgrupp": ag, "Kön": "Man", "Antal": int(total * male_share)})
            rows.append({"Område": label, "Åldersgrupp": ag, "Kön": "Kvinna", "Antal": int(total * (1 - male_share))})

    return pd.DataFrame(rows)
