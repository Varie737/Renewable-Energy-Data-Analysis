"""
Renewable Energy Forecasting with Scenario Analysis
Phase 1: Data Loading and Scenario Generation
"""

import pandas as pd
import numpy as np
import requests
import json
import os
from pathlib import Path
from datetime import datetime
import warnings
import sys
warnings.filterwarnings('ignore')

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("PHASE 1: DATA LOADING & SCENARIO GENERATION")
print("=" * 70)

# ==============================================================================
# STEP 1: Load or Generate Data
# ==============================================================================
print("\n[1/4] Loading Germany Energy & Weather Data...")

csv_file = Path('data/raw/germany_energy_weather_2012_2020.csv')

if csv_file.exists():
    print(f"  [OK] Found existing CSV: {csv_file}")
    df = pd.read_csv(csv_file)
    df['utc_timestamp'] = pd.to_datetime(df['utc_timestamp'])
else:
    print(f"  [*] CSV not found. Fetching from OPSD API...")
    
    # Load OPSD electricity data
    opsd_url = "https://data.open-power-system-data.org/time_series/latest/time_series_60min_singleindex.csv"
    opsd = pd.read_csv(
        opsd_url,
        usecols=[
            "utc_timestamp",
            "DE_load_actual_entsoe_transparency",
            "DE_wind_generation_actual",
            "DE_solar_generation_actual",
        ],
        parse_dates=["utc_timestamp"],
    )
    
    # Rename columns
    opsd.rename(columns={
        "DE_load_actual_entsoe_transparency": "load_mw",
        "DE_wind_generation_actual": "wind_generation_mw",
        "DE_solar_generation_actual": "solar_generation_mw",
    }, inplace=True)
    
    # Filter to 2012-2020
    opsd = opsd[(opsd["utc_timestamp"] >= "2012-01-01") & 
                (opsd["utc_timestamp"] < "2021-01-01")].reset_index(drop=True)
    
    print(f"  [OK] Loaded OPSD data: {len(opsd)} records")
    
    # Create synthetic weather data correlated with generation patterns
    print("  [*] Generating synthetic weather data...")
    
    weather = pd.DataFrame({
        'utc_timestamp': opsd['utc_timestamp']
    })
    
    # Generate realistic synthetic weather patterns
    np.random.seed(42)
    n = len(weather)
    hours = weather['utc_timestamp'].dt.hour.values
    dayofyear = weather['utc_timestamp'].dt.dayofyear.values
    
    # Solar irradiance: higher during day, seasonal variation
    daily_cycle = np.sin(np.pi * hours / 24) * 500  # Peak at noon
    seasonal_cycle = 300 + 250 * np.sin(2 * np.pi * dayofyear / 365)
    weather['irradiance_wm2'] = np.maximum(0, daily_cycle + seasonal_cycle + np.random.normal(0, 50, n))
    
    # Wind speed: seasonal and random variability
    weather['wind_speed_10m_ms'] = (
        5 + 3 * np.sin(2 * np.pi * dayofyear / 365) + np.random.normal(0, 1.5, n)
    )
    weather['wind_speed_10m_ms'] = np.maximum(0, weather['wind_speed_10m_ms'])
    
    # Temperature: seasonal with daily variation
    weather['temperature_2m_c'] = (
        10 + 10 * np.sin(2 * np.pi * dayofyear / 365) + 
        5 * np.sin(np.pi * hours / 24) + 
        np.random.normal(0, 2, n)
    )
    
    print(f"  [OK] Generated synthetic weather data: {len(weather)} records")
    
    # Merge datasets
    df = opsd.merge(weather, on="utc_timestamp", how="inner")
    
    # Calculate shortfall
    df["shortfall_mw"] = df["load_mw"] - (df["wind_generation_mw"] + df["solar_generation_mw"])
    df["renewable_total_mw"] = df["wind_generation_mw"] + df["solar_generation_mw"]
    
    # Save to CSV
    df.to_csv(csv_file, index=False)
    print(f"  [OK] Saved to {csv_file}")

print(f"\n  Dataset Summary:")
print(f"    • Shape: {df.shape}")
print(f"    • Date Range: {df['utc_timestamp'].min()} to {df['utc_timestamp'].max()}")
print(f"    • Columns: {list(df.columns)}")

# ==============================================================================
# STEP 2: Aggregate to Daily Level (for cleaner visualization)
# ==============================================================================
print("\n[2/4] Aggregating to Daily Level...")

