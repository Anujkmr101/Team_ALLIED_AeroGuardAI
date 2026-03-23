import os
from dotenv import load_dotenv
import requests

# Debug check: confirm .env path and content
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("Looking for .env at:", env_path)
print("Exists?", os.path.exists(env_path))

print("Raw .env content:")
with open(env_path, "r") as f:
    print(f.read())

# Load environment variables
load_dotenv(dotenv_path=env_path)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

print("Weather Key:", OPENWEATHER_API_KEY)
print("Traffic Key:", TOMTOM_API_KEY)

def get_live_weather(lat: float, lon: float) -> dict:
    """
    Fetch real-time wind speed (m/s) and temperature (°C) from OpenWeatherMap API.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "wind_speed": data["wind"]["speed"]
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Weather API request failed: {e}"}


def get_live_traffic(lat: float, lon: float) -> dict:
    """
    Fetch real-time traffic congestion data from TomTom Traffic API.
    """
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={lat},{lon}&key={TOMTOM_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "current_speed": data["flowSegmentData"]["currentSpeed"],
            "free_flow_speed": data["flowSegmentData"]["freeFlowSpeed"],
            "congestion_level": data["flowSegmentData"]["confidence"]
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Traffic API request failed: {e}"}
     # ==========================================
# SYSTEM TEST (Run this file directly to test)
#  # ==========================================
if __name__ == "__main__":
    # Test Coordinates: Connaught Place, Delhi
    test_lat = 28.6304
    test_lon = 77.2177
    print("Fetching Live Weather...")
    weather_data = get_live_weather(test_lat, test_lon)
    print(weather_data)

    print("\nFetching Live Traffic...")
    traffic_data = get_live_traffic(test_lat, test_lon)
    print(traffic_data)