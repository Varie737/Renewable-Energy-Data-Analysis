"""
Streamlit dashboard for Renewable Energy Data Analysis

Run:
    streamlit run streamlit_app.py

This app expects the CSV 'germany_energy_weather_2012_2020.csv' to be in the same folder as this script.
It processes the dataframe, computes generation totals, classifies shortfall vs surplus, and provides
interactive Plotly charts with a date-range filter and a deviation-from-mean filter.
"""

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Colors
COLOR_SOLAR = "#FFA500"  # orange
COLOR_WIND = "#1f77b4"   # blue
COLOR_DEMAND = "#d62728" # red
COLOR_SHORTFALL = "#9467bd" # purple
COLOR_SURPLUS = "#2ca02c" # green


@st.cache_data
def load_data(csv_path: str = None) -> pd.DataFrame:
    """Load CSV into a DataFrame. CSV is expected to contain utc_timestamp, load_mw,
    solar_generation_mw, wind_generation_mw (or similar names)."""
    if csv_path is None:
        csv_path = Path(__file__).resolve().parent / "germany_energy_weather_2012_2020.csv"
    df = pd.read_csv(csv_path)
    return df


@st.cache_data
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, compute totals, shortfall/surplus, cumulative sums and deviations."""
    df = df.copy()

    # timestamp
    if "utc_timestamp" not in df.columns:
        raise KeyError("Expected column 'utc_timestamp' in input dataframe")
    df["utc_timestamp"] = pd.to_datetime(df["utc_timestamp"], utc=True)

    # demand
    if "load_mw" in df.columns:
        df["demand"] = df["load_mw"]
    elif "demand_mw" in df.columns:
        df["demand"] = df["demand_mw"]
    else:
        raise KeyError("Expected demand column like 'load_mw' or 'demand_mw'")

    # solar
    if "solar_generation_mw" in df.columns:
        df["solar"] = df["solar_generation_mw"]
    elif "solar_mw" in df.columns:
        df["solar"] = df["solar_mw"]
    else:
        raise KeyError("Expected solar column like 'solar_generation_mw' or 'solar_mw'")

    # wind
    if "wind_generation_mw" in df.columns:
        df["wind"] = df["wind_generation_mw"]
    elif "wind_mw" in df.columns:
        df["wind"] = df["wind_mw"]
    else:
        raise KeyError("Expected wind column like 'wind_generation_mw' or 'wind_mw'")

    # totals and shortfall/surplus
    df["generation_total"] = df["solar"] + df["wind"]
    df["computed_shortfall"] = df["demand"] - df["generation_total"]
    df["shortfall"] = df["computed_shortfall"].clip(lower=0)
    df["surplus"] = (-df["computed_shortfall"]).clip(lower=0)

    # ensure chronological order
    df = df.sort_values("utc_timestamp").reset_index(drop=True)

    # cumulative totals
    df["cum_shortfall"] = df["shortfall"].cumsum()
    df["cum_surplus"] = df["surplus"].cumsum()
    df["cum_net"] = df["computed_shortfall"].cumsum()

    # deviations relative to mean for interactive filtering
    metrics = {
        "solar": "solar",
        "wind": "wind",
        "generation": "generation_total",
        "demand": "demand",
    }
    for key, col in metrics.items():
        mean = df[col].mean()
        if mean == 0 or np.isnan(mean):
            df[f"dev_{key}"] = 0.0
        else:
            df[f"dev_{key}"] = (df[col] - mean) / mean

    return df


def filter_by_date_and_deviation(
    df: pd.DataFrame,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    dev_col: str,
    dev_min: float,
    dev_max: float,
) -> pd.DataFrame:
    """Filter dataframe by date range and deviation column between dev_min and dev_max."""
    mask = (df["utc_timestamp"] >= start_ts) & (df["utc_timestamp"] <= end_ts)
    if dev_col in df.columns:
        mask &= (df[dev_col] >= dev_min) & (df[dev_col] <= dev_max)
    return df.loc[mask].copy()


def make_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color: str,
    title: str,
    yaxis_title: str = "MW",
    hover_name: str = None,
) -> go.Figure:
    """Create a simple Plotly line chart with clear hovertemplate."""
    fig = go.Figure()
    hovertemplate = "%{x}<br>" + title + ": %{y:,.0f} MW<extra></extra>"
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines",
            name=title,
            line=dict(color=color),
            hovertemplate=hovertemplate,
        )
    )
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title=yaxis_title, template="plotly_white")
    return fig


def make_combined_generation_vs_demand(df: pd.DataFrame) -> go.Figure:
    """Combined chart showing generation (solar+wind) vs demand."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["utc_timestamp"],
            y=df["generation_total"],
            mode="lines",
            name="Generation (Solar + Wind)",
            line=dict(color=COLOR_SOLAR),
            hovertemplate="%{x}<br>Generation: %{y:,.0f} MW<extra></extra>",
            fill="tozeroy",
            opacity=0.6,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["utc_timestamp"],
            y=df["demand"],
            mode="lines",
            name="Demand",
            line=dict(color=COLOR_DEMAND, width=2),
            hovertemplate="%{x}<br>Demand: %{y:,.0f} MW<extra></extra>",
        )
    )
    fig.update_layout(title="Generation vs Demand", xaxis_title="Time", yaxis_title="MW", template="plotly_white")
    return fig


