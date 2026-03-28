"""
AeroGuard AI - Hyperlocal AQI Prediction Engine (ML UPGRADED)
------------------------------------------------
Uses Random Forest for prediction, Isolation Forest for anomalies, 
and KNN for Generalization Trust (Interpolation vs Extrapolation).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.neighbors import NearestNeighbors
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

mock_aqi = 105.0 + (speed_drop * 4.2) - (mock_wind * 14.5) + np.random.normal(0, 15, n_samples)
mock_aqi = np.clip(mock_aqi, 50, 500)

X_train = pd.DataFrame({
    'wind_speed': mock_wind,
    'current_speed': mock_current,
    'free_flow_speed': mock_free_flow
})
y_train = mock_aqi

# ==========================================
# 2. ML MODEL TRAINING (Runs on Boot)
# ==========================================
print("🧠 [AeroGuard AI Core] Training Random Forest Regressor...")
rf_model = RandomForestRegressor(n_estimators=150, random_state=42) # 🚀 UPGRADED TO 150 FOR STABLE VARIANCE
rf_model.fit(X_train, y_train)

print("🛡️ [AeroGuard AI Core] Training Isolation Forest for Anomaly Detection...")
iso_forest = IsolationForest(contamination=0.05, random_state=42)
iso_forest.fit(X_train)

# --- NEW: KNN FOR GENERALIZATION TRUST ---
print("🔍 [AeroGuard AI Core] Training KNN for Generalization Bounds...")
knn_model = NearestNeighbors(n_neighbors=5)
knn_model.fit(X_train)
# Calculate the overall spread (std dev) of training data for normalization
train_spread = np.mean(np.std(X_train, axis=0))

print("✅ [AeroGuard AI Core] All Models fully trained and ready.\n")

# ==========================================
# 3. LIVE PREDICTION ENGINE
# ==========================================
def calculate_hyperlocal_aqi(weather_data, traffic_data):
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

    # 3. NEW: KNN GENERALIZATION TRUST (Interpolation vs Extrapolation)
    distances, _ = knn_model.kneighbors(live_features.values)
    avg_distance = np.mean(distances)
    normalized_dist = avg_distance / train_spread
    
    threshold = 0.8 # Adjusted threshold for synthetic data
    if normalized_dist < threshold:
        trust_mode = "INTERPOLATION"
        trust_exp = "Street conditions match training data perfectly. High mathematical trust."
    else:
        trust_mode = "EXTRAPOLATION"
        trust_exp = "Novel environmental conditions. Treating prediction as an estimate."
        confidence_pct -= 10 # Penalize confidence if extrapolating

    final_aqi = int(max(50, min(mean_pred, 500)))

    return {
        "aqi": final_aqi,
        "lower_bound": int(lower_bound),
        "upper_bound": int(upper_bound),
        "confidence_pct": round(confidence_pct, 1),
        "is_anomaly": is_anomaly,
        "trust_mode": trust_mode,
        "trust_exp": trust_exp }