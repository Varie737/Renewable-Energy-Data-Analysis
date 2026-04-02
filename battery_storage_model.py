"""
Battery Storage Optimization Model for Renewable Energy Scenarios

This module implements a greedy battery storage dispatch algorithm to optimize
charging/discharging patterns across three scenarios (worst/average/best case).
It analyzes:
  - Shortfall reduction with various battery capacities
  - Optimal charge/discharge timing
  - Seasonal cycling patterns
  - Economic viability metrics
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass


@dataclass
class BatteryConfig:
    """Battery storage system parameters."""
    capacity_gwh: float  # Total energy capacity (GWh)
    charge_rate_gw: float  # Max charging rate (GW)
    discharge_rate_gw: float  # Max discharging rate (GW)
    round_trip_efficiency: float  # Efficiency factor (0-1)
    min_soc_pct: float  # Minimum state of charge (%)
    max_soc_pct: float  # Maximum state of charge (%)
    capex_per_mwh: float  # Capital cost ($/MWh) - for economic analysis
    annual_opex_pct: float  # Annual O&M as % of CAPEX


def calculate_battery_dispatch(
    scenario_df: pd.DataFrame,
    battery_config: BatteryConfig,
    dispatch_method: str = "greedy"
) -> pd.DataFrame:
    """
    Calculate optimal battery dispatch for a given scenario.
    
    Uses a greedy algorithm: charge during surplus periods, discharge during shortfalls.
    Respects physical constraints (SOC bounds, rate limits, round-trip efficiency).
    
    Args:
        scenario_df: DataFrame with columns ['date', 'load_mw', 'renewable_total_mw', 
                     'shortfall_mw', 'surplus_mw']
        battery_config: BatteryConfig object with system parameters
        dispatch_method: Dispatch strategy ('greedy' for rolling-window optimization)
    
    Returns:
        DataFrame with columns: date, load_mw, renewable_total_mw, shortfall_mw,
                  battery_charge_mw, battery_discharge_mw, battery_soc_gwh,
                  battery_soc_pct, unmet_demand_mw, net_shortfall_mw
    """
    
    result_rows = []
    capacity_gwh = battery_config.capacity_gwh
    capacity_mwh = capacity_gwh * 1000
    charge_rate_mw = battery_config.charge_rate_gw * 1000
    discharge_rate_mw = battery_config.discharge_rate_gw * 1000
    efficiency = battery_config.round_trip_efficiency
    min_soc_mwh = capacity_mwh * battery_config.min_soc_pct / 100
    max_soc_mwh = capacity_mwh * battery_config.max_soc_pct / 100
    
    # Initialize battery state
    current_soc_mwh = capacity_mwh * 0.5  # Start at 50% SOC
    
    for idx, row in scenario_df.iterrows():
        date = row['date']
        load_mw = row['load_mw']
        renewable_mw = row['renewable_total_mw']
        shortfall_mw = row['shortfall_mw']
        surplus_mw = row['surplus_mw']
        
        # Handle missing values
        if pd.isna(load_mw) or pd.isna(renewable_mw):
            continue
        
        battery_charge_mw = 0.0
        battery_discharge_mw = 0.0
        unmet_demand_mw = shortfall_mw
        
        # Greedy dispatch: charge during surplus, discharge during shortfall
        if surplus_mw > 0:
            # Can charge: limited by charge rate and available SOC headroom
            max_charge = min(
                surplus_mw,  # Available surplus
                charge_rate_mw,  # Physical rate limit
                (max_soc_mwh - current_soc_mwh) / efficiency  # SOC headroom (accounting for round-trip loss)
            )
            battery_charge_mw = max(0, max_charge)
            current_soc_mwh += battery_charge_mw * efficiency  # Charge with efficiency loss
            
        elif shortfall_mw > 0:
            # Can discharge: limited by discharge rate and current SOC
            max_discharge = min(
                shortfall_mw,  # Needed to meet demand
                discharge_rate_mw,  # Physical rate limit
                current_soc_mwh  # Available energy
            )
            battery_discharge_mw = max(0, max_discharge)
            current_soc_mwh -= battery_discharge_mw  # Discharge (no efficiency loss on discharge)
            unmet_demand_mw = max(0, shortfall_mw - battery_discharge_mw)
        
        # Enforce SOC bounds
        current_soc_mwh = np.clip(current_soc_mwh, min_soc_mwh, max_soc_mwh)
        
        result_rows.append({
            'date': date,
            'load_mw': load_mw,
            'renewable_total_mw': renewable_mw,
            'shortfall_mw': shortfall_mw,
            'surplus_mw': surplus_mw,
            'battery_charge_mw': battery_charge_mw,
            'battery_discharge_mw': battery_discharge_mw,
            'battery_soc_mwh': current_soc_mwh,
            'battery_soc_pct': (current_soc_mwh / capacity_mwh) * 100,
            'unmet_demand_mw': unmet_demand_mw,
            'net_shortfall_pct': (unmet_demand_mw / load_mw * 100) if load_mw > 0 else 0
        })
    
    return pd.DataFrame(result_rows)


def analyze_battery_impact(
    scenario_data: pd.DataFrame,
    battery_configs: dict,
    scenario_name: str
) -> dict:
    """
    Analyze battery storage impact across different capacity configurations.
    
    Args:
        scenario_data: Full scenario DataFrame for a single scenario
        battery_configs: Dict mapping config_name -> BatteryConfig
        scenario_name: Name of scenario ('worst', 'average', 'best')
    
    Returns:
        Dict with analysis results for the scenario
    """
    
    results = {
        'scenario': scenario_name,
        'configs': {}
    }
    
    for config_name, battery_config in battery_configs.items():
        dispatch_df = calculate_battery_dispatch(scenario_data, battery_config)
        
        # Calculate metrics
        total_days = len(dispatch_df)
        unmet_days = (dispatch_df['unmet_demand_mw'] > 0).sum()
        avg_charge_cycles = dispatch_df['battery_charge_mw'].sum() / (battery_config.capacity_gwh * 1000)
        avg_soc = dispatch_df['battery_soc_pct'].mean()
        max_soc_swing = dispatch_df['battery_soc_pct'].max() - dispatch_df['battery_soc_pct'].min()
        
        # Economic metrics
        capex = battery_config.capacity_gwh * 1000 * battery_config.capex_per_mwh
        annual_opex = capex * battery_config.annual_opex_pct / 100
        total_unmet_gwh = dispatch_df['unmet_demand_mw'].sum() / 1000 / 24  # Convert to daily average GWh
        
        # Shortfall reduction
        baseline_shortfall = scenario_data['shortfall_mw'].sum() / 1000 / 24
        shortfall_reduction_pct = ((baseline_shortfall - total_unmet_gwh) / baseline_shortfall * 100) if baseline_shortfall > 0 else 0
        
        config_result = {
            'battery_config': battery_config,
            'dispatch': dispatch_df,
            'metrics': {
                'capacity_gwh': battery_config.capacity_gwh,
                'total_days': total_days,
                'unmet_days': unmet_days,
                'coverage_pct': ((total_days - unmet_days) / total_days * 100),
                'avg_daily_charge_cycles': avg_charge_cycles / total_days,
                'avg_soc_pct': avg_soc,
                'max_soc_swing_pct': max_soc_swing,
                'baseline_shortfall_gwh': baseline_shortfall,
                'residual_shortfall_gwh': total_unmet_gwh,
                'shortfall_reduction_pct': shortfall_reduction_pct,
                'capex_million_usd': capex / 1_000_000,
                'annual_opex_million_usd': annual_opex / 1_000_000,
                'cost_per_mwh_stored': capex / (battery_config.capacity_gwh * 1000) if battery_config.capacity_gwh > 0 else 0,
            }
        }
        
        results['configs'][config_name] = config_result
    
    return results


def main():
    """Main execution: generate battery storage analysis for all scenarios."""
    
    # Load scenario data
    print("Loading scenario forecasts...")
    df = pd.read_csv('scenario_forecasts.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Define battery configurations to analyze
    battery_configs = {
        'Battery_5GWh': BatteryConfig(
            capacity_gwh=5.0,
            charge_rate_gw=1.0,
            discharge_rate_gw=1.0,
            round_trip_efficiency=0.87,
            min_soc_pct=20.0,
            max_soc_pct=100.0,
            capex_per_mwh=150,  # $/MWh (2024 market rates)
            annual_opex_pct=2.5
        ),
        'Battery_10GWh': BatteryConfig(
            capacity_gwh=10.0,
            charge_rate_gw=2.0,
            discharge_rate_gw=2.0,
            round_trip_efficiency=0.87,
            min_soc_pct=20.0,
            max_soc_pct=100.0,
            capex_per_mwh=150,
            annual_opex_pct=2.5
        ),
        'Battery_20GWh': BatteryConfig(
            capacity_gwh=20.0,
            charge_rate_gw=3.0,
            discharge_rate_gw=3.0,
            round_trip_efficiency=0.87,
            min_soc_pct=20.0,
            max_soc_pct=100.0,
            capex_per_mwh=150,
            annual_opex_pct=2.5
        ),
        'Battery_50GWh': BatteryConfig(
            capacity_gwh=50.0,
            charge_rate_gw=5.0,
            discharge_rate_gw=5.0,
            round_trip_efficiency=0.87,
            min_soc_pct=20.0,
            max_soc_pct=100.0,
            capex_per_mwh=150,
            annual_opex_pct=2.5
        ),
    }
    
    # Store results by scenario
    all_results = {}
    
    # Process each scenario
    for scenario in ['worst', 'average', 'best']:
        print(f"\nAnalyzing {scenario} scenario...")
        scenario_df = df[df['scenario'] == scenario].reset_index(drop=True)
        
        results = analyze_battery_impact(scenario_df, battery_configs, scenario)
        all_results[scenario] = results
        
        # Print summary
        print(f"  {scenario.upper()} SCENARIO - Battery Analysis Summary:")
        print(f"  {'Config':<15} {'Shortfall Reduction':<20} {'Days w/ Unmet Demand':<25} {'CAPEX (M USD)':<15}")
        print("  " + "-" * 75)
        
        for config_name, config_result in results['configs'].items():
            metrics = config_result['metrics']
            print(f"  {config_name:<15} {metrics['shortfall_reduction_pct']:>6.1f}% "
                  f"({metrics['baseline_shortfall_gwh']:.1f}->{metrics['residual_shortfall_gwh']:.1f} GWh) "
                  f"{metrics['unmet_days']:>5} days                "
                  f"${metrics['capex_million_usd']:>6.1f}M")
    
    # Generate comprehensive output CSV
    print("\nGenerating storage analysis output files...")
    
    # Create summary table with all battery configs
    summary_rows = []
    for scenario, results in all_results.items():
        for config_name, config_result in results['configs'].items():
            row = {
                'scenario': scenario,
                'battery_config': config_name,
            }
            row.update(config_result['metrics'])
            summary_rows.append(row)
    
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv('battery_storage_analysis.csv', index=False)
    print(f"  [OK] Saved battery_storage_analysis.csv ({len(summary_df)} rows)")
    
    # Save dispatch details for each scenario (for dashboard use)
    for scenario, results in all_results.items():
        for config_name, config_result in results['configs'].items():
            dispatch = config_result['dispatch']
            filename = f"dispatch_{scenario}_{config_name.lower().replace('_', '')}.csv"
            dispatch.to_csv(filename, index=False)
    print(f"  [OK] Saved dispatch files for all scenarios/configs ({len(all_results) * len(battery_configs)} files)")
    
    # Create optimization recommendation CSV
    print("\nGenerating optimization recommendations...")
    recommendations = []
    for scenario, results in all_results.items():
        # Find optimal battery size for 90% shortfall reduction
        target_reduction = 90.0
        configs = results['configs']
        best_config = None
        best_cost_effectiveness = float('inf')
        
        for config_name, config_result in configs.items():
            reduction = config_result['metrics']['shortfall_reduction_pct']
            capex = config_result['metrics']['capex_million_usd']
            
            if reduction >= target_reduction:
                cost_per_percent = capex / (reduction + 1)  # Avoid division by zero
                if cost_per_percent < best_cost_effectiveness:
                    best_config = config_name
                    best_cost_effectiveness = cost_per_percent
        
        if best_config:
            rec_metrics = results['configs'][best_config]['metrics']
            recommendations.append({
                'scenario': scenario,
                'recommended_battery_config': best_config,
                'battery_capacity_gwh': rec_metrics['capacity_gwh'],
                'shortfall_reduction_pct': rec_metrics['shortfall_reduction_pct'],
                'residual_shortfall_gwh': rec_metrics['residual_shortfall_gwh'],
                'annual_opex_million_usd': rec_metrics['annual_opex_million_usd'],
                'payback_assumption_years': rec_metrics['capex_million_usd'] / rec_metrics['annual_opex_million_usd'] if rec_metrics['annual_opex_million_usd'] > 0 else 0,
                'note': f"Achieves {rec_metrics['shortfall_reduction_pct']:.1f}% shortfall reduction at optimal cost-effectiveness"
            })
    
    rec_df = pd.DataFrame(recommendations)
    rec_df.to_csv('battery_recommendations.csv', index=False)
    print(f"  [OK] Saved battery_recommendations.csv ({len(rec_df)} rows)")
    
    print("\n[COMPLETE] Battery storage analysis finished successfully!")
    print("\nKey Outputs:")
    print("  - battery_storage_analysis.csv: Comprehensive metrics for all configs/scenarios")
    print("  - battery_recommendations.csv: Optimal battery sizing by scenario")
    print("  - dispatch_*.csv: Detailed hourly dispatch for each config/scenario")


if __name__ == '__main__':
    main()
