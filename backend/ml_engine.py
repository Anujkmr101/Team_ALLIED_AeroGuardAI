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

    Parameters
    ----------
    weather_data : dict
        Dictionary containing weather information.
        Expected keys: 'wind_speed' (float, in m/s)

    traffic_data : dict
        Dictionary containing traffic information.
        Expected keys: 'traffic_delay' (float, arbitrary scale)

    Returns
    -------
    ai_predicted_aqi : int
        Predicted AQI value based on heuristic rules.
    """

    # Extract values safely with defaults
    wind_speed = weather_data.get("wind_speed", 0.0)
    traffic_delay = traffic_data.get("traffic_delay", 0.0)

    # Heuristic logic:
    # - Low wind speed (< 2 m/s) + high traffic delay → trapped emissions → high AQI
    # - Otherwise → normal AQI
    if wind_speed < 2.0 and traffic_delay > 5.0:
        ai_predicted_aqi = 275  # Severe AQI due to trapped pollution
    elif wind_speed < 2.0 and traffic_delay > 2.0:
        ai_predicted_aqi = 225  # Moderately high AQI
    elif wind_speed >= 5.0:
        ai_predicted_aqi = 75   # Good dispersion, normal AQI
    else:
        ai_predicted_aqi = 100  # Default moderate AQI

    return int(ai_predicted_aqi)


# Example usage (for quick testing, remove in production):
if __name__ == "__main__":
    sample_weather = {"wind_speed": 1.5}
    sample_traffic = {"traffic_delay": 6.0}
    result = calculate_hyperlocal_aqi(sample_weather, sample_traffic)
    print(f"Predicted AQI: {result}")

