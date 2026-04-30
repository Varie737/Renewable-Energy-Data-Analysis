"""
Interactive Dashboard for Renewable Energy Scenario Analysis

Multi-page Dash application for exploring renewable energy scenarios,
battery storage optimization, and comparative metrics.

Run with: python dashboard.py
Then navigate to http://localhost:8050
"""

import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, module='numpy')

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


# Load data
print("Loading data...")
project_root = Path(__file__).resolve().parents[1]
processed_dir = project_root / 'data' / 'processed'
scenarios_df = pd.read_csv(processed_dir / 'scenario_forecasts.csv')
scenarios_df['date'] = pd.to_datetime(scenarios_df['date'])
battery_analysis_df = pd.read_csv(processed_dir / 'battery_storage_analysis.csv')

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

# Color scheme (matching existing visualizations)
COLOR_WORST = '#8c564b'      # Brown
COLOR_AVERAGE = '#17becf'    # Cyan
COLOR_BEST = '#9467bd'       # Purple
COLOR_DEMAND = '#d62728'     # Red
COLOR_BG = '#faf6fb'         # Light background

SCENARIO_COLORS = {
    'worst': COLOR_WORST,
    'average': COLOR_AVERAGE,
    'best': COLOR_BEST
}


# ============================================================================
# PAGE 1: OVERVIEW DASHBOARD
# ============================================================================

