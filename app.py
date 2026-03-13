"""
JM Marknadsanalys — Demografisk data per DeSO-område
=====================================================
MVP for self-service demographic & demand analysis.

Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from demo_data import (
    DESO_AREAS, DESO_COORDS, get_all_deso_flat,
    generate_demo_population, generate_demo_income,
    generate_demo_migration, generate_demo_age_pyramid,
    generate_demo_forecast_deso, calculate_absorption_capacity,
)
from scb_client import is_api_available, fetch_population_by_age, fetch_income, fetch_migration

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="JM Marknadsanalys",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# JM Brand colors
# ──────────────────────────────────────────────
JM_DARK_GREEN = "#004438"
JM_GREEN = "#00816D"
JM_LIGHT_GREEN = "#7ABFB5"
JM_SAND = "#F5F0EB"
JM_ORANGE = "#E87C03"
JM_DARK = "#1A1A1A"
CHART_COLORS = [JM_GREEN, JM_ORANGE, "#5B9BD5", "#ED7D31", JM_DARK_GREEN, JM_LIGHT_GREEN, "#A5A5A5", "#FFC000"]

# Custom CSS
st.markdown(f"""
<style>
    .stApp {{
        background-color: {JM_SAND};
    }}
    section[data-testid="stSidebar"] {{
        background-color: {JM_DARK_GREEN};
    }}
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] span {{
        color: white !important;
    }}
    h1, h2, h3 {{
        color: {JM_DARK_GREEN} !important;
    }}
    .metric-card {{
        background: white;
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }}
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {JM_GREEN};
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.3rem;
    }}
    div[data-testid="stMetric"] {{
        background: white;
        border-radius: 8px;
        padding: 0.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Check data source
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def check_api():
    return is_api_available()

use_live = check_api()


# ──────────────────────────────────────────────
# Sidebar — Area selection
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/JM_logo.svg/200px-JM_logo.svg.png", width=100)
    st.title("Marknadsanalys")

    if use_live:
        st.success("🟢 Live SCB-data")
    else:
        st.info("🟡 Demodata — starta lokalt för live SCB")

    st.markdown("---")
    st.subheader("Välj områden")

    # Kommun filter first, then DeSO areas
    selected_kommun = st.multiselect(
        "Kommun / region",
        options=list(DESO_AREAS.keys()),
        default=["Stockholm"],
    )

    # Build available DeSO areas based on kommun selection
    available_areas = {}
    for k in selected_kommun:
        available_areas.update(DESO_AREAS.get(k, {}))

    if not available_areas:
        st.warning("Välj minst en kommun ovan")
        st.stop()

    selected_names = st.multiselect(
        "DeSO-områden",
        options=list(available_areas.keys()),
        default=list(available_areas.keys())[:3],
        help="Välj 1–6 områden att jämföra",
    )

    if not selected_names:
        st.warning("Välj minst ett område")
        st.stop()

    if len(selected_names) > 6:
        st.warning("Max 6 områden för tydliga jämförelser")
        selected_names = selected_names[:6]

    # Map names -> codes
    selected_codes = [available_areas[n] for n in selected_names]
    code_to_label = {available_areas[n]: n for n in selected_names}

    st.markdown("---")
    st.subheader("Modellparametrar")
    st.caption("Justera absorptionsmodellen")

    mobility_rate = st.slider(
        "Rörlighet (%/år)",
        min_value=3.0, max_value=10.0, value=6.0, step=0.5,
        help="Andel hushåll som flyttar per år (rikssnitt ~6%)",
    ) / 100

    new_pref_share = st.slider(
        "Nyproduktionspreferens (%)",
        min_value=10.0, max_value=35.0, value=20.0, step=2.5,
        help="Av de som flyttar, hur stor andel föredrar nyproduktion?",
    ) / 100

    household_size = st.slider(
        "Hushållsstorlek",
        min_value=1.2, max_value=2.8, value=1.8, step=0.1,
        help="Genomsnittlig hushållsstorlek i målgruppen",
    )

    st.markdown("---")
    st.caption("Datakälla: SCB (Statistiska centralbyrån)")
    st.caption(f"Antal valda områden: {len(selected_codes)}")


# ──────────────────────────────────────────────
# Load data (live or demo)
# ──────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_population(codes, labels):
    if use_live:
        df = fetch_population_by_age(codes)
        if not df.empty:
            return df
    return generate_demo_population(codes, labels)

@st.cache_data(ttl=3600)
def load_income(codes, labels):
    if use_live:
        df = fetch_income(codes)
        if not df.empty:
            return df
    return generate_demo_income(codes, labels)

@st.cache_data(ttl=3600)
def load_migration(codes, labels):
    if use_live:
        df = fetch_migration(codes)
        if not df.empty:
            return df
    return generate_demo_migration(codes, labels)

@st.cache_data(ttl=3600)
def load_age_pyramid(codes, labels):
    return generate_demo_age_pyramid(codes, labels)


pop_df = load_population(selected_codes, code_to_label)
income_df = load_income(selected_codes, code_to_label)
migration_df = load_migration(selected_codes, code_to_label)
pyramid_df = load_age_pyramid(selected_codes, code_to_label)

# Forecast (kommun-level distributed to DeSO)
forecast_df = generate_demo_forecast_deso(selected_codes, pop_df, code_to_label)

# Absorption capacity
absorption_df = calculate_absorption_capacity(
    pop_df, income_df, migration_df, forecast_df,
    mobility_rate=mobility_rate,
    new_pref_share=new_pref_share,
    household_size=household_size,
    labels=code_to_label,
)


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.title("🏠 Demografisk Marknadsanalys")
st.markdown(f"Jämför efterfråge-indikatorer för **{len(selected_codes)}** DeSO-områden")

# ──────────────────────────────────────────────
# KPI row — summary metrics
# ──────────────────────────────────────────────
if not pop_df.empty:
    latest_year = pop_df["År"].max()
    prev_year = latest_year - 1

    latest_pop = pop_df[pop_df["År"] == latest_year].groupby("Område")["Antal"].sum()
    prev_pop = pop_df[pop_df["År"] == prev_year].groupby("Område")["Antal"].sum()

    total_pop = latest_pop.sum()
    pop_change_pct = ((latest_pop.sum() - prev_pop.sum()) / prev_pop.sum() * 100) if prev_pop.sum() > 0 else 0

    # Working age (25-54) share
    working_age = pop_df[
        (pop_df["År"] == latest_year) &
        (pop_df["Åldersgrupp"].isin(["25-34", "35-44", "45-54"]))
    ]["Antal"].sum()
    working_age_pct = (working_age / total_pop * 100) if total_pop > 0 else 0

    # Latest income
    avg_income = income_df[income_df["År"] == income_df["År"].max()]["Medianinkomst (tkr)"].mean() if not income_df.empty else 0

    # Net migration
    net_mig = migration_df[migration_df["År"] == migration_df["År"].max()]["Nettomigration"].sum() if not migration_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total befolkning", f"{total_pop:,.0f}", f"{pop_change_pct:+.1f}% vs föregående år")
    with col2:
        st.metric("Arbetsför ålder (25–54)", f"{working_age_pct:.0f}%")
    with col3:
        st.metric("Snittinkomst (median)", f"{avg_income:.0f} tkr")
    with col4:
        st.metric("Nettomigration", f"{net_mig:+.0f}", "senaste året")

st.markdown("---")

# ──────────────────────────────────────────────
# Tab layout for different analyses
# ──────────────────────────────────────────────
tab_map, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🗺️ Karta", "📊 Befolkning", "👥 Åldersstruktur", "💰 Inkomst", "🔄 Migration",
    "🔮 Prognos", "🏗️ Marknadsdjup", "📋 Exportera"
])


