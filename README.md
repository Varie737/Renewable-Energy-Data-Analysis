**# Renewable Energy Shortfall Analysis for Germany (2012–2020)**  
  
This project analyzes renewable energy shortfalls in Germany by integrating electricity demand and generation data with weather conditions. The goal is to understand the dynamics of renewable energy production, identify patterns in shortfalls, and develop forecasting models to predict future renewable energy gaps.  
  
**## Overview**  
  
Renewable energy sources like wind and solar are crucial for sustainable electricity, but their intermittent nature can lead to shortfalls where demand exceeds renewable generation. This analysis combines historical data from Germany's electricity grid with weather data to explore these dynamics, perform exploratory data analysis, and build machine learning models for shortfall forecasting.  
  
The study period covers 2012–2020, focusing on hourly data to capture daily and seasonal patterns. Key insights include the impact of weather on renewable generation, seasonal variability, and the effectiveness of predictive models.  
  
**## Data Sources**  
  
- **Electricity Data**: Hourly electricity load, wind generation, and solar generation for Germany from the Open Power System Data (OPSD) platform.  
- **Weather Data**: Hourly solar irradiance, wind speed, and temperature from NASA POWER for five representative German cities (Berlin, Hamburg, Munich, Frankfurt, Cologne), averaged to create national-level weather variables.  
  
The merged dataset includes variables such as load (MW), wind/solar generation (MW), shortfall (MW), irradiance (W/m²), wind speed (m/s), and temperature (°C).  
  
**## Methodology**  
  
1. **Data Collection and Merging**: Download and clean OPSD energy data and NASA POWER weather data, then merge them on timestamps to create a unified dataset.  
2. **Exploratory Data Analysis (EDA)**: Visualize time series, distributions, correlations, and seasonal patterns. Analyze relationships between weather variables and renewable generation.  
3. **Feature Engineering**: Create time-based features (hour, day of week, month) and lagged variables (e.g., previous hour/day shortfall) for modeling.  
4. **Machine Learning Modeling**:  
   - Train a Random Forest Regressor with lagged features for high-accuracy forecasting.  
   - Compare with a reduced model excluding short-term lags and a Prophet model incorporating seasonality and weather regressors.  
5. **Evaluation**: Assess models using MAE, RMSE, and R² metrics, and analyze feature importance.  
  
**## Key Findings**  
  
- Renewable shortfalls average ~39 GW, with significant variability driven by weather and seasonal patterns.  
- Solar generation correlates strongly with irradiance; wind generation with wind speed.  
- Random Forest with lagged features achieves excellent performance (R² ~0.98), while Prophet provides strong results without short-term lags (R² ~0.77).  
- Extreme shortfalls occur in winter due to high demand and low solar output.  
  
**## Technologies Used**  
  
- **Programming Language**: Python  
- **Libraries**: Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, Prophet  
- **Data Sources**: OPSD API, NASA POWER API  
  
**## How to Run**  
  
1. Clone the repository.  
2. Install dependencies: `pip install -r requirements.txt`  
3. Open and run the Jupyter notebook `Renewable Energy Data Analysis project.ipynb` to reproduce the analysis.  
  
**## Contributing**  
  
Contributions are welcome! Please open an issue or submit a pull request for improvements.  
  
**## License**  
  
This project is open-source under the MIT License.