def create_overview_page():
    """Overview page with KPI cards and scenario selector."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Renewable Energy Scenario Analysis Dashboard", 
                       className="text-center mt-4 mb-2")
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.P("Interactive exploration of solar and wind generation forecasts across three scenarios",
                      className="text-center text-muted mb-4")
            ]),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Label("Select Scenario:", className="fw-bold"),
                dcc.RadioItems(
                    id='scenario-selector',
                    options=[
                        {'label': '  Worst Case', 'value': 'worst'},
                        {'label': '  Average Case', 'value': 'average'},
                        {'label': '  Best Case', 'value': 'best'},
                    ],
                    value='average',
                    inline=True,
                    className="mb-4"
                )
            ], width=12),
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Average Coverage", className="card-title text-muted"),
                        html.H3(id='kpi-coverage', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Days with Shortfall", className="card-title text-muted"),
                        html.H3(id='kpi-shortfall-days', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Avg Daily Shortfall", className="card-title text-muted"),
                        html.H3(id='kpi-avg-shortfall', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Peak Shortfall", className="card-title text-muted"),
                        html.H3(id='kpi-peak-shortfall', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
        ], className="mb-4"),
        
        html.Hr(),
        
        dbc.Row([
            dbc.Col([
                html.H5("Scenario Metrics Comparison", className="mb-3"),
                dcc.Loading(
                    id="loading-metrics",
                    children=[
                        dcc.Graph(id='comparison-metrics-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
    ], fluid=True, style={'backgroundColor': COLOR_BG, 'minHeight': '100vh', 'padding': '20px'})


# ============================================================================
# PAGE 2: SCENARIO EXPLORER
# ============================================================================

def create_scenario_page():
    """Interactive time-series explorer for scenarios."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Scenario Time Series Explorer", className="mt-4 mb-4")
            ]),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Label("Select Scenario:", className="fw-bold"),
                dcc.Dropdown(
                    id='timeseries-scenario-dropdown',
                    options=[
                        {'label': 'Worst Case', 'value': 'worst'},
                        {'label': 'Average Case', 'value': 'average'},
                        {'label': 'Best Case', 'value': 'best'},
                    ],
                    value='average',
                    clearable=False,
                ),
            ], width=12, md=6),
            dbc.Col([
                html.Label("Date Range:", className="fw-bold"),
                dcc.DatePickerRange(
                    id='timeseries-date-range',
                    start_date=scenarios_df['date'].min(),
                    end_date=scenarios_df['date'].min() + timedelta(days=365),
                    display_format='YYYY-MM-DD',
                )
            ], width=12, md=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("Show/Hide Series:", className="fw-bold"),
                    dcc.Checklist(
                        id='timeseries-series-toggle',
                        options=[
                            {'label': ' Wind Generation', 'value': 'wind'},
                            {'label': ' Solar Generation', 'value': 'solar'},
                            {'label': ' Electricity Demand', 'value': 'demand'},
                        ],
                        value=['wind', 'solar', 'demand'],
                        inline=True,
                    )
                ])
            ], width=12),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="loading-timeseries",
                    children=[
                        dcc.Graph(id='timeseries-chart', style={'height': '600px'})
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Shortfall Analysis", className="mb-3"),
                dcc.Loading(
                    id="loading-shortfall",
                    children=[
                        dcc.Graph(id='shortfall-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ]),
        
    ], fluid=True, style={'backgroundColor': COLOR_BG, 'minHeight': '100vh', 'padding': '20px'})


# ============================================================================
# PAGE 3: BATTERY STORAGE ANALYSIS
# ============================================================================

def create_battery_page():
    """Battery storage optimization and analysis."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Battery Storage Optimization", className="mt-4 mb-4")
            ]),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Label("Select Scenario:", className="fw-bold"),
                dcc.Dropdown(
                    id='battery-scenario-dropdown',
                    options=[
                        {'label': 'Worst Case', 'value': 'worst'},
                        {'label': 'Average Case', 'value': 'average'},
                        {'label': 'Best Case', 'value': 'best'},
                    ],
                    value='average',
                    clearable=False,
                ),
            ], width=12, md=6),
            dbc.Col([
                html.Label("Select Battery Configuration:", className="fw-bold"),
                dcc.Dropdown(
                    id='battery-config-dropdown',
                    options=[
                        {'label': '5 GWh Battery', 'value': 'Battery_5GWh'},
                        {'label': '10 GWh Battery', 'value': 'Battery_10GWh'},
                        {'label': '20 GWh Battery', 'value': 'Battery_20GWh'},
                        {'label': '50 GWh Battery', 'value': 'Battery_50GWh'},
                    ],
                    value='Battery_10GWh',
                    clearable=False,
                ),
            ], width=12, md=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Shortfall Reduction", className="card-title text-muted"),
                        html.H3(id='battery-kpi-reduction', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Residual Shortfall", className="card-title text-muted"),
                        html.H3(id='battery-kpi-residual', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Unmet Demand Days", className="card-title text-muted"),
                        html.H3(id='battery-kpi-unmet-days', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("CAPEX Cost", className="card-title text-muted"),
                        html.H3(id='battery-kpi-capex', children="--"),
                    ])
                ], className="text-center")
            ], width=6, lg=3),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Battery State of Charge Over Time", className="mb-3"),
                dcc.Loading(
                    id="loading-battery-soc",
                    children=[
                        dcc.Graph(id='battery-soc-chart', style={'height': '500px'})
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Daily Charge/Discharge Patterns", className="mb-3"),
                dcc.Loading(
                    id="loading-battery-dispatch",
                    children=[
                        dcc.Graph(id='battery-dispatch-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Shortfall Reduction Across Battery Sizes", className="mb-3"),
                dcc.Loading(
                    id="loading-battery-comparison",
                    children=[
                        dcc.Graph(id='battery-comparison-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ]),
        
    ], fluid=True, style={'backgroundColor': COLOR_BG, 'minHeight': '100vh', 'padding': '20px'})


# ============================================================================
# PAGE 4: COMPREHENSIVE METRICS
# ============================================================================

def create_metrics_page():
    """Side-by-side scenario metrics and comparison."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Comprehensive Metrics Comparison", className="mt-4 mb-4")
            ]),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H5("Key Metrics by Scenario", className="mb-3"),
                dcc.Loading(
                    id="loading-metrics-table",
                    children=[
                        html.Div(id='metrics-table-container')
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Seasonal Patterns", className="mb-3"),
                dcc.Loading(
                    id="loading-seasonal",
                    children=[
                        dcc.Graph(id='seasonal-patterns-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Coverage Distribution", className="mb-3"),
                dcc.Loading(
                    id="loading-distribution",
                    children=[
                        dcc.Graph(id='coverage-distribution-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Battery Storage Economics", className="mb-3"),
                dcc.Loading(
                    id="loading-battery-economics",
                    children=[
                        dcc.Graph(id='battery-economics-chart', style={'height': '400px'})
                    ],
                    type="default",
                ),
            ]),
        ]),
        
    ], fluid=True, style={'backgroundColor': COLOR_BG, 'minHeight': '100vh', 'padding': '20px'})


# ============================================================================
# PAGE LAYOUT
# ============================================================================

app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    
    # Navigation Bar
    dbc.Navbar([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H4("[RE] Energy Dashboard", className="mb-0 text-white")
                ], width="auto"),
                dbc.Col([
                    dcc.Link(
                        "Overview", href="/",
                        style={'textDecoration': 'none', 'color': 'white'}
                    ),
                    dcc.Link(
                        "Time Series", href="/scenarios",
                        style={'textDecoration': 'none', 'color': 'white'}
                    ),
                    dcc.Link(
                        "Storage", href="/battery",
                        style={'textDecoration': 'none', 'color': 'white'}
                    ),
                    dcc.Link(
                        "Metrics", href="/metrics",
                        style={'textDecoration': 'none', 'color': 'white'}
                    ),
                ], className="d-flex gap-3 ms-auto"),
            ], align="center"),
        ], fluid=True)
    ], dark=True, color="dark", sticky="top", className="mb-4"),
    
    # Page Content
    html.Div(id='page-content'),
    
], fluid=True, style={'padding': '0px'})


