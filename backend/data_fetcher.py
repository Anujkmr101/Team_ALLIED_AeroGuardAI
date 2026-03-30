import os
from dotenv import load_dotenv
import requests
import ee

# ==========================================
# 1. ENVIRONMENT SETUP & SECURITY
# ==========================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(BASE_DIR, ".env")

load_dotenv(env_path)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
WAQI_API_KEY = os.getenv("WAQI_API_KEY")
GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")

print("ENV PATH:", env_path)
print("OpenWeather Key Loaded:", bool(OPENWEATHER_API_KEY))
print("TomTom Key Loaded:", bool(TOMTOM_API_KEY))
print("WAQI Key Loaded:", bool(WAQI_API_KEY))
print("GEE Project ID:", GEE_PROJECT_ID)

# ==========================================
# 2. GEE INITIALIZATION
# ==========================================
gee_initialized = False
try:
    if GEE_PROJECT_ID:
        ee.Initialize(project=GEE_PROJECT_ID)
    else:
        ee.Initialize()
    gee_initialized = True
    print("GEE Initialized: True")
except Exception as e:
    print("⚠️ GEE Initialization failed:", e)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def safe_request(url):
    """Retry-safe request handler"""
    for _ in range(2):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            last_error = str(e)
    return {"error": last_error}


def is_valid(data):
    return isinstance(data, dict) and "error" not in data


# ==========================================
# 4. API FETCHERS
# ==========================================

def get_live_weather(lat: float, lon: float) -> dict:
    if not OPENWEATHER_API_KEY:
        return {"error": "OpenWeather API key missing"}

    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    data = safe_request(url)

    if not is_valid(data) or "main" not in data:
        return {"error": f"Invalid weather response: {data}"}

    return {
        "temperature": data["main"]["temp"],
        "wind_speed": data["wind"]["speed"]
    }


def get_live_traffic(lat: float, lon: float) -> dict:
    if not TOMTOM_API_KEY:
        return {"error": "TomTom API key missing"}

    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={lat},{lon}&key={TOMTOM_API_KEY}"
    
    data = safe_request(url)

    if not is_valid(data) or "flowSegmentData" not in data:
        return {"error": f"Invalid traffic response: {data}"}

    flow = data["flowSegmentData"]

    return {
        "current_speed": flow.get("currentSpeed"),
        "free_flow_speed": flow.get("freeFlowSpeed"),
        "congestion_level": flow.get("confidence")
    }


def get_real_hardware_aqi(lat: float, lon: float) -> dict:
    if not WAQI_API_KEY:
        return {"error": "WAQI API key missing"}

    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
    
    data = safe_request(url)

    if not is_valid(data) or data.get("status") != "ok":
        return {"error": f"WAQI error: {data}"}

    return {
        "sensor_aqi": data["data"].get("aqi"),
        "station_name": data["data"]["city"].get("name")
    }


def get_satellite_no2(lat: float, lon: float, buffer_meters: int = 1000) -> dict:
    if not gee_initialized:
        return {"error": "GEE not initialized"}

    try:
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(buffer_meters)

        collection = (
            ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2')
            .select('NO2_column_number_density')
            .filterBounds(region)
            .sort('system:time_start', False)
            .first()
        )

        mean_dict = collection.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=1000
        )

        result = mean_dict.getInfo()
        value = result.get('NO2_column_number_density')

        if value is None:
            return {"error": "No NO2 data (cloud cover likely)"}

        return {"satellite_no2_density": value}

    except Exception as e:
        return {"error": f"GEE request failed: {e}"}


# ==========================================
# 5. TEST BLOCK
# ==========================================
if __name__ == "__main__":
    lat, lon = 28.6304, 77.2177

    print("\n--- TESTING APIs ---")

    print("\nWeather:", get_live_weather(lat, lon))
    print("\nTraffic:", get_live_traffic(lat, lon))
    print("\nAQI:", get_real_hardware_aqi(lat, lon))
    print("\nSatellite NO2:", get_satellite_no2(lat, lon))

    print("\n--- DONE ---")