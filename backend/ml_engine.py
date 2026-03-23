# ml_engine.py
"""
AeroGuard AI - Hyperlocal AQI Prediction Engine
------------------------------------------------
This module provides a prototype function to estimate AQI values
based on weather and traffic conditions, specifically modeling
the 'Street-Canyon Effect' where pollution gets trapped between buildings.

Author: Hackathon Team
"""

def calculate_hyperlocal_aqi(weather_data, traffic_data):
    """
    Calculate AI-predicted AQI based on weather and traffic inputs.
    """
    # Extract weather values safely
    wind_speed = weather_data.get("wind_speed", 5.0) # Default to 5.0 (safe) if missing
    
    # Bridge the gap with Hina's data format
    current_speed = traffic_data.get("current_speed", 40.0)
    free_flow_speed = traffic_data.get("free_flow_speed", 40.0)
    
    # Calculate Traffic Congestion (Speed Drop)
    # Agar free flow 50 hai aur current 10 hai, toh speed_drop 40 hoga (High Traffic)
    speed_drop = free_flow_speed - current_speed
    
    # Heuristic logic:
    # - Low wind speed (< 2.5 m/s) + High traffic jam (Speed drop > 20) → trapped emissions → high AQI
    if wind_speed < 2.5 and speed_drop > 20:
        ai_predicted_aqi = 285  # Severe AQI (Gas Chamber Effect)
    elif wind_speed < 2.5 and speed_drop > 10:
        ai_predicted_aqi = 210  # Moderately high AQI
    elif wind_speed >= 4.0:
        ai_predicted_aqi = 65   # Good dispersion, normal AQI
    else:
        ai_predicted_aqi = 120  # Default moderate AQI

    return int(ai_predicted_aqi)

# Example usage (Testing with Hina's format):
if __name__ == "__main__":
    sample_weather = {"wind_speed": 1.2}
    sample_traffic = {"current_speed": 15.0, "free_flow_speed": 50.0} # 35 km/h drop!
    result = calculate_hyperlocal_aqi(sample_weather, sample_traffic)
    print(f"Predicted AQI: {result} (Expected: 285 because of slow wind & high traffic)")