# ============================================================================
# CALLBACKS
# ============================================================================

@callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    """Route to appropriate page."""
    if pathname == '/scenarios':
        return create_scenario_page()
    elif pathname == '/battery':
        return create_battery_page()
    elif pathname == '/metrics':
        return create_metrics_page()
    else:
        return create_overview_page()


# OVERVIEW PAGE CALLBACKS

@callback(
    [Output('kpi-coverage', 'children'),
     Output('kpi-shortfall-days', 'children'),
     Output('kpi-avg-shortfall', 'children'),
     Output('kpi-peak-shortfall', 'children')],
    [Input('scenario-selector', 'value')]
)
def update_overview_kpis(scenario):
    """Update overview page KPIs based on selected scenario."""
    df = scenarios_df[scenarios_df['scenario'] == scenario]
    
    coverage = df['coverage_pct'].mean()
    shortfall_days = (df['shortfall_mw'] > 0).sum()
    avg_shortfall = df['shortfall_mw'].mean()
    peak_shortfall = df['shortfall_mw'].max()
    
    return (
        f"{coverage:.1f}%",
        f"{shortfall_days} days",
        f"{avg_shortfall:,.0f} MW",
        f"{peak_shortfall:,.0f} MW"
    )


@callback(
    Output('comparison-metrics-chart', 'figure'),
    [Input('scenario-selector', 'value')]
)
def update_comparison_chart(selected_scenario):
    """Create scenario comparison bar chart."""
    metrics = []
    for scenario in ['worst', 'average', 'best']:
        df = scenarios_df[scenarios_df['scenario'] == scenario]
        metrics.append({
            'Scenario': scenario.capitalize(),
            'Avg Coverage (%)': df['coverage_pct'].mean(),
            'Avg Shortfall (GW)': df['shortfall_mw'].mean() / 1000,
            'Max Shortfall (GW)': df['shortfall_mw'].max() / 1000,
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=metrics_df['Scenario'], y=metrics_df['Avg Coverage (%)'], 
                        name='Avg Coverage (%)', marker_color=COLOR_AVERAGE))
    fig.add_trace(go.Bar(x=metrics_df['Scenario'], y=metrics_df['Avg Shortfall (GW)'], 
                        name='Avg Shortfall (GW)', marker_color=COLOR_DEMAND, yaxis='y2'))
    
    fig.update_layout(
        title="Scenario Metrics Overview",
        xaxis_title="Scenario",
        yaxis_title="Coverage (%)",
        yaxis2=dict(title="Shortfall (GW)", overlaying='y', side='right'),
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


# TIME SERIES PAGE CALLBACKS

@callback(
    Output('timeseries-chart', 'figure'),
    [Input('timeseries-scenario-dropdown', 'value'),
     Input('timeseries-date-range', 'start_date'),
     Input('timeseries-date-range', 'end_date'),
     Input('timeseries-series-toggle', 'value')]
)
def update_timeseries(scenario, start_date, end_date, selected_series):
    """Update time series chart."""
    df = scenarios_df[(scenarios_df['scenario'] == scenario) &
                      (scenarios_df['date'] >= start_date) &
                      (scenarios_df['date'] <= end_date)].copy()
    
    fig = go.Figure()
    
    if 'wind' in selected_series:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['wind_generation_mw'],
            name='Wind Generation', fill='tozeroy',
            line=dict(color=COLOR_BEST, width=2)
        ))
    
    if 'solar' in selected_series:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['solar_generation_mw'],
            name='Solar Generation', fill='tozeroy',
            line=dict(color=COLOR_AVERAGE, width=2)
        ))
    
    if 'demand' in selected_series:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['load_mw'],
            name='Electricity Demand', fill=None,
            line=dict(color=COLOR_DEMAND, width=3, dash='dash')
        ))
    
    fig.update_layout(
        title=f"Time Series - {scenario.upper()} Scenario",
        xaxis_title="Date",
        yaxis_title="Power (MW)",
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


@callback(
    Output('shortfall-chart', 'figure'),
    [Input('timeseries-scenario-dropdown', 'value'),
     Input('timeseries-date-range', 'start_date'),
     Input('timeseries-date-range', 'end_date')]
)
def update_shortfall_chart(scenario, start_date, end_date):
    """Update shortfall chart."""
    df = scenarios_df[(scenarios_df['scenario'] == scenario) &
                      (scenarios_df['date'] >= start_date) &
                      (scenarios_df['date'] <= end_date)].copy()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['date'], y=df['shortfall_mw'],
        name='Unmet Demand', marker_color=COLOR_DEMAND,
        hovertemplate='%{x}<br>Shortfall: %{y:,.0f} MW'
    ))
    
    fig.update_layout(
        title=f"Daily Shortfall - {scenario.upper()} Scenario",
        xaxis_title="Date",
        yaxis_title="Shortfall (MW)",
        hovermode='x',
        template='plotly_white',
        height=400
    )
    
    return fig


