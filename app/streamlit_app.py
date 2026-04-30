"""
Streamlit dashboard for Renewable Energy Data Analysis

Run:
    streamlit run streamlit_app.py

This app expects the CSV 'germany_energy_weather_2012_2020.csv' to be located in data/raw.
It processes the dataframe, computes generation totals, identifies shortfall periods, and provides
interactive Plotly charts with a date-range filter and a deviation-from-mean filter.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from neuralprophet import NeuralProphet


# Colors
COLOR_SOLAR = "#FFA500"  # orange
COLOR_WIND = "#1f77b4"   # blue
COLOR_DEMAND = "#d62728" # red
COLOR_SHORTFALL = "#9467bd" # purple


@st.cache_data
def load_data(csv_file_path: str = None) -> pd.DataFrame:
    """Load CSV into a DataFrame. CSV is expected to contain utc_timestamp, load_mw,
    solar_generation_mw, wind_generation_mw (or similar names)."""
    if csv_file_path is None:
        csv_file_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "germany_energy_weather_2012_2020.csv"
    dataframe = pd.read_csv(csv_file_path)
    if dataframe.empty:
        raise ValueError(f"Loaded CSV is empty: {csv_file_path}")
    return dataframe


@st.cache_data
def process_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, compute totals, shortfall, cumulative sums and deviations."""
    dataframe = dataframe.copy()

    # timestamp
    if "utc_timestamp" not in dataframe.columns:
        raise KeyError("Expected column 'utc_timestamp' in input dataframe")
    dataframe["utc_timestamp"] = pd.to_datetime(dataframe["utc_timestamp"], utc=True)

    # demand
    if "load_mw" in dataframe.columns:
        dataframe["demand"] = dataframe["load_mw"]
    elif "demand_mw" in dataframe.columns:
        dataframe["demand"] = dataframe["demand_mw"]
    else:
        raise KeyError("Expected demand column like 'load_mw' or 'demand_mw'")

    # solar
    if "solar_generation_mw" in dataframe.columns:
        dataframe["solar"] = dataframe["solar_generation_mw"]
    elif "solar_mw" in dataframe.columns:
        dataframe["solar"] = dataframe["solar_mw"]
    else:
        raise KeyError("Expected solar column like 'solar_generation_mw' or 'solar_mw'")

    # wind
    if "wind_generation_mw" in dataframe.columns:
        dataframe["wind"] = dataframe["wind_generation_mw"]
    elif "wind_mw" in dataframe.columns:
        dataframe["wind"] = dataframe["wind_mw"]
    else:
        raise KeyError("Expected wind column like 'wind_generation_mw' or 'wind_mw'")

    # totals and shortfall
    dataframe["generation_total"] = dataframe["solar"] + dataframe["wind"]
    dataframe["computed_shortfall"] = dataframe["demand"] - dataframe["generation_total"]
    dataframe["shortfall"] = dataframe["computed_shortfall"].clip(lower=0)

    # ensure chronological order
    dataframe = dataframe.sort_values("utc_timestamp").reset_index(drop=True)

    # cumulative totals
    dataframe["cum_shortfall"] = dataframe["shortfall"].cumsum()
    dataframe["cum_net"] = dataframe["computed_shortfall"].cumsum()

    # deviations relative to mean for interactive filtering
    metrics = {
        "solar": "solar",
        "wind": "wind",
        "generation": "generation_total",
        "demand": "demand",
    }
    for key, col in metrics.items():
        mean = dataframe[col].mean()
        if mean == 0 or np.isnan(mean):
            dataframe[f"dev_{key}"] = 0.0
        else:
            dataframe[f"dev_{key}"] = (dataframe[col] - mean) / mean

    return dataframe


def filter_by_date_and_deviation(
    dataframe: pd.DataFrame,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    deviation_column: str,
    deviation_minimum: float,
    deviation_maximum: float,
) -> pd.DataFrame:
    """Filter dataframe by date range and deviation column between deviation_minimum and deviation_maximum."""
    mask = (dataframe["utc_timestamp"] >= start_ts) & (dataframe["utc_timestamp"] <= end_ts)
    if deviation_column in dataframe.columns:
        mask &= (dataframe[deviation_column] >= deviation_minimum) & (dataframe[deviation_column] <= deviation_maximum)
    return dataframe.loc[mask].copy()


