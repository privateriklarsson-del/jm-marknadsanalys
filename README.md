# JM Marknadsanalys — Demografisk MVP

Self-service dashboard for demographic & demand analysis at DeSO level, built on SCB's free API.

## Quick start

```bash
# 1. Clone / copy this folder
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Opens at `http://localhost:8501`. The app auto-detects if SCB's API is reachable — if yes, it pulls live data; if not, it shows realistic demo data.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Streamlit   │────▶│  scb_client  │────▶│  SCB REST API  │
│  Dashboard   │     │  (caching)   │     │  (free, public)│
│              │     └──────────────┘     └────────────────┘
│  - Charts    │
│  - KPIs      │     ┌──────────────┐
│  - Export    │────▶│  demo_data   │  (fallback when API unavailable)
└─────────────┘     └──────────────┘
```

### Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit dashboard — all UI and visualizations |
| `scb_client.py` | SCB API client with rate limiting and file-based caching |
| `demo_data.py` | DeSO area definitions (JM markets) + synthetic demo data |
| `requirements.txt` | Python dependencies |

### Data flow

1. User selects kommun → DeSO areas in the sidebar
2. App calls `scb_client` functions (population, income, migration)
3. `scb_client` checks local cache → calls SCB API if stale → returns DataFrame
4. App renders Plotly charts + KPIs + export functionality

### Caching

- SCB responses are cached to `./cache/` as JSON files (24h TTL)
- Streamlit's `@st.cache_data` provides in-memory caching per session
- This keeps the app snappy and respects SCB's rate limits

## SCB API reference

- Base URL: `https://api.scb.se/OV0104/v1/doris/sv/ssd/`
- Documentation: https://www.scb.se/vara-tjanster/oppna-data/api-for-statistikdatabasen/
- Rate limit: ~10 requests per 10 seconds
- No API key needed

### Key tables used

| Table path | Content |
|------------|---------|
| `BE/BE0101/BE0101A/FolsijkDeSO` | Population by age, sex, DeSO |
| `HE/HE0110/HE0110A/SamijsInk1DeSO` | Income by DeSO |
| `BE/BE0101/BE0101J/FlyijttDeSOReg` | Migration flows by DeSO |

> **Note:** Table paths may change when SCB updates their database structure.
> If a table returns errors, check https://www.scb.se/hitta-statistik/ for current paths.

## Extending the MVP

### Add more DeSO areas
Edit `DESO_AREAS` in `demo_data.py`. Find DeSO codes at:
https://www.scb.se/hitta-statistik/regional-statistik-och-kartor/regionala-indelningar/deso/

### Add new data dimensions
1. Find the SCB table path (browse the API tree or scb.se)
2. Add a fetch function in `scb_client.py`
3. Add a demo data generator in `demo_data.py`
4. Add a new tab in `app.py`

### Future roadmap ideas
- **Booli API integration** for comparable sales data
- **Map view** with DeSO boundaries (requires GeoJSON from SCB)
- **Forecasting** using SCB's population projection tables (BE0401)
- **JM internal data** overlay (historical project outcomes)
- **Competition layer** from building permit data
- **Authentication** via Azure AD for internal deployment
