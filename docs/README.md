# Renewable Energy Forecasting & Battery Storage Analysis for Germany

A system for modeling renewable energy scenarios and evaluating battery storage impacts through interactive analysis.

## Project Summary

This project extends the original 2012-2020 shortfall analysis with:

- **Three-scenario forecasting** (best/average/worst case) for solar and wind generation
- **Battery storage optimization** modeling (5-50 GWh configurations)
- **Interactive dashboard** for stakeholder exploration and decision-making
- **Publication-ready visualizations** for presentations and reports
- Modular code structure for data processing, modeling, and visualization

---

## Quick Start

### Prerequisites

```bash
# Python 3.8+ with pip
python --version  # Should be 3.8+
```

### Installation & Running Dashboard

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Regenerate raw and processed data
python app/generate_scenarios.py

# 3. Run battery storage analysis
python app/battery_storage_model.py

# 4. Start interactive dashboard
python app/dashboard.py

# 5. Open browser
# Navigate to: http://localhost:8050
```

### Dashboard Features

- **Overview Page**: KPI cards and scenario selector
- **Time Series Page**: Interactive charts with date range slider
- **Battery Storage Page**: What-if analysis for 5/10/20/50 GWh batteries
- **Metrics Page**: Comprehensive scenario comparison

See [DASHBOARD_README.md](DASHBOARD_README.md) for detailed guide.

---

## Key Results

### Renewable Coverage (Average %)

| Scenario | Coverage | Max Shortfall | Unmet Days |
|----------|----------|---------------|-----------|
| Worst Case | 20.1% | 65.2 GW | 2,099/2,101 |
| Average Case | 29.4% | 60.8 GW | 2,099/2,101 |
| Best Case | 38.6% | 56.1 GW | 2,086/2,101 |

### Battery Impact: 20 GWh Storage

| Scenario | Shortfall Reduction | CAPEX | Residual Shortfall |
|----------|-------------------|-------|-------------------|
| Worst Case | 6.8% | $3.0M | 3,624 GWh/yr |
| Average Case | 7.6% | $3.0M | 3,182 GWh/yr |
| Best Case | 8.7% | $3.0M | 2,741 GWh/yr |

**Key Insight**: Even 50 GWh battery reduces shortfalls by only 11-14% because shortfalls span weeks (seasonal), not hours.

---

## Project Structure

### Code Files

```txt
├── app/dashboard.py                 # Interactive web application (Plotly/Dash)
├── app/battery_storage_model.py    # Battery optimization algorithm
├── app/generate_scenarios.py       # Scenario generation pipeline
├── app/create_visualizations.py    # Static chart generator
├── app/streamlit_app.py            # Optional Streamlit interface
├── src/ingestion/01_data_ingestion.ipynb
├── src/features/02_feature_engineering.ipynb
├── src/models/03_modeling.ipynb
├── src/evaluation/04_evaluation.ipynb
└── src/visualization/05_visualization.ipynb
```

### Data Files

```txt
├── data/raw/germany_energy_weather_2012_2020.csv  # Raw hourly source dataset
├── data/processed/scenario_forecasts.csv          # Scenario forecast dataset
├── data/processed/daily_data.csv                  # Daily aggregate data
├── data/processed/battery_storage_analysis.csv    # Battery metrics summary
├── data/processed/battery_recommendations.csv     # Battery sizing recommendations
├── data/processed/dispatch_*.csv                  # Detailed dispatch results
└── visualizations/                                 # Static PNG charts
```

---

## Pipeline Overview

1. Scenario generation → `generate_scenarios.py`
2. Battery modeling → `battery_storage_model.py`
3. Visualization → `create_visualizations.py`
4. Dashboard → `dashboard.py`

## Tech Stack

- Dash / Plotly – dashboard
- Pandas / NumPy – data processing
- Prophet – forecasting
- Flask – backend

## Data Dictionary

### scenario_forecasts.csv (Main Dataset)

| Column | Unit | Description |
|--------|------|-------------|
| date | YYYY-MM-DD | Day of forecast |
| load_mw | MW | Electricity demand |
| wind_generation_mw | MW | Wind power output |
| solar_generation_mw | MW | Solar power output |
| renewable_total_mw | MW | Wind + Solar |
| shortfall_mw | MW | Unmet demand (Demand - Renewables) |
| surplus_mw | MW | Excess renewable (Renewables - Demand) |
| coverage_pct | % | (Renewables / Demand) × 100 |
| scenario | worst/avg/best | Forecast scenario |

### battery_storage_analysis.csv

| Column | Unit | Description |
|--------|------|-------------|
| scenario | worst/avg/best | Scenario name |
| battery_config | 5/10/20/50 GWh | Battery capacity |
| capacity_gwh | GWh | Total capacity |
| shortfall_reduction_pct | % | % of shortfall eliminated by storage |
| residual_shortfall_gwh | GWh/yr | Remaining unmet demand |
| capex_million_usd | M$ | Capital cost at $150/MWh |
| unmet_days | days | Days with shortfall even after storage |

---

## Troubleshooting

### Dashboard won't start

```bash
# Check Python version (3.8+)
python --version

# Verify dependencies installed
pip install -r requirements.txt

# If port 8050 occupied, edit dashboard.py:
# app.run_server(debug=True, port=8051)
```

### Data not loading

```bash
# Check files exist in current directory
ls scenario_forecasts.csv battery_storage_analysis.csv

# Verify CSV format
head -1 scenario_forecasts.csv  # Should show headers
```

### Import errors

```bash
# Reinstall Dash ecosystem
pip install --upgrade dash plotly dash-bootstrap-components

# Or use venv to isolate
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## References

- [OPSD Data](https://data.open-power-system-data.org/)
- [Dash Documentation](https://dash.plotly.com/)
- [Plotly Python](https://plotly.com/python/)

---

## Use Cases

1. **Policy Development**: Assess renewable adequacy and storage needs
2. **Grid Planning**: Optimize battery deployment timing and sizing
3. **Investment Analysis**: Evaluate battery storage ROI by scenario
4. **Research**: Extend with additional storage types (hydrogen, thermal)
5. **Education**: Teach renewable energy forecasting and optimization

---

## Credits

### Humans

| Name              | Student ID |
|-------------------|------------|
| Varsha Roopchand  | 816039243  |
| Daniel Mangal     | 816004599  |
| Micah Hosein      | 816040436  |
| Adam Mohammed     | 816041441  |
| Kaitlyn Khan      | 816037294  |

### AI Assistance

- Copilot — code generation  
- ChatGPT — writing assistance
  