def make_grand_total_chart(df: pd.DataFrame) -> go.Figure:
    """Grand total chart showing cumulative shortfall and cumulative surplus over time."""
    fig = go.Figure()
    # cumulative shortfall
    fig.add_trace(
        go.Scatter(
            x=df["utc_timestamp"],
            y=df["cum_shortfall"],
            mode="lines",
            name="Cumulative Shortfall",
            line=dict(color=COLOR_SHORTFALL),
            hovertemplate="%{x}<br>Cumulative shortfall: %{y:,.0f} MW·hours<extra></extra>",
            fill="tozeroy",
            opacity=0.6,
        )
    )
    # cumulative surplus
    fig.add_trace(
        go.Scatter(
            x=df["utc_timestamp"],
            y=df["cum_surplus"],
            mode="lines",
            name="Cumulative Surplus",
            line=dict(color=COLOR_SURPLUS),
            hovertemplate="%{x}<br>Cumulative surplus: %{y:,.0f} MW·hours<extra></extra>",
            fill="tozeroy",
            opacity=0.6,
        )
    )
    # net cumulative line
    fig.add_trace(
        go.Scatter(
            x=df["utc_timestamp"],
            y=df["cum_net"],
            mode="lines",
            name="Net Cumulative (Shortfall - Surplus)",
            line=dict(color="black", width=2, dash="dash"),
            hovertemplate="%{x}<br>Net cumulative: %{y:,.0f} MW·hours<extra></extra>",
        )
    )
    fig.update_layout(
        title="Grand Total: Cumulative Shortfall and Surplus",
        xaxis_title="Time",
        yaxis_title="Cumulative MW·hours",
        template="plotly_white",
    )
    return fig


def format_large_number(x: float) -> str:
    return f"{x:,.0f}"


