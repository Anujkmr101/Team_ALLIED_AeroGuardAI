import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

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