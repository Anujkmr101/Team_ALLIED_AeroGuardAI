"""
AeroGuard AI - Hyperlocal AQI Prediction Engine (ML UPGRADED)
------------------------------------------------
This module uses Random Forest Regression to predict street-level trapped emissions
and Isolation Forest to detect extreme environmental anomalies.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
import warnings

# Terminal warnings ko clean rakhne ke liye
warnings.filterwarnings("ignore") 

# ==========================================
# 1. DIGITAL TWIN: HISTORICAL DATA GENERATION
# ==========================================
# Hackathon demo ke liye hum Delhi ka synthetic historical data generate kar rahe hain
# Real startup mein yeh data tumhare SQL/Cloud database se aayega.
np.random.seed(42)
n_samples = 1500

# Generating realistic past features: [wind_speed, current_speed, free_flow_speed]
mock_wind = np.random.uniform(0.1, 8.0, n_samples)
mock_free_flow = np.full(n_samples, 40.0)
mock_current = np.random.uniform(5.0, 40.0, n_samples)
speed_drop = mock_free_flow - mock_current

# Target: Generating corresponding historical AQI values
# (Adding some random noise so the AI actually has to 'learn' the pattern)
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
print("🧠 [AeroGuard AI Core] Booting up... Training Random Forest Regressor...")
rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
rf_model.fit(X_train, y_train)

print("🛡️ [AeroGuard AI Core] Training Isolation Forest for Anomaly Detection...")
iso_forest = IsolationForest(contamination=0.05, random_state=42)
iso_forest.fit(X_train)
print("✅ [AeroGuard AI Core] Models fully trained and ready for live ingestion.\n")

# ==========================================
# 3. LIVE PREDICTION ENGINE
# ==========================================
def calculate_hyperlocal_aqi(weather_data, traffic_data):
    """
    Uses the pre-trained Random Forest ML model to predict true street-level AQI.
    Uses Isolation Forest to detect if current environmental conditions are anomalous.
    """
    # 1. Parse live inputs safely
    wind_speed = weather_data.get("wind_speed", 2.0)
    current_speed = traffic_data.get("current_speed", 40.0)
    free_flow_speed = traffic_data.get("free_flow_speed", 40.0)

    # 2. Format for Scikit-Learn prediction
    live_features = pd.DataFrame({
        'wind_speed': [wind_speed],
        'current_speed': [current_speed],
        'free_flow_speed': [free_flow_speed]
    })

    # 3. ML PREDICTION (The actual AI doing the math)
    predicted_aqi = rf_model.predict(live_features)[0]

    # 4. ANOMALY DETECTION (Trust Score Logic)
    # -1 means anomaly (rare condition), 1 means normal condition
    is_anomaly = iso_forest.predict(live_features)[0] == -1 
    
    # Clip bounds for realistic AQI range
    final_aqi = int(max(50, min(predicted_aqi, 500)))

    # Console logging for Tech Leads/Judges
    if is_anomaly:
        print(f"⚠️ [AI WARNING] Rare extreme environmental conditions detected! (Wind: {wind_speed}m/s, Speed: {current_speed}km/h)")

    return final_aqi

# Example usage for testing
if __name__ == "__main__":
    test_weather = {"wind_speed": 1.0}
    test_traffic = {"current_speed": 12.0, "free_flow_speed": 40.0}
    
    print("Testing ML Engine...")
    result = calculate_hyperlocal_aqi(test_weather, test_traffic)
    print(f"Test Input -> AI Predicted AQI: {result}")