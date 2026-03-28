"""
AeroGuard AI - Hyperlocal AQI Prediction & Forecasting Engine
-------------------------------------------------------------
Engines:
1. NOWCAST: Random Forest (Prediction), Isolation Forest (Anomalies), KNN (Trust).
2. FORECAST: XGBoost (1-6 Hour Ahead Prediction Baseline).
3. ROUTING: Inhaled Dose Calculator (Physiological Health Impact).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.neighbors import NearestNeighbors
import xgboost as xgb # NEW: For Forecasting
import warnings

warnings.filterwarnings("ignore") 

# ==========================================
# 1. DIGITAL TWIN: HISTORICAL DATA GENERATION
# ==========================================
np.random.seed(42)
n_samples = 1500

mock_wind = np.random.uniform(0.1, 8.0, n_samples)
mock_free_flow = np.full(n_samples, 40.0)
mock_current = np.random.uniform(5.0, 40.0, n_samples)
speed_drop = mock_free_flow - mock_current

# Current AQI target (For Nowcast)
mock_aqi = 105.0 + (speed_drop * 4.2) - (mock_wind * 14.5) + np.random.normal(0, 15, n_samples)
mock_aqi = np.clip(mock_aqi, 50, 500)

# Future AQI target (For Forecast - Simulating what happens 3 hours later based on wind clearing traffic)
mock_future_aqi = mock_aqi * 0.85 - (mock_wind * 5.0) + np.random.normal(0, 10, n_samples)
mock_future_aqi = np.clip(mock_future_aqi, 50, 500)

X_train = pd.DataFrame({
    'wind_speed': mock_wind,
    'current_speed': mock_current,
    'free_flow_speed': mock_free_flow
})
y_train_nowcast = mock_aqi
y_train_forecast = mock_future_aqi

# ==========================================
# 2. ML MODEL TRAINING (Runs on Boot)
# ==========================================
# --- ENGINE A: NOWCAST MODELS ---
print("🧠 [AeroGuard AI Core] Training Random Forest Regressor (Nowcast)...")
rf_model = RandomForestRegressor(n_estimators=150, random_state=42) 
rf_model.fit(X_train, y_train_nowcast)

print("🛡️ [AeroGuard AI Core] Training Isolation Forest for Anomaly Detection...")
iso_forest = IsolationForest(contamination=0.05, random_state=42)
iso_forest.fit(X_train)

print("🔍 [AeroGuard AI Core] Training KNN for Generalization Bounds...")
knn_model = NearestNeighbors(n_neighbors=5)
knn_model.fit(X_train)
train_spread = np.mean(np.std(X_train, axis=0))

# --- ENGINE B: FORECAST MODEL (NEW) ---
print("🔮 [AeroGuard AI Core] Training XGBoost Baseline (3-Hour Forecast)...")
xgb_forecast_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
xgb_forecast_model.fit(X_train, y_train_forecast)

print("✅ [AeroGuard AI Core] All Models fully trained and ready.\n")

# ==========================================
# 3. LIVE PREDICTION ENGINE (NOWCAST)
# ==========================================
def calculate_hyperlocal_aqi(weather_data, traffic_data):
    """Calculates CURRENT AQI based on live traffic and weather (Engine A)"""
    wind_speed = weather_data.get("wind_speed", 2.0)
    current_speed = traffic_data.get("current_speed", 40.0)
    free_flow_speed = traffic_data.get("free_flow_speed", 40.0)

    live_features = pd.DataFrame({
        'wind_speed': [wind_speed],
        'current_speed': [current_speed],
        'free_flow_speed': [free_flow_speed]
    })

    # 1. PREDICTION & VARIANCE (Confidence Interval)
    all_tree_predictions = np.array([
        tree.predict(live_features.values) for tree in rf_model.estimators_
    ])
    mean_pred = np.mean(all_tree_predictions, axis=0)[0]
    std_pred  = np.std(all_tree_predictions, axis=0)[0]
    
    lower_bound = max(50, mean_pred - (1.96 * std_pred))
    upper_bound = min(500, mean_pred + (1.96 * std_pred))
    confidence_pct = max(0, min(100, 100 - (std_pred / mean_pred * 100)))

    # 2. ANOMALY DETECTION
    is_anomaly = iso_forest.predict(live_features)[0] == -1 
    if is_anomaly:
        confidence_pct -= 15 

    # 3. KNN GENERALIZATION TRUST (Interpolation vs Extrapolation)
    distances, _ = knn_model.kneighbors(live_features.values)
    avg_distance = np.mean(distances)
    normalized_dist = avg_distance / train_spread
    
    threshold = 0.8 
    if normalized_dist < threshold:
        trust_mode = "INTERPOLATION"
        trust_exp = "Street conditions match training data perfectly. High mathematical trust."
    else:
        trust_mode = "EXTRAPOLATION"
        trust_exp = "Novel environmental conditions. Treating prediction as an estimate."
        confidence_pct -= 10 

    final_aqi = int(max(50, min(mean_pred, 500)))

    return {
        "current_aqi": final_aqi,
        "lower_bound": int(lower_bound),
        "upper_bound": int(upper_bound),
        "confidence_pct": round(confidence_pct, 1),
        "is_anomaly": is_anomaly,
        "trust_mode": trust_mode,
        "trust_exp": trust_exp 
    }

# ==========================================
# 4. FORECASTING ENGINE (NEW)
# ==========================================
def forecast_future_aqi(weather_data, traffic_data):
    """Predicts future AQI (1-6 hours ahead) using XGBoost (Engine B)"""
    live_features = pd.DataFrame({
        'wind_speed': [weather_data.get("wind_speed", 2.0)],
        'current_speed': [traffic_data.get("current_speed", 40.0)],
        'free_flow_speed': [traffic_data.get("free_flow_speed", 40.0)]
    })
    
    future_pred = xgb_forecast_model.predict(live_features)[0]
    return int(max(50, min(future_pred, 500)))

# ==========================================
# 5. DOSAGE CALCULATOR (SCIENTIFIC RIGOR)
# ==========================================
def calculate_inhaled_dose(aqi_val, duration_minutes, transport_mode="vehicle_closed"):
    """
    Calculates physiological dose using Breathing Rates (BR) and Infiltration Factors (IF).
    """
    # Convert AQI heuristic to PM2.5 concentration (µg/m³)
    estimated_concentration_ug_m3 = aqi_val * 0.7 
    
    # Profiles: [Breathing Rate (m3/hour), Infiltration Factor]
    exposure_profiles = {
        "pedestrian": [1.5, 1.0],       # Moderate activity, 100% exposure
        "cyclist": [2.5, 1.0],          # Heavy activity, 100% exposure
        "vehicle_open": [0.6, 0.8],     # Sedentary, windows down (80% infiltration)
        "vehicle_closed": [0.6, 0.4]    # Sedentary, AC on/recirculate (40% infiltration)
    }
    
    br, infiltration = exposure_profiles.get(transport_mode.lower(), [0.6, 0.4])
    duration_hours = duration_minutes / 60.0
    
    # Scientific Formula: Mass = Concentration * Infiltration Factor * Breathing Rate * Time
    total_dose_ug = estimated_concentration_ug_m3 * infiltration * duration_hours * br
    return round(total_dose_ug, 2)


# ==========================================
# 6. SYSTEM TEST
# ==========================================
if __name__ == "__main__":
    test_weather = {"wind_speed": 1.5}
    test_traffic = {"current_speed": 15.0, "free_flow_speed": 40.0} # Heavy congestion
    
    print("--- 🚦 NOWCAST (Live) ---")
    live_data = calculate_hyperlocal_aqi(test_weather, test_traffic)
    print(live_data)
    
    print("\n--- 🔮 FORECAST (3 Hours Ahead) ---")
    future_aqi = forecast_future_aqi(test_weather, test_traffic)
    print(f"Predicted AQI in 3 hours: {future_aqi}")
    
    print("\n--- 🫁 HEALTH IMPACT (Commute Comparison) ---")
    commute_time = 45 # 45 minute drive
    dose_now = calculate_inhaled_dose(live_data["current_aqi"], commute_time, "driving")
    dose_later = calculate_inhaled_dose(future_aqi, commute_time, "driving")
    
    print(f"If dispatched NOW: User inhales ~{dose_now} µg of PM2.5")
    print(f"If dispatched in 3 HOURS: User inhales ~{dose_later} µg of PM2.5")
    if dose_later < dose_now:
        print("💡 RECOMMENDATION: Delay dispatch to optimize health constraints.")