def main():
    st.set_page_config(page_title="Renewable Energy Dashboard", layout="wide")
    st.title("Renewable Energy — Solar, Wind, and Demand")

    # Load and prepare data
    raw = load_data()
    df = process_data(raw)

    # Sidebar controls: date range and deviation
    st.sidebar.header("Filters")
    min_date = df["utc_timestamp"].dt.date.min()
    max_date = df["utc_timestamp"].dt.date.max()
    date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = date_range
        end_date = date_range

    # deviation metric selection
    metric_options = {
        "Generation (solar+wind)": "dev_generation",
        "Solar": "dev_solar",
        "Wind": "dev_wind",
        "Demand": "dev_demand",
    }
    metric_label = st.sidebar.selectbox("Deviation metric (choose which series to filter)", list(metric_options.keys()))
    dev_col = metric_options[metric_label]

    # dynamic slider bounds from full data
    dev_min_full = float(df[dev_col].min())
    dev_max_full = float(df[dev_col].max())
    # clamp extremes for UX
    clamp_min, clamp_max = max(dev_min_full, -2.0), min(dev_max_full, 5.0)
    dev_range = st.sidebar.slider(
        label="Allowed deviation range (value - mean) / mean",
        min_value=float(dev_min_full),
        max_value=float(dev_max_full),
        value=(float(dev_min_full), float(dev_max_full)),
        step=0.01,
    )

    # Convert selected dates to timestamps (include entire day for end_date)
    start_ts = pd.Timestamp(start_date).tz_localize("UTC")
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    end_ts = end_ts.tz_localize("UTC") if end_ts.tzinfo is None else end_ts

    # Filter data
    df_filtered = filter_by_date_and_deviation(df, start_ts, end_ts, dev_col, dev_range[0], dev_range[1])

    # Summary metrics
    total_generation = df_filtered["generation_total"].sum()
    total_demand = df_filtered["demand"].sum()
    total_shortfall = df_filtered["shortfall"].sum()
    total_surplus = df_filtered["surplus"].sum()

    # Top-level metrics
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    col1.metric("Total generation (Solar + Wind)", format_large_number(total_generation) + " MW·hrs")
    col2.metric("Total demand", format_large_number(total_demand) + " MW·hrs")
    col3.metric("Total shortfall (only deficits)", format_large_number(total_shortfall) + " MW·hrs")
    col4.metric("Total surplus (only excess)", format_large_number(total_surplus) + " MW·hrs")

    if df_filtered.empty:
        st.warning("No data matches the selected filters. Try expanding the date range or deviation slider.")
        return

    # Layout: Top row - 3 charts
    st.markdown("### Top: Individual series")
    top_col1, top_col2, top_col3 = st.columns(3)

    fig_solar = make_line_chart(df_filtered, "utc_timestamp", "solar", COLOR_SOLAR, "Solar generation", "MW")
    fig_wind = make_line_chart(df_filtered, "utc_timestamp", "wind", COLOR_WIND, "Wind generation", "MW")
    fig_demand = make_line_chart(df_filtered, "utc_timestamp", "demand", COLOR_DEMAND, "Demand (load)", "MW")

    with top_col1:
        st.plotly_chart(fig_solar, use_container_width=True)
    with top_col2:
        st.plotly_chart(fig_wind, use_container_width=True)
    with top_col3:
        st.plotly_chart(fig_demand, use_container_width=True)

    # Middle: combined generation vs demand
    st.markdown("### Middle: Generation (solar + wind) vs Demand")
    fig_combined = make_combined_generation_vs_demand(df_filtered)
    st.plotly_chart(fig_combined, use_container_width=True)

    # Bottom: grand total cumulative shortfall/surplus
    st.markdown("### Bottom: Grand total — cumulative shortfall and surplus")
    fig_grand = make_grand_total_chart(df_filtered)
    st.plotly_chart(fig_grand, use_container_width=True)

    # Footer explanations for non-technical users
    with st.expander("How to read these charts"):
        st.write(
            ""
            "- Solar, Wind and Demand are shown as time series (MW).\n"
            "- Generation = Solar + Wind.\n"
            "- Shortfall shows only when Demand > Generation; Surplus shows when Generation > Demand.\n"
            "- The Grand Total chart shows cumulative shortfall and surplus over the selected period (approx. MW·hours if hourly data).\n"
            "- Use the deviation slider to filter hours by how far a selected metric deviates from its long-term average.\n"
            "- All charts update reactively when you change the date range or deviation range."
            ""
        )


if __name__ == "__main__":
    main()