# ── TAB MAP: Geographic overview ──
with tab_map:
    st.subheader("Geografisk översikt")

    # Build map data by combining coordinates with metrics
    map_rows = []
    for name in selected_names:
        code = available_areas[name]
        coords = DESO_COORDS.get(code)
        if not coords:
            continue

        row_data = {
            "Område": name,
            "DeSO": code,
            "lat": coords[0],
            "lon": coords[1],
        }

        # Add population
        if not pop_df.empty:
            area_pop = pop_df[(pop_df["Område"] == name) & (pop_df["År"] == pop_df["År"].max())]
            row_data["Befolkning"] = int(area_pop["Antal"].sum()) if not area_pop.empty else 0
        else:
            row_data["Befolkning"] = 0

        # Add absorption
        if not absorption_df.empty:
            abs_row = absorption_df[absorption_df["Område"] == name]
            row_data["Absorption (lgh/år)"] = int(abs_row["Absorptionskapacitet (lgh/år)"].values[0]) if not abs_row.empty else 0
        else:
            row_data["Absorption (lgh/år)"] = 0

        # Add income
        if not income_df.empty:
            inc_row = income_df[(income_df["Område"] == name) & (income_df["År"] == income_df["År"].max())]
            row_data["Medianinkomst (tkr)"] = int(inc_row["Medianinkomst (tkr)"].values[0]) if not inc_row.empty else 0
        else:
            row_data["Medianinkomst (tkr)"] = 0

        map_rows.append(row_data)

    if map_rows:
        map_df = pd.DataFrame(map_rows)

        # Color metric selector
        color_metric = st.radio(
            "Färglägg efter:",
            ["Absorption (lgh/år)", "Befolkning", "Medianinkomst (tkr)"],
            horizontal=True,
        )

        # Ensure minimum marker size
        map_df["marker_size"] = map_df[color_metric]
        min_size = map_df["marker_size"].min()
        max_size = map_df["marker_size"].max()
        if max_size > min_size:
            map_df["marker_size_scaled"] = 10 + (map_df["marker_size"] - min_size) / (max_size - min_size) * 30
        else:
            map_df["marker_size_scaled"] = 20

        # Build hover text
        map_df["hover"] = map_df.apply(
            lambda r: (
                f"<b>{r['Område']}</b><br>"
                f"Befolkning: {r['Befolkning']:,}<br>"
                f"Absorption: {r['Absorption (lgh/år)']} lgh/år<br>"
                f"Medianinkomst: {r['Medianinkomst (tkr)']} tkr"
            ), axis=1
        )

        fig_map = px.scatter_mapbox(
            map_df,
            lat="lat",
            lon="lon",
            size="marker_size_scaled",
            color=color_metric,
            hover_name="Område",
            hover_data={
                "Befolkning": True,
                "Absorption (lgh/år)": True,
                "Medianinkomst (tkr)": True,
                "lat": False,
                "lon": False,
                "marker_size_scaled": False,
            },
            color_continuous_scale=[JM_LIGHT_GREEN, JM_GREEN, JM_DARK_GREEN],
            size_max=25,
            zoom=10 if len(set(map_df["lat"].round(0))) <= 2 else 5,
            mapbox_style="open-street-map",
        )
        fig_map.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Summary table below map
        st.dataframe(
            map_df[["Område", "Befolkning", "Absorption (lgh/år)", "Medianinkomst (tkr)"]].sort_values(
                color_metric, ascending=False
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Koordinater saknas för valda områden.")


# ── TAB 1: Population overview ──
with tab1:
    st.subheader("Befolkningsutveckling per område")

    if not pop_df.empty:
        # Total population per area per year
        pop_total = pop_df.groupby(["Område", "År"])["Antal"].sum().reset_index()

        fig = px.line(
            pop_total,
            x="År", y="Antal", color="Område",
            markers=True,
            color_discrete_sequence=CHART_COLORS,
            labels={"Antal": "Befolkning", "År": ""},
        )
        fig.update_layout(
            plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.15),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Age group breakdown for latest year
        st.subheader(f"Åldersfördelning ({latest_year})")
        pop_latest = pop_df[pop_df["År"] == latest_year]

        fig2 = px.bar(
            pop_latest,
            x="Åldersgrupp", y="Antal", color="Område",
            barmode="group",
            color_discrete_sequence=CHART_COLORS,
            labels={"Antal": "Antal personer", "Åldersgrupp": ""},
        )
        fig2.update_layout(plot_bgcolor="white", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig2, use_container_width=True)

        # Demand indicator: share of 25-44 (prime home-buying age)
        st.subheader("🎯 Efterfrågeindikator: Andel 25–44 år (primär bostadsköpargrupp)")
        buying_age = pop_latest[pop_latest["Åldersgrupp"].isin(["25-34", "35-44"])]
        buying_share = buying_age.groupby("Område")["Antal"].sum() / pop_latest.groupby("Område")["Antal"].sum() * 100
        buying_share = buying_share.reset_index()
        buying_share.columns = ["Område", "Andel 25-44 (%)"]
        buying_share = buying_share.sort_values("Andel 25-44 (%)", ascending=True)

        fig3 = px.bar(
            buying_share,
            x="Andel 25-44 (%)", y="Område",
            orientation="h",
            color_discrete_sequence=[JM_GREEN],
            labels={"Andel 25-44 (%)": "Andel (%)"},
        )
        fig3.update_layout(plot_bgcolor="white", showlegend=False)
        fig3.add_vline(x=34, line_dash="dash", line_color=JM_ORANGE,
                       annotation_text="Rikssnitt ~34%", annotation_position="top right")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Ingen befolkningsdata tillgänglig.")


# ── TAB 2: Age pyramid ──
with tab2:
    st.subheader("Befolkningspyramid per område")

    if not pyramid_df.empty:
        for area_name in selected_names:
            area_data = pyramid_df[pyramid_df["Område"] == area_name].copy()
            if area_data.empty:
                continue

            male = area_data[area_data["Kön"] == "Man"].copy()
            female = area_data[area_data["Kön"] == "Kvinna"].copy()
            male["Antal"] = -male["Antal"]  # Flip for pyramid

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=male["Åldersgrupp"], x=male["Antal"], name="Man",
                orientation="h", marker_color=JM_GREEN,
            ))
            fig.add_trace(go.Bar(
                y=female["Åldersgrupp"], x=female["Antal"], name="Kvinna",
                orientation="h", marker_color=JM_ORANGE,
            ))
            fig.update_layout(
                title=area_name,
                barmode="overlay",
                bargap=0.1,
                plot_bgcolor="white",
                xaxis=dict(title="Antal", tickvals=[]),
                height=300,
                margin=dict(t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)


# ── TAB 3: Income ──
with tab3:
    st.subheader("Medianinkomst (disponibel, tkr)")

    if not income_df.empty:
        fig = px.line(
            income_df,
            x="År", y="Medianinkomst (tkr)", color="Område",
            markers=True,
            color_discrete_sequence=CHART_COLORS,
            labels={"Medianinkomst (tkr)": "Median disp. inkomst (tkr)", "År": ""},
        )
        fig.update_layout(
            plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.15),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Income growth rate
        st.subheader("Inkomsttillväxt (genomsnittlig årlig)")
        latest = income_df["År"].max()
        earliest = income_df["År"].min()
        growth = income_df.groupby("Område").apply(
            lambda g: ((g[g["År"] == latest]["Medianinkomst (tkr)"].values[0] /
                        g[g["År"] == earliest]["Medianinkomst (tkr)"].values[0]) ** (1 / (latest - earliest)) - 1) * 100
            if len(g[g["År"] == latest]) > 0 and len(g[g["År"] == earliest]) > 0 else 0
        ).reset_index()
        growth.columns = ["Område", "Årlig tillväxt (%)"]
        growth = growth.sort_values("Årlig tillväxt (%)", ascending=True)

        fig2 = px.bar(
            growth, x="Årlig tillväxt (%)", y="Område",
            orientation="h",
            color_discrete_sequence=[JM_GREEN],
        )
        fig2.update_layout(plot_bgcolor="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # Purchasing power insight
        st.info("""
        💡 **Köpkraftsindikator:** Områden med hög medianinkomst OCH positiv tillväxt signalerar
        stark efterfrågan på nyproduktion. Kombinera med åldersstruktur (fliken Befolkning) för
        att identifiera områden där köpstarka hushåll i åldern 25–44 växer.
        """)
    else:
        st.info("Ingen inkomstdata tillgänglig.")


# ── TAB 4: Migration ──
with tab4:
    st.subheader("In- och utflyttning")

    if not migration_df.empty:
        # Net migration trend
        fig = px.bar(
            migration_df,
            x="År", y="Nettomigration", color="Område",
            barmode="group",
            color_discrete_sequence=CHART_COLORS,
            labels={"Nettomigration": "Netto (inflyttade − utflyttade)", "År": ""},
        )
        fig.update_layout(plot_bgcolor="white", legend=dict(orientation="h", y=-0.15))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)

        # Detailed in/out
        st.subheader("Detaljerad in-/utflyttning (senaste år)")
        latest_mig = migration_df[migration_df["År"] == migration_df["År"].max()]

        col1, col2 = st.columns(2)
        with col1:
            fig2 = px.bar(
                latest_mig, x="Område", y=["Inflyttade", "Utflyttade"],
                barmode="group",
                color_discrete_sequence=[JM_GREEN, JM_ORANGE],
                labels={"value": "Antal", "variable": ""},
            )
            fig2.update_layout(plot_bgcolor="white", xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            # Migration intensity (turnover relative to area)
            st.markdown("**Migrationsdynamik**")
            st.markdown("""
            Hög omsättning (mycket in- OCH utflyttning) tyder på ett dynamiskt område
            med aktiv bostadsmarknad. Positivt netto = ökande efterfrågan.
            """)
            for _, row in latest_mig.iterrows():
                total_flow = row["Inflyttade"] + row["Utflyttade"]
                net = row["Nettomigration"]
                emoji = "🟢" if net > 0 else "🔴" if net < 0 else "⚪"
                st.markdown(f"{emoji} **{row['Område']}**: {total_flow} total rörlighet, netto {net:+d}")

        st.info("""
        💡 **Efterfrågesignal:** Områden med positivt netto och hög total rörlighet
        har störst potential för nyproduktion — folk *vill* flytta dit och marknaden är aktiv.
        """)
    else:
        st.info("Ingen migrationsdata tillgänglig.")


# ── TAB 5: Prognos (3-year forecast) ──
with tab5:
    st.subheader("Befolkningsprognos (3 år)")
    st.markdown("""
    Prognosen baseras på SCB:s kommunala befolkningsprognos, fördelad till DeSO-nivå
    utifrån varje områdes nuvarande andel av kommunens befolkning.
    """)

    if not forecast_df.empty and not pop_df.empty:
        # Combine historical + forecast for each area
        latest_year = pop_df["År"].max()
        hist_totals = pop_df.groupby(["Område", "År"])["Antal"].sum().reset_index()
        hist_totals.columns = ["Område", "År", "Befolkning"]
        hist_totals["Typ"] = "Historisk"

        fc_totals = forecast_df[["Område", "År", "Prognos befolkning"]].copy()
        fc_totals.columns = ["Område", "År", "Befolkning"]
        fc_totals["Typ"] = "Prognos"

        combined = pd.concat([hist_totals, fc_totals], ignore_index=True)

        fig = px.line(
            combined,
            x="År", y="Befolkning", color="Område",
            line_dash="Typ",
            markers=True,
            color_discrete_sequence=CHART_COLORS,
            labels={"Befolkning": "Antal invånare", "År": ""},
        )
        fig.update_layout(
            plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.2),
            hovermode="x unified",
        )
        # Add a vertical line at the boundary between historical and forecast
        fig.add_vline(x=latest_year + 0.5, line_dash="dot", line_color="gray",
                      annotation_text="← Historisk | Prognos →", annotation_position="top")
        st.plotly_chart(fig, use_container_width=True)

        # Growth summary table
        st.subheader("Prognostiserad tillväxt")
        growth_rows = []
        for area in forecast_df["Område"].unique():
            fc_area = forecast_df[forecast_df["Område"] == area]
            hist_area = hist_totals[hist_totals["Område"] == area]
            if hist_area.empty or fc_area.empty:
                continue
            current = hist_area[hist_area["År"] == latest_year]["Befolkning"].values[0]
            future = fc_area[fc_area["År"] == fc_area["År"].max()]["Prognos befolkning"].values[0]
            change = future - current
            change_pct = (change / current * 100) if current > 0 else 0
            growth_rows.append({
                "Område": area,
                f"Befolkning {latest_year}": int(current),
                f"Prognos {fc_area['År'].max()}": int(future),
                "Förändring": f"{change:+d}",
                "Förändring (%)": f"{change_pct:+.1f}%",
            })
        if growth_rows:
            st.dataframe(pd.DataFrame(growth_rows), use_container_width=True, hide_index=True)

        st.info("""
        💡 **Metod:** Kommunprognos × DeSO-andel. Antagande: varje DeSO behåller sin
        relativa andel av kommunens befolkning. I verkligheten kan nybyggnation eller
        stadsomvandling förskjuta detta — justera manuellt vid behov.
        """)
    else:
        st.info("Ingen prognosdata tillgänglig.")


# ── TAB 6: Marknadsdjup / Absorption ──
with tab6:
    st.subheader("🏗️ Marknadsdjup — Absorptionskapacitet")
    st.markdown("""
    **Hur många nya lägenheter per år kan marknaden i varje område absorbera utan att störa prisbilden?**

    Modellen beräknar efterfrågan utifrån köpstark befolkning (25–44 år), rörlighet,
    nyproduktionspreferens, migration och inkomstnivå. Justera parametrarna i sidomenyn.
    """)

    if not absorption_df.empty:
        # Main chart: absorption per area
        abs_sorted = absorption_df.sort_values("Absorptionskapacitet (lgh/år)", ascending=True)

        fig = px.bar(
            abs_sorted,
            x="Absorptionskapacitet (lgh/år)", y="Område",
            orientation="h",
            color_discrete_sequence=[JM_GREEN],
            labels={"Absorptionskapacitet (lgh/år)": "Lägenheter / år"},
        )
        fig.update_layout(
            plot_bgcolor="white",
            showlegend=False,
            height=max(300, len(abs_sorted) * 60),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Breakdown waterfall for each area
        st.subheader("Detaljerad nedbrytning")

        for _, row in absorption_df.iterrows():
            with st.expander(f"**{row['Område']}** — {int(row['Absorptionskapacitet (lgh/år)'])} lgh/år"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Befolkning 25–44", f"{int(row['Köpålder (25-44)'])}")
                    st.metric("Målhushåll", f"{int(row['Målhushåll'])}")
                with col2:
                    st.metric("Basefterfrågan", f"{row['Basefterfrågan (lgh/år)']} lgh/år")
                    st.metric("Migrationsbonus", f"+{row['Migrationsbonus']} lgh/år")
                with col3:
                    st.metric("Tillväxtbonus", f"+{row['Tillväxtbonus']} lgh/år")
                    st.metric("Inkomstfaktor", f"×{row['Inkomstfaktor']}")

                # Mini waterfall
                fig_wf = go.Figure(go.Waterfall(
                    name="", orientation="v",
                    measure=["absolute", "relative", "relative", "total"],
                    x=["Basefterfrågan", "Migration", "Tillväxt", "Totalt"],
                    y=[
                        row["Basefterfrågan (lgh/år)"] * row["Inkomstfaktor"],
                        row["Migrationsbonus"] * row["Inkomstfaktor"],
                        row["Tillväxtbonus"],
                        0,  # auto-calculated as total
                    ],
                    connector={"line": {"color": "gray", "dash": "dot"}},
                    increasing={"marker": {"color": JM_GREEN}},
                    totals={"marker": {"color": JM_DARK_GREEN}},
                ))
                fig_wf.update_layout(
                    plot_bgcolor="white", height=250,
                    margin=dict(t=20, b=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_wf, use_container_width=True)

        # Comparison summary
        st.subheader("Jämförelsetabell")
        display_cols = ["Område", "Befolkning", "Köpålder (25-44)", "Nettomigration",
                        "Inkomstfaktor", "Absorptionskapacitet (lgh/år)"]
        st.dataframe(
            absorption_df[display_cols].sort_values("Absorptionskapacitet (lgh/år)", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.info(f"""
        💡 **Modellens antaganden:** Rörlighet {mobility_rate*100:.0f}% | Nyproduktionspreferens
        {new_pref_share*100:.0f}% | Hushållsstorlek {household_size:.1f} | Inkomstjusterad.
        Ändra parametrarna i sidomenyn och se hur resultaten förändras.
        Modellen ger en **indikation** — komplettera med lokal marknadskunskap.
        """)
    else:
        st.info("Kan inte beräkna absorptionskapacitet — befolkningsdata saknas.")


# ── TAB 7: Export ──
with tab7:
    st.subheader("Exportera data")
    st.markdown("Ladda ner rådata som Excel för vidare analys eller rapportering.")

    @st.cache_data
    def create_excel_export(pop, inc, mig, fc, absorb):
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            if not pop.empty:
                pop.to_excel(writer, sheet_name="Befolkning", index=False)
            if not inc.empty:
                inc.to_excel(writer, sheet_name="Inkomst", index=False)
            if not mig.empty:
                mig.to_excel(writer, sheet_name="Migration", index=False)
            if not fc.empty:
                fc.to_excel(writer, sheet_name="Prognos", index=False)
            if not absorb.empty:
                absorb.to_excel(writer, sheet_name="Marknadsdjup", index=False)
        return buffer.getvalue()

    excel_data = create_excel_export(pop_df, income_df, migration_df, forecast_df, absorption_df)
    st.download_button(
        label="📥 Ladda ner Excel",
        data=excel_data,
        file_name="jm_marknadsdata.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("---")
    st.subheader("Dataöversikt")
    with st.expander("Befolkningsdata"):
        st.dataframe(pop_df, use_container_width=True)
    with st.expander("Inkomstdata"):
        st.dataframe(income_df, use_container_width=True)
    with st.expander("Migrationsdata"):
        st.dataframe(migration_df, use_container_width=True)
    with st.expander("Prognosdata"):
        st.dataframe(forecast_df, use_container_width=True)
    with st.expander("Absorptionskapacitet"):
        st.dataframe(absorption_df, use_container_width=True)


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.caption(
    "JM Marknadsanalys MVP • Data: SCB (Statistiska centralbyrån) • "
    f"{'🟢 Live data' if use_live else '🟡 Demodata'}"
)