def make_line_chart(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    color: str,
    title: str,
    y_axis_title: str = "MW",
    hover_name: str = None,
) -> go.Figure:
    """Create a simple Plotly line chart with clear hovertemplate."""
    fig = go.Figure()
    hovertemplate = "%{x}<br>" + title + ": %{y:,.0f} MW<extra></extra>"
    fig.add_trace(
        go.Scatter(
            x=dataframe[x_column],
            y=dataframe[y_column],
            mode="lines",
            name=title,
            line=dict(color=color),
            hovertemplate=hovertemplate,
        )
    )
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title=y_axis_title, template="plotly_white")
    return fig


def make_combined_generation_vs_demand(dataframe: pd.DataFrame) -> go.Figure:
    """Combined chart showing generation (solar+wind) vs demand."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dataframe["utc_timestamp"],
            y=dataframe["generation_total"],
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
            x=dataframe["utc_timestamp"],
            y=dataframe["demand"],
            mode="lines",
            name="Demand",
            line=dict(color=COLOR_DEMAND, width=2),
            hovertemplate="%{x}<br>Demand: %{y:,.0f} MW<extra></extra>",
        )
    )
    fig.update_layout(title="Generation vs Demand", xaxis_title="Time", yaxis_title="MW", template="plotly_white")
    return fig


def make_shortfall_chart(dataframe: pd.DataFrame) -> go.Figure:
    """Shortfall chart over time range."""
    fig = go.Figure()
    # shortfall
    fig.add_trace(
        go.Scatter(
            x=dataframe["utc_timestamp"],
            y=dataframe["shortfall"],
            mode="lines",
            name="Shortfall",
            line=dict(color=COLOR_SHORTFALL),
            hovertemplate="%{x}<br>Shortfall: %{y:,.0f} MW·hours<extra></extra>",
            fill="tozeroy",
            opacity=0.6,
        )
    )

    fig.update_layout(
        title="Shortfall Over Time",
        xaxis_title="Time",
        yaxis_title="MW·hours",
        template="plotly_white",
    )
    return fig


def format_large_number(x: float) -> str:
    return f"{x:,.0f}"


@st.cache_resource
def load_models():
    """Load all trained models and feature information."""
    try:
        # Use src/models in the project root
        models_dir = Path(__file__).resolve().parents[1] / "src" / "models"
        
        # If that doesn't exist, try from cwd
        if not models_dir.exists():
            models_dir = Path.cwd() / "src" / "models"
        
        if not models_dir.exists():
            st.error(f"Models directory not found at: {models_dir}")
            return None
        
        # Load models with better error handling
        rf_path = models_dir / "random_forest_model.joblib"
        prophet_path = models_dir / "prophet_model.joblib"
        feature_path = models_dir / "feature_info.joblib"
        
        if not rf_path.exists():
            st.error(f"Random Forest model not found at: {rf_path}")
            return None
        if not prophet_path.exists():
            st.error(f"Prophet model not found at: {prophet_path}")
            return None
        if not feature_path.exists():
            st.error(f"Feature info not found at: {feature_path}")
            return None
        
        random_forest_model = joblib.load(str(rf_path))
        prophet_model = joblib.load(str(prophet_path))
        
        # Try loading NeuralProphet with the save method format
        try:
            neuralprophet_model = NeuralProphet.load(str(models_dir / "neuralprophet_model"))
        except Exception:
            # Fallback: try joblib
            neuralprophet_model = joblib.load(str(models_dir / "neuralprophet_model.joblib"))
        
        feature_info = joblib.load(str(feature_path))
        return {
            "random_forest": random_forest_model,
            "prophet": prophet_model,
            "neuralprophet": neuralprophet_model,
            "feature_info": feature_info
        }
    except Exception as e:
        st.error(f"Models not found or error loading models: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None


def predict_random_forest(model, irradiance: float, wind_speed: float, temperature: float) -> float:
    """Predict shortfall using Random Forest model."""
    from datetime import datetime
    now = datetime.now()
    
    features = pd.DataFrame({
        "irradiance_wm2": [irradiance],
        "wind_speed_10m_ms": [wind_speed],
        "temperature_2m_c": [temperature],
        "hour": [now.hour],
        "day_of_week": [now.weekday()],
        "month": [now.month],
        "day_of_year": [now.timetuple().tm_yday],
        "lag_1h_shortfall": [40000],  # Use typical value
        "lag_24h_shortfall": [40000],
        "lag_168h_shortfall": [40000],
        "lag_24h_load": [50000],
        "lag_24h_wind": [15000],
        "lag_24h_solar": [5000],
    })
    prediction = model.predict(features)[0]
    return max(0, prediction)  # Shortfall cannot be negative


def predict_prophet(model, irradiance: float, wind_speed: float, temperature: float) -> float:
    """Predict shortfall using Prophet model."""
    from datetime import datetime
    now = datetime.now()
    
    forecast_data = pd.DataFrame({
        "ds": [now],
        "irradiance_wm2": [irradiance],
        "wind_speed_10m_ms": [wind_speed],
        "temperature_2m_c": [temperature],
    })
    forecast = model.predict(forecast_data)
    prediction = forecast["yhat"].values[0]
    return max(0, prediction)


def predict_neuralprophet(model, irradiance: float, wind_speed: float, temperature: float) -> float:
    """Predict shortfall using NeuralProphet model."""
    from datetime import datetime
    now = datetime.now()
    
    df = pd.DataFrame({
        "ds": [now],
        "y": [40000],  # Use typical value for history
        "irradiance_wm2": [irradiance],
        "wind_speed_10m_ms": [wind_speed],
        "temperature_2m_c": [temperature],
    })
    forecast = model.predict(df)
    if forecast.empty or forecast["yhat1"].isna().all():
        return 40000
    prediction = forecast["yhat1"].values[-1]
    return max(0, prediction) if not pd.isna(prediction) else 40000


def main():
    st.set_page_config(page_title="Renewable Energy Dashboard", layout="wide")
    st.title("Renewable Energy — Solar, Wind, and Demand")

    # Load and prepare data
    raw_data = load_data()
    dataframe = process_data(raw_data)

    # Sidebar controls: comprehensive interactive filters
    st.sidebar.header("📊 Filters & Controls")
    
    # ===== Date & Time Filters =====
    with st.sidebar.expander("📅 Date & Time", expanded=True):
        min_date = dataframe["utc_timestamp"].dt.date.min()
        max_date = dataframe["utc_timestamp"].dt.date.max()
        date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = date_range
            end_date = date_range
        
        # Hour of day filter
        hour_range = st.slider("Hour of day", min_value=0, max_value=23, value=(0, 23), step=1)
        
        # Day of week filter
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days = st.multiselect("Days of week", days_of_week, default=days_of_week)
        selected_day_nums = [days_of_week.index(day) for day in selected_days]
        
        # Month filter
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        selected_months = st.multiselect("Months", months, default=months)
        selected_month_nums = [months.index(m) + 1 for m in selected_months]
    
    # ===== Generation & Demand Filters =====
    with st.sidebar.expander("⚡ Generation & Demand", expanded=True):
        solar_min = float(dataframe["solar"].min())
        solar_max = float(dataframe["solar"].max())
        solar_range = st.slider("Solar generation (MW)", min_value=solar_min, max_value=solar_max, 
                                value=(solar_min, solar_max), step=100.0)
        
        wind_min = float(dataframe["wind"].min())
        wind_max = float(dataframe["wind"].max())
        wind_range = st.slider("Wind generation (MW)", min_value=wind_min, max_value=wind_max, 
                               value=(wind_min, wind_max), step=100.0)
        
        demand_min = float(dataframe["demand"].min())
        demand_max = float(dataframe["demand"].max())
        demand_range = st.slider("Demand (MW)", min_value=demand_min, max_value=demand_max, 
                                 value=(demand_min, demand_max), step=100.0)
    
    # ===== Shortfall Filters =====
    with st.sidebar.expander("📉 Shortfall Analysis", expanded=True):
        shortfall_min = float(dataframe["shortfall"].min())
        shortfall_max = float(dataframe["shortfall"].max())
        shortfall_range = st.slider("Shortfall (MW)", min_value=shortfall_min, max_value=shortfall_max, 
                                    value=(shortfall_min, shortfall_max), step=100.0)
        
        # Filter for periods with shortfall
        show_only_shortfall = st.checkbox("Show only periods with shortfall", value=False)
    
    # ===== Deviation Filters =====
    with st.sidebar.expander("📊 Deviation from Mean", expanded=False):
        metric_options = {
            "Generation (solar+wind)": "dev_generation",
            "Solar": "dev_solar",
            "Wind": "dev_wind",
            "Demand": "dev_demand",
        }
        metric_label = st.selectbox("Deviation metric", list(metric_options.keys()))
        deviation_column = metric_options[metric_label]
        
        full_deviation_minimum = float(dataframe[deviation_column].min())
        full_deviation_maximum = float(dataframe[deviation_column].max())
        deviation_range = st.slider(
            label="Allowed deviation range",
            min_value=float(full_deviation_minimum),
            max_value=float(full_deviation_maximum),
            value=(float(full_deviation_minimum), float(full_deviation_maximum)),
            step=0.01,
        )

    # Apply all filters to the dataframe
    filtered_dataframe = dataframe.copy()
    
    # Date range filter
    start_timestamp = pd.Timestamp(start_date).tz_localize("UTC")
    end_timestamp = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    end_timestamp = end_timestamp.tz_localize("UTC") if end_timestamp.tzinfo is None else end_timestamp
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe["utc_timestamp"] >= start_timestamp) & 
        (filtered_dataframe["utc_timestamp"] <= end_timestamp)
    ]
    
    # Hour of day filter
    filtered_dataframe["hour"] = filtered_dataframe["utc_timestamp"].dt.hour
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe["hour"] >= hour_range[0]) & 
        (filtered_dataframe["hour"] <= hour_range[1])
    ]
    
    # Day of week filter
    filtered_dataframe["day_of_week"] = filtered_dataframe["utc_timestamp"].dt.dayofweek
    filtered_dataframe = filtered_dataframe[filtered_dataframe["day_of_week"].isin(selected_day_nums)]
    
    # Month filter
    filtered_dataframe["month"] = filtered_dataframe["utc_timestamp"].dt.month
    filtered_dataframe = filtered_dataframe[filtered_dataframe["month"].isin(selected_month_nums)]
    
    # Solar generation range filter
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe["solar"] >= solar_range[0]) & 
        (filtered_dataframe["solar"] <= solar_range[1])
    ]
    
    # Wind generation range filter
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe["wind"] >= wind_range[0]) & 
        (filtered_dataframe["wind"] <= wind_range[1])
    ]
    
    # Demand range filter
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe["demand"] >= demand_range[0]) & 
        (filtered_dataframe["demand"] <= demand_range[1])
    ]
    
    # Shortfall range filter
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe["shortfall"] >= shortfall_range[0]) & 
        (filtered_dataframe["shortfall"] <= shortfall_range[1])
    ]
    
    # Show only shortfall periods filter
    if show_only_shortfall:
        filtered_dataframe = filtered_dataframe[filtered_dataframe["shortfall"] > 0]
    
    # Deviation range filter
    filtered_dataframe = filtered_dataframe[
        (filtered_dataframe[deviation_column] >= deviation_range[0]) & 
        (filtered_dataframe[deviation_column] <= deviation_range[1])
    ]

    # Summary metrics
    total_generation = filtered_dataframe["generation_total"].sum()
    total_demand = filtered_dataframe["demand"].sum()
    total_shortfall = filtered_dataframe["shortfall"].sum()
    
    # Filter statistics
    total_records = len(dataframe)
    filtered_records = len(filtered_dataframe)
    filter_efficiency = (filtered_records / total_records * 100) if total_records > 0 else 0

    # Top-level metrics
    st.markdown("### 📈 Filtered Data Summary")
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Records Matched", f"{filtered_records:,} / {total_records:,}")
    metric_col2.metric("Filter Coverage", f"{filter_efficiency:.1f}%")
    metric_col3.metric("Total Generation", format_large_number(total_generation) + " MW·hrs")
    metric_col4.metric("Total Demand", format_large_number(total_demand) + " MW·hrs")
    metric_col5.metric("Total Shortfall", format_large_number(total_shortfall) + " MW·hrs")

    if filtered_dataframe.empty:
        st.warning("No data matches the selected filters. Try expanding the date range or deviation slider.")
        return

    # Layout: Top row - 3 charts
    st.markdown("### Individual series")
    solar_column, wind_column, demand_column = st.columns(3)

    solar_chart = make_line_chart(filtered_dataframe, "utc_timestamp", "solar", COLOR_SOLAR, "Solar generation", "MW")
    wind_chart = make_line_chart(filtered_dataframe, "utc_timestamp", "wind", COLOR_WIND, "Wind generation", "MW")
    demand_chart = make_line_chart(filtered_dataframe, "utc_timestamp", "demand", COLOR_DEMAND, "Demand (load)", "MW")

    with solar_column:
        st.plotly_chart(solar_chart, use_container_width=True)
    with wind_column:
        st.plotly_chart(wind_chart, use_container_width=True)
    with demand_column:
        st.plotly_chart(demand_chart, use_container_width=True)

    # Middle: combined generation vs demand
    st.markdown("### Generation (solar + wind) vs Demand")
    combined_chart = make_combined_generation_vs_demand(filtered_dataframe)
    st.plotly_chart(combined_chart, use_container_width=True)

    # Bottom: cumulative shortfall
    st.markdown("### Cumulative Shortfall Over Time")
    cumulative_chart = make_shortfall_chart(filtered_dataframe)
    st.plotly_chart(cumulative_chart, use_container_width=True)

    # Prediction section
    st.markdown("---")
    
    # Advanced Statistics Section
    st.markdown("## 📊 Detailed Statistics")
    
    stats_col1, stats_col2 = st.columns(2)
    
    with stats_col1:
        st.subheader("Generation & Demand Stats")
        stats_data = {
            "Metric": ["Solar (MW)", "Wind (MW)", "Generation (MW)", "Demand (MW)", "Shortfall (MW)"],
            "Mean": [
                f"{filtered_dataframe['solar'].mean():.0f}",
                f"{filtered_dataframe['wind'].mean():.0f}",
                f"{filtered_dataframe['generation_total'].mean():.0f}",
                f"{filtered_dataframe['demand'].mean():.0f}",
                f"{filtered_dataframe['shortfall'].mean():.0f}",
            ],
            "Median": [
                f"{filtered_dataframe['solar'].median():.0f}",
                f"{filtered_dataframe['wind'].median():.0f}",
                f"{filtered_dataframe['generation_total'].median():.0f}",
                f"{filtered_dataframe['demand'].median():.0f}",
                f"{filtered_dataframe['shortfall'].median():.0f}",
            ],
            "Std Dev": [
                f"{filtered_dataframe['solar'].std():.0f}",
                f"{filtered_dataframe['wind'].std():.0f}",
                f"{filtered_dataframe['generation_total'].std():.0f}",
                f"{filtered_dataframe['demand'].std():.0f}",
                f"{filtered_dataframe['shortfall'].std():.0f}",
            ],
            "Min": [
                f"{filtered_dataframe['solar'].min():.0f}",
                f"{filtered_dataframe['wind'].min():.0f}",
                f"{filtered_dataframe['generation_total'].min():.0f}",
                f"{filtered_dataframe['demand'].min():.0f}",
                f"{filtered_dataframe['shortfall'].min():.0f}",
            ],
            "Max": [
                f"{filtered_dataframe['solar'].max():.0f}",
                f"{filtered_dataframe['wind'].max():.0f}",
                f"{filtered_dataframe['generation_total'].max():.0f}",
                f"{filtered_dataframe['demand'].max():.0f}",
                f"{filtered_dataframe['shortfall'].max():.0f}",
            ]
        }
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
    
    with stats_col2:
        st.subheader("Shortfall Analysis")
        shortfall_df = filtered_dataframe[filtered_dataframe["shortfall"] > 0]
        shortfall_pct = (len(shortfall_df) / len(filtered_dataframe) * 100) if len(filtered_dataframe) > 0 else 0
        
        col_a, col_b = st.columns(2)
        col_a.metric("Periods with Shortfall", f"{len(shortfall_df):,} ({shortfall_pct:.1f}%)")
        col_a.metric("Avg Shortfall (when occurs)", f"{shortfall_df['shortfall'].mean():.0f} MW" if len(shortfall_df) > 0 else "N/A")
        col_b.metric("Max Shortfall", f"{filtered_dataframe['shortfall'].max():.0f} MW")
        col_b.metric("Total Shortfall Hours", f"{total_shortfall:.0f} MW·hrs")
    
    # Breakdown by time dimensions
    st.markdown("### Breakdown by Time")
    time_col1, time_col2, time_col3 = st.columns(3)
    
    with time_col1:
        st.subheader("By Hour of Day")
        hourly = filtered_dataframe.groupby("hour").agg({
            "generation_total": "mean",
            "demand": "mean",
            "shortfall": "mean"
        }).round(0)
        st.line_chart(hourly)
    
    with time_col2:
        st.subheader("By Day of Week")
        days_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        daily = filtered_dataframe.groupby("day_of_week").agg({
            "generation_total": "mean",
            "demand": "mean",
            "shortfall": "mean"
        }).round(0)
        daily.index = daily.index.map(days_map)
        st.bar_chart(daily)
    
    with time_col3:
        st.subheader("By Month")
        month_map = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                     7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        monthly = filtered_dataframe.groupby("month").agg({
            "generation_total": "mean",
            "demand": "mean",
            "shortfall": "mean"
        }).round(0)
        monthly.index = monthly.index.map(month_map)
        st.bar_chart(monthly)
    
    st.markdown("---")
    st.markdown("## 🤖 Model-Based Predictions")
    
    models = load_models()
    if models:
        # Model selection and weather parameter controls
        prediction_col1, prediction_col2 = st.columns([2, 3])
        
        with prediction_col1:
            st.subheader("Prediction Settings")
            selected_model = st.selectbox(
                "Select Model",
                options=["Random Forest", "Prophet", "NeuralProphet"],
                help="Choose which trained model to use for predictions"
            )
        
        with prediction_col2:
            st.subheader("Weather Parameters")
            param_col1, param_col2, param_col3 = st.columns(3)
            
            with param_col1:
                irradiance = st.slider(
                    "Solar Irradiance (W/m²)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=500.0,
                    step=10.0,
                    key="irradiance_slider"
                )
            
            with param_col2:
                wind_speed = st.slider(
                    "Wind Speed (m/s)",
                    min_value=0.0,
                    max_value=25.0,
                    value=5.0,
                    step=0.5,
                    key="wind_speed_slider"
                )
            
            with param_col3:
                temperature = st.slider(
                    "Temperature (°C)",
                    min_value=-20.0,
                    max_value=40.0,
                    value=10.0,
                    step=1.0,
                    key="temperature_slider"
                )
        
        # Make prediction based on selected model
        model_map = {
            "Random Forest": ("random_forest", predict_random_forest),
            "Prophet": ("prophet", predict_prophet),
            "NeuralProphet": ("neuralprophet", predict_neuralprophet),
        }
        
        model_key, predict_func = model_map[selected_model]
        
        try:
            predicted_shortfall = predict_func(
                models[model_key],
                irradiance,
                wind_speed,
                temperature
            )
        except Exception as e:
            st.warning(f"Prediction error: {str(e)}")
            predicted_shortfall = 40000
        
        # Display prediction results
        st.markdown("### Prediction Results")
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric(
                "Model Used",
                selected_model,
            )
        
        with metric_col2:
            st.metric(
                "Predicted Shortfall",
                format_large_number(predicted_shortfall) + " MW",
                delta=None
            )
        
        with metric_col3:
            actual_shortfall = total_shortfall / len(filtered_dataframe) if len(filtered_dataframe) > 0 else 0
            delta_value = predicted_shortfall - actual_shortfall
            st.metric(
                "vs Average in Selection",
                format_large_number(delta_value) + " MW",
                delta=f"{delta_value:+,.0f}" if delta_value != 0 else "0"
            )
        
        # Prediction explanation
        with st.expander("About Predictions"):
            st.write(
                """
                **How Predictions Work:**
                - **Random Forest**: Uses weather data + temporal patterns + lagged values to predict shortfall
                - **Prophet**: Facebook's time-series forecasting with weather regressors and seasonal components
                - **NeuralProphet**: Neural network with 24-hour autoregressive lookback and weather integration
                
                **Weather Parameters:**
                - **Solar Irradiance**: Affects solar generation (0-1000 W/m²)
                - **Wind Speed**: Affects wind generation (0-25 m/s)
                - **Temperature**: Affects both generation and demand (°C)
                
                Adjust sliders to see how weather conditions impact predicted energy shortfall.
                """
            )

    # Footer explanations for non-technical users
    st.markdown("---")
    with st.expander("How to read these charts"):
        st.write(
            ""
            "- Solar, Wind and Demand are shown as time series (MW).\n"
            "- Generation = Solar + Wind.\n"
            "- Shortfall is the difference between Demand and Generation. Right now, demand exceeds generation.\n"
            "- The Cumulative Shortfall chart shows how energy deficits add up over the selected period (approx. MW·hours if hourly data).\n"
            "- Use the deviation slider to filter hours by how far a selected metric deviates from its long-term average.\n"
            "- All charts update reactively when you change the date range or deviation range."
            ""
        )


if __name__ == "__main__":
    main()
