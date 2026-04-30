"""
Renewable Energy Forecasting with Scenario Analysis
Phase 2: Create Engaging Visualizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 80)
print("PHASE 2: CREATING ENGAGING SCENARIO VISUALIZATIONS")
print("=" * 80)

# ==============================================================================
# LOAD DATA
# ==============================================================================
print("\n[1/6] Loading scenario data...")
project_root = Path(__file__).resolve().parents[1]
processed_dir = project_root / 'data' / 'processed'
visualizations_dir = project_root / 'visualizations'
visualizations_dir.mkdir(parents=True, exist_ok=True)

scenarios_df = pd.read_csv(processed_dir / 'scenario_forecasts.csv')
daily_df = pd.read_csv(processed_dir / 'daily_data.csv')
scenarios_df['date'] = pd.to_datetime(scenarios_df['date'])
daily_df['date'] = pd.to_datetime(daily_df['date'])

print(f"  [OK] Loaded {len(scenarios_df)} scenario records across 3 scenarios")

# Color scheme (consistent with notebook theme)
colors = {
    'worst': '#e08adf',      # light orchid
    'average': '#c06bb7',    # pink-purple
    'best': '#9b59b6',       # purple
    'demand': '#7a4d7e',     # dark purple
    'wind': '#d16ba5',       # rosy pink
    'solar': '#7b68ee',      # soft violet
}

background_color = '#faf6fb'
edge_color = '#7a4d7e'

# ==============================================================================
# VISUALIZATION 1: STACKED AREA CHART (3 scenarios side by side)
# ==============================================================================
print("\n[2/6] Creating stacked area charts...")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.patch.set_facecolor('white')

scenarios_list = ['worst', 'average', 'best']
scenario_titles = {
    'worst': 'Worst Case: Low Renewable Output',
    'average': 'Average Case: Baseline Forecast',
    'best': 'Best Case: High Renewable Output'
}

for idx, (ax, scenario) in enumerate(zip(axes, scenarios_list)):
    data = scenarios_df[scenarios_df['scenario'] == scenario].sort_values('date')
    
    ax.fill_between(data['date'], 0, data['wind_generation_mw'], 
                     label='Wind', color=colors['wind'], alpha=0.7)
    ax.fill_between(data['date'], data['wind_generation_mw'], 
                     data['renewable_total_mw'], 
                     label='Solar', color=colors['solar'], alpha=0.7)
    ax.plot(data['date'], data['load_mw'], linewidth=3, label='Demand',
            color=colors['demand'], linestyle='--')
    
    ax.set_facecolor(background_color)
    ax.set_title(scenario_titles[scenario], fontsize=13, fontweight='bold',
                color=edge_color)
    ax.set_xlabel('Date', fontsize=11, color=edge_color)
    ax.set_ylabel('Power (MW)', fontsize=11, color=edge_color)
    ax.grid(True, alpha=0.3, color=edge_color)
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
    ax.tick_params(colors=edge_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(edge_color)

plt.tight_layout()
plt.savefig(visualizations_dir / '01_stacked_area_scenarios.png', dpi=300, bbox_inches='tight')
print(f"  [OK] Saved: {visualizations_dir / '01_stacked_area_scenarios.png'}")
plt.close()

# ==============================================================================
# VISUALIZATION 2: LINE CHART WITH CONFIDENCE BANDS
# ==============================================================================
print("\n[3/6] Creating line chart with confidence bands...")

fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor('white')
ax.set_facecolor(background_color)

# Plot renewable generation for each scenario
for scenario in ['worst', 'average', 'best']:
    data = scenarios_df[scenarios_df['scenario'] == scenario].sort_values('date')
    ax.plot(data['date'], data['renewable_total_mw'], linewidth=2.5,
            label=scenario.capitalize(), color=colors[scenario], alpha=0.8)

# Plot demand as reference
demand_data = scenarios_df[scenarios_df['scenario'] == 'average'].sort_values('date')
ax.plot(demand_data['date'], demand_data['load_mw'], linewidth=3,
        label='Demand', color=colors['demand'], linestyle='--', alpha=0.9)

# Add shaded region for uncertainty between worst and best
worst_data = scenarios_df[scenarios_df['scenario'] == 'worst'].sort_values('date')
best_data = scenarios_df[scenarios_df['scenario'] == 'best'].sort_values('date')
ax.fill_between(demand_data['date'], worst_data['renewable_total_mw'], 
                best_data['renewable_total_mw'], alpha=0.15, color=colors['average'])

ax.set_xlabel('Date', fontsize=12, fontweight='bold', color=edge_color)
ax.set_ylabel('Power Generation / Demand (MW)', fontsize=12, fontweight='bold', color=edge_color)
ax.set_title('Renewable Energy Forecasts: Scenario Comparison\n(Shaded area shows forecast uncertainty)', 
             fontsize=14, fontweight='bold', color=edge_color)
ax.grid(True, alpha=0.3, color=edge_color)
ax.legend(loc='upper left', frameon=False, fontsize=11, title='Scenario',
          title_fontsize=12)
ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
ax.tick_params(colors=edge_color)
for spine in ax.spines.values():
    spine.set_edgecolor(edge_color)
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.savefig(visualizations_dir / '02_line_chart_uncertainty_band.png', dpi=300, bbox_inches='tight')
print(f"  [OK] Saved: {visualizations_dir / '02_line_chart_uncertainty_band.png'}")
plt.close()

# ==============================================================================
# VISUALIZATION 3: SMALL MULTIPLES (3 panels with shortfall highlighting)
# ==============================================================================
print("\n[4/6] Creating small multiples comparison...")

fig, axes = plt.subplots(3, 1, figsize=(14, 10))
fig.patch.set_facecolor('white')

for idx, scenario in enumerate(scenarios_list):
    ax = axes[idx]
    data = scenarios_df[scenarios_df['scenario'] == scenario].sort_values('date')
    
    # Plot renewable generation
    ax.bar(data['date'], data['renewable_total_mw'], width=1, label='Renewable Generation',
           color=colors[scenario], alpha=0.7)
    
    # Plot demand line
    ax.plot(data['date'], data['load_mw'], linewidth=2.5, label='Demand',
            color=colors['demand'], zorder=5)
    
    # Shade shortfall areas (where renewables < demand)
    shortfall_mask = data['renewable_total_mw'] < data['load_mw']
    ax.fill_between(data.loc[shortfall_mask, 'date'], 
                     data.loc[shortfall_mask, 'renewable_total_mw'],
                     data.loc[shortfall_mask, 'load_mw'],
                     alpha=0.2, color='red', label='Shortfall')
    
    ax.set_facecolor(background_color)
    ax.set_title(scenario_titles[scenario], fontsize=12, fontweight='bold',
                color=edge_color, loc='left')
    ax.set_ylabel('Power (MW)', fontsize=10, color=edge_color)
    ax.grid(True, alpha=0.3, axis='y', color=edge_color)
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
    ax.tick_params(colors=edge_color)
    
    for spine in ax.spines.values():
        spine.set_edgecolor(edge_color)

axes[-1].set_xlabel('Date', fontsize=11, fontweight='bold', color=edge_color)
plt.tight_layout()
plt.savefig(visualizations_dir / '03_small_multiples_shortfall.png', dpi=300, bbox_inches='tight')
print(f"  [OK] Saved: {visualizations_dir / '03_small_multiples_shortfall.png'}")
plt.close()

# ==============================================================================
# VISUALIZATION 4: SHORTFALL SEVERITY HEATMAP
# ==============================================================================
print("\n[5/6] Creating shortfall severity heatmap...")

# Create month-scenario grid
scenarios_df['year_month'] = scenarios_df['date'].dt.to_period('M')
scenarios_df['month'] = scenarios_df['date'].dt.month
scenarios_df['year'] = scenarios_df['date'].dt.year

# Calculate average shortfall by month and scenario
heatmap_data = scenarios_df.pivot_table(
    values='shortfall_mw', 
    index='scenario', 
    columns='month', 
    aggfunc='mean'
)

# Reorder rows
heatmap_data = heatmap_data.reindex(['worst', 'average', 'best'])

fig, ax = plt.subplots(figsize=(12, 4))
fig.patch.set_facecolor('white')

sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='RdYlGn_r',
            cbar_kws={'label': 'Average Shortfall (MW)'}, ax=ax,
            linewidths=0.5, linecolor=edge_color)

ax.set_title('Energy Shortfall Severity by Scenario and Month\n(Red = larger shortfalls)', 
             fontsize=13, fontweight='bold', color=edge_color, pad=20)
ax.set_xlabel('Month', fontsize=11, fontweight='bold', color=edge_color)
ax.set_ylabel('Scenario', fontsize=11, fontweight='bold', color=edge_color)
ax.set_yticklabels(['Worst Case', 'Average Case', 'Best Case'], rotation=0)
month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ax.set_xticklabels(month_labels, rotation=0)
ax.tick_params(colors=edge_color)

plt.tight_layout()
plt.savefig(visualizations_dir / '04_shortfall_heatmap.png', dpi=300, bbox_inches='tight')
print(f"  [OK] Saved: {visualizations_dir / '04_shortfall_heatmap.png'}")
plt.close()

# ==============================================================================
# VISUALIZATION 5: SCENARIO SUMMARY COMPARISON TABLE
# ==============================================================================
print("\n[6/6] Creating scenario comparison summary...")

# Calculate metrics for each scenario
metrics = []
for scenario in ['worst', 'average', 'best']:
    data = scenarios_df[scenarios_df['scenario'] == scenario]
    metrics.append({
        'Scenario': scenario.capitalize(),
        'Avg Wind (MW)': f"{data['wind_generation_mw'].mean():,.0f}",
        'Avg Solar (MW)': f"{data['solar_generation_mw'].mean():,.0f}",
        'Avg Renewable (MW)': f"{data['renewable_total_mw'].mean():,.0f}",
        'Avg Demand (MW)': f"{data['load_mw'].mean():,.0f}",
        'Coverage %': f"{(data['renewable_total_mw'].sum() / data['load_mw'].sum() * 100):.1f}%",
        'Avg Shortfall (MW)': f"{data['shortfall_mw'].mean():,.0f}",
        'Max Shortfall (MW)': f"{data['shortfall_mw'].max():,.0f}",
        'Days w/ Shortfall': f"{(data['shortfall_mw'] > 0).sum()}/{len(data)}",
    })

summary_df = pd.DataFrame(metrics)

# Create figure with table
fig, ax = plt.subplots(figsize=(16, 3.5))
fig.patch.set_facecolor('white')
ax.axis('tight')
ax.axis('off')

# Create table
table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns,
                cellLoc='center', loc='center',
                colColours=['#d9b3df']*len(summary_df.columns),
                cellColours=[['#faf6fb']*len(summary_df.columns)]*len(summary_df))

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Style the header
for i in range(len(summary_df.columns)):
    table[(0, i)].set_facecolor('#7a4d7e')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Style the rows with scenario colors
scenario_colors_map = {
    0: '#e08adf',  # worst (light orchid)
    1: '#c06bb7',  # average (pink-purple)
    2: '#9b59b6',  # best (purple)
}

for i in range(len(summary_df)):
    table[(i+1, 0)].set_facecolor(scenario_colors_map[i])
    table[(i+1, 0)].set_text_props(weight='bold', color='white')

plt.title('Scenario Comparison: Key Metrics', 
         fontsize=14, fontweight='bold', color='#7a4d7e', pad=20)
plt.savefig(visualizations_dir / '05_scenario_summary_table.png', dpi=300, bbox_inches='tight')
print(f"  [OK] Saved: {visualizations_dir / '05_scenario_summary_table.png'}")
plt.close()

# Save summary table as CSV too
summary_df.to_csv(visualizations_dir / 'scenario_summary_table.csv', index=False)
print(f"  [OK] Saved: {visualizations_dir / 'scenario_summary_table.csv'}")

# ==============================================================================
# VISUALIZATION 6: RENEWABLE vs DEMAND COMPARISON DASHBOARD
# ==============================================================================
print("\n     Creating dashboard comparison...")

fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('white')
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Panel 1-3: Renewable vs Demand for each scenario
for idx, scenario in enumerate(scenarios_list):
    ax = fig.add_subplot(gs[idx, :])
    data = scenarios_df[scenarios_df['scenario'] == scenario].sort_values('date')
    
    # Calculate monthly averages for cleaner visualization
    monthly = data.set_index('date').resample('M').agg({
        'wind_generation_mw': 'mean',
        'solar_generation_mw': 'mean',
        'load_mw': 'mean',
        'shortfall_mw': 'mean'
    }).reset_index()
    
    # Add renewable total
    monthly['renewable_total_mw'] = monthly['wind_generation_mw'] + monthly['solar_generation_mw']
    
    x = np.arange(len(monthly))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, monthly['renewable_total_mw'], width,
                   label='Renewable Total', color=colors[scenario], alpha=0.8)
    bars2 = ax.bar(x + width/2, monthly['load_mw'], width,
                   label='Demand', color=colors['demand'], alpha=0.8)
    
    ax.set_facecolor(background_color)
    ax.set_title(f"{scenario.upper()}: Monthly Renewable Generation vs Demand",
                fontsize=11, fontweight='bold', color=edge_color, loc='left')
    ax.set_ylabel('Power (MW)', fontsize=10, color=edge_color)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.grid(True, alpha=0.3, axis='y', color=edge_color)
    ax.tick_params(colors=edge_color)
    
    for spine in ax.spines.values():
        spine.set_edgecolor(edge_color)
    
    # Set x labels (every 3 months)
    ax.set_xticks(x[::3])
    ax.set_xticklabels([d.strftime('%b %Y') for d in monthly['date'].iloc[::3]], 
                       rotation=45, ha='right', fontsize=9)

plt.suptitle('Renewable Energy Forecasting: 3-Scenario Analysis\n' + 
             'Comparing Solar + Wind Generation Against Electricity Demand',
             fontsize=15, fontweight='bold', color=edge_color, y=0.995)

plt.savefig(visualizations_dir / '06_dashboard_comparison.png', dpi=300, bbox_inches='tight')
print(f"  [OK] Saved: {visualizations_dir / '06_dashboard_comparison.png'}")
plt.close()

print("\n" + "=" * 80)
print("[COMPLETE] PHASE 2: All visualizations created")
print("=" * 80)
print("\nGenerated visualizations:")
print("  1. 01_stacked_area_scenarios.png - Stacked area charts (3 scenarios)")
print("  2. 02_line_chart_uncertainty_band.png - Line chart with confidence band")
print("  3. 03_small_multiples_shortfall.png - 3-panel shortfall comparison")
print("  4. 04_shortfall_heatmap.png - Monthly shortfall severity heatmap")
print("  5. 05_scenario_summary_table.png - Summary metrics table")
print("  6. 06_dashboard_comparison.png - Dashboard with monthly trends")
print(f"\nAll files saved to: {visualizations_dir}")
