# Renewable Energy Forecasting & Battery Storage Analysis for Germany

A comprehensive system for analyzing renewable energy scenarios with battery storage optimization and interactive data exploration.

## Project Summary

This project extends the original 2012-2020 shortfall analysis with:

- **Three-scenario forecasting** (best/average/worst case) for solar and wind generation
- **Battery storage optimization** modeling (5-50 GWh configurations)
- **Interactive dashboard** for stakeholder exploration and decision-making
- **Publication-ready visualizations** for presentations and reports is organized into modular files for data processing, modeling, and visualization. The dashboard provides real-time insights into renewable coverage, shortfall patterns, and storage impacts.

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

### Documentation

```txt
├── README.md                    # This file
├── PROJECT_SUMMARY.md          # Comprehensive project overview
├── DASHBOARD_README.md         # Dashboard setup & features
├── SCENARIO_ANALYSIS_GUIDE.md  # Methodology & interpretation
└── visualizations/             # Static PNG charts (6 files, 300 DPI)
```

---

## Phase Breakdown

Each phase corresponds to a notebook in the `src/` directory, with outputs feeding into the next phase. The final dashboard integrates all results for interactive exploration. The python files in the `app/` directory contain the core logic for scenario generation, battery modeling, and dashboard functionality, while the notebooks in `src/` provide detailed analysis and visualization steps.

### Phase 1: Data Loading & Scenarios

`ingestion/01_data_ingestion.ipynb` → `app/generate_scenarios.py`

- Loaded OPSD electricity API (50,401 hourly records)
- Generated synthetic weather patterns
- Created 3 scenario forecasts with multipliers
- Output: `scenario_forecasts.csv` (6,303 daily records)

### Phase 2: Battery Storage Model

`models/03_modeling.ipynb` → `app/battery_storage_model.py`

- Implemented greedy dispatch algorithm
- Modeled 4 battery configurations (5/10/20/50 GWh)
- Analyzed cycling patterns and economics
- Output: `battery_storage_analysis.csv`, `dispatch_*.csv`

### Phase 3: Visualizations

`visualization/05_visualization.ipynb` → `app/create_visualizations.py`

- 6 static publication-ready PNG charts (300 DPI)
- Stacked area, line chart, small multiples, heatmap, etc.
- Output: `visualizations/` directory

### Phase 4: Interactive Dashboard

`app/dashboard.py`

- Built multi-page Dash web application
- 4 pages: Overview, Time Series, Storage, Metrics
- Real-time filtering and interactive charts
- Output: Live dashboard at <http://localhost:8050>

---

## How to Use

### For Policy Makers

```bash
python dashboard.py
# Navigate to Overview page
# Select scenario → view coverage % and shortfall
# Use to assess renewable adequacy
```

### For Grid Operators

```bash
# Time Series page: detailed shortfall patterns
# Storage page: battery dispatch optimization
# Export data for operational planning
```

### For Investors

```bash
# Storage page: battery CAPEX and payback analysis
# Metrics page: scenario comparison (risk assessment)
# Compare best/worst case ROI
```

### For Researchers

```bash
# Edit generate_scenarios.py to modify scenario multipliers
# Create new battery configs in battery_storage_model.py
# Export data for publication or further analysis
```

---

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Plotly Dash | Interactive dashboard |
| **Charting** | Plotly.js | Real-time visualizations |
| **Backend** | Python Flask | Development server |
| **Data Processing** | Pandas, NumPy | Scenario generation |
| **Optimization** | Custom Greedy Algorithm | Battery dispatch |
| **UI Framework** | Bootstrap | Responsive styling |

### Dependencies

See [requirements.txt](requirements.txt) for full list. Key packages:

- `plotly` - Interactive charts
- `dash` - Web framework
- `dash-bootstrap-components` - UI styling
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `prophet` - Time series forecasting

---

## Documentation

### Main Documents

1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** ← Start here for overview
   - Complete project architecture
   - Technical decisions and rationale
   - Key metrics and statistics
   - Future enhancements

2. **[DASHBOARD_README.md](DASHBOARD_README.md)** ← For dashboard users
   - Features and pages
   - How to use each component
   - Interpretation guide
   - Troubleshooting

3. **[SCENARIO_ANALYSIS_GUIDE.md](SCENARIO_ANALYSIS_GUIDE.md)** ← For methodology
   - Scenario definitions
   - Visualization explanations
   - Use cases and decision-making
   - Assumptions and limitations

---

## Key Files Explained

### battery_storage_model.py

Implements battery storage optimization:

- **BatteryConfig class**: Configurable battery parameters
- **calculate_battery_dispatch()**: Greedy dispatch algorithm
- **analyze_battery_impact()**: Metrics calculation
- **Output**: Battery analysis CSVs and dispatch details

Key features:

- Round-trip efficiency modeling (87% realistic)
- SOC bounds enforcement (20-100%)
- Rate limit constraints (1-5 GW)
- Economic metrics (CAPEX, O&M, payback)

### dashboard.py

Multi-page Plotly/Dash application:

- **4 Pages**: Overview, Time Series, Battery, Metrics
- **12+ Charts**: Real-time interactive visualizations
- **Callbacks**: Responsive to user interactions
- **Color scheme**: Purple/pink palette matching existing viz

Run with: `python dashboard.py`

### generate_scenarios.py

Data pipeline for scenario generation:

- **Data Loading**: OPSD API electricity data
- **Scenario Definition**: Worst/average/best multipliers
- **Weather Synthesis**: Realistic synthetic patterns
- **Output**: scenario_forecasts.csv (6,303 rows)

Modifiable parameters:

- Capacity factor multipliers (line 129-170)
- Date range (line 49)
- Synthetic weather parameters (line 41-104)

---

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

### Related Documentation

- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete technical overview
- [DASHBOARD_README.md](DASHBOARD_README.md) - Dashboard user guide
- [SCENARIO_ANALYSIS_GUIDE.md](SCENARIO_ANALYSIS_GUIDE.md) - Methodology

### External Resources

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

## Original Analysis

The original notebook (`Renewable Energy Data Analysis project.ipynb`) contains:

- EDA of 2012-2020 Germany electricity data
- Random Forest and Prophet forecasting models (R² ~0.98 and ~0.77)
- Weather impact analysis and feature importance

This project builds on that foundation with scenario analysis and storage optimization.

---

## Support

For questions about:

- **Dashboard**: See [DASHBOARD_README.md](DASHBOARD_README.md)
- **Battery Model**: See `battery_storage_model.py` docstrings
- **Scenarios**: See [SCENARIO_ANALYSIS_GUIDE.md](SCENARIO_ANALYSIS_GUIDE.md)
- **Data Pipeline**: See `generate_scenarios.py` comments

---

## Credits
Team members: Varsha Roopchand, Daniel Mangal, Micah Hosein, Adam Mohammed, Kaitlyn Khan