# BATTERY PAGE CALLBACKS

@callback(
    [Output('battery-kpi-reduction', 'children'),
     Output('battery-kpi-residual', 'children'),
     Output('battery-kpi-unmet-days', 'children'),
     Output('battery-kpi-capex', 'children')],
    [Input('battery-scenario-dropdown', 'value'),
     Input('battery-config-dropdown', 'value')]
)
def update_battery_kpis(scenario, battery_config):
    """Update battery storage KPIs."""
    row = battery_analysis_df[
        (battery_analysis_df['scenario'] == scenario) &
        (battery_analysis_df['battery_config'] == battery_config)
    ]
    
    if row.empty:
        return "--", "--", "--", "--"
    
    row = row.iloc[0]
    
    return (
        f"{row['shortfall_reduction_pct']:.1f}%",
        f"{row['residual_shortfall_gwh']:.1f} GWh",
        f"{row['unmet_days']:.0f} days",
        f"${row['capex_million_usd']:.1f}M"
    )


@callback(
    Output('battery-soc-chart', 'figure'),
    [Input('battery-scenario-dropdown', 'value'),
     Input('battery-config-dropdown', 'value')]
)
def update_battery_soc_chart(scenario, battery_config):
    """Plot battery state of charge."""
    filename = processed_dir / f"dispatch_{scenario}_{battery_config.lower().replace('_', '')}.csv"
    try:
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['battery_soc_pct'],
            fill='tozeroy', name='State of Charge',
            line=dict(color=COLOR_BEST, width=2)
        ))
        
        fig.update_layout(
            title=f"Battery State of Charge - {scenario.upper()} | {battery_config.replace('_', ' ')}",
            xaxis_title="Date",
            yaxis_title="SOC (%)",
            hovermode='x',
            template='plotly_white',
            height=500,
            yaxis=dict(range=[0, 100])
        )
        
        return fig
    except:
        return go.Figure().add_annotation(text="Data not available")


@callback(
    Output('battery-dispatch-chart', 'figure'),
    [Input('battery-scenario-dropdown', 'value'),
     Input('battery-config-dropdown', 'value')]
)
def update_battery_dispatch_chart(scenario, battery_config):
    """Plot battery charge/discharge."""
    filename = processed_dir / f"dispatch_{scenario}_{battery_config.lower().replace('_', '')}.csv"
    try:
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        # Limit to first 365 days for clarity
        df = df.head(365)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['date'], y=df['battery_charge_mw'],
            name='Charging', marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=df['date'], y=-df['battery_discharge_mw'],
            name='Discharging', marker_color='orange'
        ))
        
        fig.update_layout(
            title=f"Battery Dispatch (First Year) - {scenario.upper()}",
            xaxis_title="Date",
            yaxis_title="Power (MW)",
            barmode='overlay',
            hovermode='x',
            template='plotly_white',
            height=400
        )
        
        return fig
    except:
        return go.Figure().add_annotation(text="Data not available")


@callback(
    Output('battery-comparison-chart', 'figure'),
    [Input('battery-scenario-dropdown', 'value')]
)
def update_battery_comparison(scenario):
    """Compare shortfall reduction across battery sizes."""
    data = battery_analysis_df[battery_analysis_df['scenario'] == scenario]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['capacity_gwh'], y=data['shortfall_reduction_pct'],
        mode='lines+markers', name='Shortfall Reduction',
        line=dict(color=SCENARIO_COLORS.get(scenario, COLOR_AVERAGE), width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title=f"Shortfall Reduction vs Battery Capacity - {scenario.upper()}",
        xaxis_title="Battery Capacity (GWh)",
        yaxis_title="Shortfall Reduction (%)",
        hovermode='x',
        template='plotly_white',
        height=400
    )
    
    return fig