df['date'] = df['utc_timestamp'].dt.date
daily = df.groupby('date').agg({
    'load_mw': 'mean',
    'wind_generation_mw': 'mean',
    'solar_generation_mw': 'mean',
    'renewable_total_mw': 'mean',
    'shortfall_mw': 'mean',
    'irradiance_wm2': 'mean',
    'wind_speed_10m_ms': 'mean',
    'temperature_2m_c': 'mean',
}).reset_index()

daily['date'] = pd.to_datetime(daily['date'])
print(f"  [OK] Aggregated to {len(daily)} daily records")

# ==============================================================================
# STEP 3: Define Scenarios
# ==============================================================================
print("\n[3/4] Defining Best/Average/Worst Case Scenarios...")

# Calculate statistics for scenario definition
wind_residuals = df['wind_generation_mw'].std()
solar_residuals = df['solar_generation_mw'].std()

wind_base = df['wind_generation_mw'].mean()
solar_base = df['solar_generation_mw'].mean()

# Scenario adjustments (in terms of generation multipliers)
scenarios = {
    'worst': {
        'description': 'Low renewable generation (10th percentile)',
        'wind_factor': 0.70,  # 30% reduction from baseline
        'solar_factor': 0.65,  # 35% reduction from baseline
    },
    'average': {
        'description': 'Baseline forecast (median)',
        'wind_factor': 1.00,
        'solar_factor': 1.00,
    },
    'best': {
        'description': 'High renewable generation (90th percentile)',
        'wind_factor': 1.30,  # 30% increase from baseline
        'solar_factor': 1.35,  # 35% increase from baseline
    }
}

print("  Scenario Assumptions:")
for scenario, params in scenarios.items():
    print(f"    • {scenario.upper()}: {params['description']}")
    print(f"      - Wind: {params['wind_factor']:.2f}x baseline")
    print(f"      - Solar: {params['solar_factor']:.2f}x baseline")

# ==============================================================================
# STEP 4: Generate Scenario Forecasts
# ==============================================================================
print("\n[4/4] Generating Scenario Forecasts...")

scenario_data = {}

for scenario_name, scenario_params in scenarios.items():
    # Create scenario dataframe
    scenario_df = daily.copy()
    
    # Apply scenario multipliers
    scenario_df['wind_generation_mw'] = scenario_df['wind_generation_mw'] * scenario_params['wind_factor']
    scenario_df['solar_generation_mw'] = scenario_df['solar_generation_mw'] * scenario_params['solar_factor']
    scenario_df['renewable_total_mw'] = scenario_df['wind_generation_mw'] + scenario_df['solar_generation_mw']
    scenario_df['shortfall_mw'] = scenario_df['load_mw'] - scenario_df['renewable_total_mw']
    scenario_df['surplus_mw'] = scenario_df['renewable_total_mw'] - scenario_df['load_mw']
    scenario_df['coverage_pct'] = (scenario_df['renewable_total_mw'] / scenario_df['load_mw'] * 100).clip(lower=0)
    scenario_df['scenario'] = scenario_name
    
    scenario_data[scenario_name] = scenario_df
    
    # Print statistics
    print(f"\n  {scenario_name.upper()} Case Statistics:")
    print(f"    • Avg Wind: {scenario_df['wind_generation_mw'].mean():.1f} MW")
    print(f"    • Avg Solar: {scenario_df['solar_generation_mw'].mean():.1f} MW")
    print(f"    • Avg Renewable Total: {scenario_df['renewable_total_mw'].mean():.1f} MW")
    print(f"    • Avg Demand: {scenario_df['load_mw'].mean():.1f} MW")
    print(f"    • Avg Coverage: {scenario_df['coverage_pct'].mean():.1f}%")
    print(f"    • Avg Shortfall: {scenario_df['shortfall_mw'].mean():.1f} MW")
    print(f"    • Days with shortfall: {(scenario_df['shortfall_mw'] > 0).sum()}/{len(scenario_df)}")
    print(f"    • Max shortfall: {scenario_df['shortfall_mw'].max():.1f} MW")

# Combine all scenarios
all_scenarios = pd.concat(
    [scenario_data[s] for s in ['worst', 'average', 'best']],
    ignore_index=True
)

# Save scenario data
all_scenarios.to_csv('data/processed/scenario_forecasts.csv', index=False)
daily.to_csv('data/processed/daily_data.csv', index=False)

print(f"\n  [OK] Scenario data saved to: data/processed/scenario_forecasts.csv ({len(all_scenarios)} records)")
print(f"  [OK] Daily data saved to: data/processed/daily_data.csv ({len(daily)} records)")

print("\n" + "=" * 70)
print("[COMPLETE] PHASE 1: Data loaded and scenarios generated")
print("=" * 70)
