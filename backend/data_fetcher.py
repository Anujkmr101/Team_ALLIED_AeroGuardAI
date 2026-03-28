import os
from dotenv import load_dotenv
import requests
import ee  # ADDED: Google Earth Engine

# ==========================================
# 1. ENVIRONMENT SETUP & SECURITY
# ==========================================
env_path = os.path.join(os.path.dirname(__file__), ".env")
# Load environment variables FIRST
load_dotenv(dotenv_path=env_path)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
WAQI_API_KEY = os.getenv("WAQI_API_KEY") # The new CPCB Hardware API Key
GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID") # Optional: Your Google Cloud Project ID for GEE

# Debug check (Printing Boolean instead of raw keys to prevent leak during live demo)
print("Looking for .env at:", env_path)
print("OpenWeather Key Loaded:", bool(OPENWEATHER_API_KEY))
print("TomTom Key Loaded:", bool(TOMTOM_API_KEY))
print("WAQI (Hardware) Key Loaded:", bool(WAQI_API_KEY))

# --- Initialize Google Earth Engine ---
gee_initialized = False
try:
    if GEE_PROJECT_ID:
        ee.Initialize(project=GEE_PROJECT_ID)
    else:
        ee.Initialize()
    gee_initialized = True
    print("Google Earth Engine Initialized: True")
except Exception as e:
    print("\n⚠️ GEE Initialization failed! Ensure you run 'ee.Authenticate()' in your terminal once.")
    print(f"Error: {e}\n")


# ==========================================
# 2. THE API FETCHERS (HINA'S NODE)
# ==========================================
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


def get_real_hardware_aqi(lat: float, lon: float) -> dict:
    """
    Fetch real-time AQI from the nearest physical CPCB hardware sensor using WAQI.
    """
    if not WAQI_API_KEY:
        return {"error": "WAQI API key missing in .env"}

    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "ok":
            return {
                "sensor_aqi": data["data"]["aqi"],
                "station_name": data["data"]["city"]["name"]
            }
        else:
            return {"error": "Sensor station offline or not found."}
    except requests.exceptions.RequestException as e:
        return {"error": f"WAQI API request failed: {e}"}

# --- ADDED: SATELLITE DATA FETCHER ---
def get_satellite_no2(lat: float, lon: float, buffer_meters: int = 1000) -> dict:
    """
    Fetch satellite NO2 column number density from Sentinel-5P via Google Earth Engine.
    Useful as a static/historical baseline feature for the Forecasting Engine.
    """
    if not gee_initialized:
        return {"error": "Google Earth Engine not initialized."}

    try:
        # Create a region around the coordinates
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(buffer_meters)

        # Sentinel-5P NO2 collection (latest available day)
        collection = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2')
                      .select('NO2_column_number_density')
                      .filterBounds(region)
                      .sort('system:time_start', False)
                      .first())

        # Extract the mean value for the buffered region
        mean_dict = collection.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=1000
        )

        # Execute the request and return a Python dict
        result = mean_dict.getInfo()
        
        # Handle cases where data might be null due to cloud cover
        no2_val = result.get('NO2_column_number_density')
        if no2_val is not None:
            return {"satellite_no2_density": no2_val}
        else:
            return {"error": "No NO2 data available for this region today (likely cloud cover)."}

    except Exception as e:
        return {"error": f"GEE API request failed: {e}"}

# ==========================================
# 3. SYSTEM TEST (Run this file directly to test)
# ==========================================
if __name__ == "__main__":
    # Test Coordinates: Connaught Place, Delhi
    test_lat = 28.6304
    test_lon = 77.2177
    
    print("\n--- INITIATING API NODE TEST ---")
    
    print("\nFetching Live Weather...")
    weather_data = get_live_weather(test_lat, test_lon)
    print(weather_data)

    print("\nFetching Live Traffic...")
    traffic_data = get_live_traffic(test_lat, test_lon)
    print(traffic_data)
    
    print("\nFetching Real Hardware Sensor (CPCB) Data...")
    hardware_data = get_real_hardware_aqi(test_lat, test_lon)
    print(hardware_data)
    
    print("\nFetching Satellite NO2 Data (Sentinel-5P)...")
    satellite_data = get_satellite_no2(test_lat, test_lon)
    print(satellite_data)
    
    print("\n--- TEST COMPLETE ---")