# METRICS PAGE CALLBACKS

@callback(
    Output('metrics-table-container', 'children'),
    [Input('url', 'pathname')]
)
def update_metrics_table(pathname):
    """Create comprehensive metrics table."""
    metrics = []
    for scenario in ['worst', 'average', 'best']:
        df = scenarios_df[scenarios_df['scenario'] == scenario]
        metrics.append({
            'Scenario': scenario.capitalize(),
            'Avg Coverage': f"{df['coverage_pct'].mean():.1f}%",
            'Avg Shortfall': f"{df['shortfall_mw'].mean():,.0f} MW",
            'Max Shortfall': f"{df['shortfall_mw'].max():,.0f} MW",
            'Days w/ Shortfall': f"{(df['shortfall_mw'] > 0).sum()}/2101",
            'Avg Surplus': f"{df['surplus_mw'].mean():,.0f} MW"
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    table = dbc.Table.from_dataframe(
        metrics_df, striped=True, bordered=True, hover=True, responsive=True, className="mb-4"
    )
    
    return table


@callback(
    Output('seasonal-patterns-chart', 'figure'),
    [Input('url', 'pathname')]
)
def update_seasonal_patterns(pathname):
    """Plot seasonal patterns by scenario."""
    scenarios_df['month'] = pd.to_datetime(scenarios_df['date']).dt.month
    
    seasonal = scenarios_df.groupby(['scenario', 'month'])['shortfall_mw'].mean().reset_index()
    
    fig = go.Figure()
    for scenario in ['worst', 'average', 'best']:
        data = seasonal[seasonal['scenario'] == scenario]
        fig.add_trace(go.Scatter(
            x=data['month'], y=data['shortfall_mw'],
            mode='lines+markers', name=scenario.capitalize(),
            line=dict(color=SCENARIO_COLORS.get(scenario, COLOR_AVERAGE), width=3),
            marker=dict(size=8)
        ))
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    fig.update_layout(
        title="Seasonal Shortfall Patterns",
        xaxis_title="Month",
        xaxis=dict(tickvals=list(range(1, 13)), ticktext=month_names),
        yaxis_title="Average Shortfall (MW)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


@callback(
    Output('coverage-distribution-chart', 'figure'),
    [Input('url', 'pathname')]
)
def update_coverage_distribution(pathname):
    """Plot coverage distribution."""
    fig = go.Figure()
    
    for scenario in ['worst', 'average', 'best']:
        df = scenarios_df[scenarios_df['scenario'] == scenario]
        fig.add_trace(go.Histogram(
            x=df['coverage_pct'], name=scenario.capitalize(),
            marker_color=SCENARIO_COLORS.get(scenario, COLOR_AVERAGE),
            opacity=0.7, nbinsx=50
        ))
    
    fig.update_layout(
        title="Coverage Distribution Across Scenarios",
        xaxis_title="Coverage (%)",
        yaxis_title="Days",
        barmode='overlay',
        template='plotly_white',
        height=400,
        hovermode='x'
    )
    
    return fig


@callback(
    Output('battery-economics-chart', 'figure'),
    [Input('url', 'pathname')]
)
def update_battery_economics(pathname):
    """Compare battery economics across scenarios."""
    fig = go.Figure()
    
    for scenario in ['worst', 'average', 'best']:
        data = battery_analysis_df[battery_analysis_df['scenario'] == scenario]
        fig.add_trace(go.Scatter(
            x=data['capacity_gwh'], y=data['capex_million_usd'],
            mode='lines+markers', name=scenario.capitalize(),
            line=dict(color=SCENARIO_COLORS.get(scenario, COLOR_AVERAGE), width=2),
            marker=dict(size=8),
            text=data['shortfall_reduction_pct'].round(1),
            hovertemplate='%{x} GWh<br>CAPEX: $%{y:.1f}M<br>Reduction: %{text}%'
        ))
    
    fig.update_layout(
        title="Battery Storage Capital Costs",
        xaxis_title="Battery Capacity (GWh)",
        yaxis_title="CAPEX (Million USD)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Interactive Renewable Energy Dashboard")
    print("="*70)
    print("\nStarting Dash application...")
    print("Navigate to: http://localhost:8050")
    print("\nPages:")
    print("  - Overview: Dashboard with key metrics")
    print("  - Time Series: Interactive scenario explorer")
    print("  - Storage: Battery optimization analysis")
    print("  - Metrics: Comprehensive comparison and analytics")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, port=8050)