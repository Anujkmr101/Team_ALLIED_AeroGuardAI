import sqlite3
from datetime import datetime
from contextlib import closing

# Database file
DB_NAME = "aeroguard_secure.db"


def initialize_database():
    """
    Initializes the SQLite database and creates the spoofing_alerts table if it does not exist.
    """
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spoofing_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    sensor_aqi REAL NOT NULL,
                    ai_predicted_aqi REAL NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
        conn.commit()


def evaluate_and_log_sensor(location: str, sensor_aqi: float, ai_predicted_aqi: float) -> str:
    """
    Compares physical sensor AQI with AI-predicted AQI to detect spoofing anomalies.
    
    Parameters:
        location (str): Sensor location
        sensor_aqi (float): AQI reported by physical sensor
        ai_predicted_aqi (float): AQI predicted by AI model
    
    Returns:
        str: Alert status message
    """

    # Input validation (basic hardening)
    if not isinstance(location, str) or not location.strip():
        raise ValueError("Invalid location input")

    if not (isinstance(sensor_aqi, (int, float)) and isinstance(ai_predicted_aqi, (int, float))):
        raise ValueError("AQI values must be numeric")

    if sensor_aqi < 0 or ai_predicted_aqi < 0:
        raise ValueError("AQI values cannot be negative")

    # Security Logic
    if (ai_predicted_aqi - sensor_aqi) > 50:
        status = "🚨 CRITICAL SPOOFING ANOMALY"
    else:
        status = "✅ VERIFIED"

    timestamp = datetime.utcnow().isoformat()

    # Secure DB insertion using parameterized query
    try:
        with sqlite3.connect(DB_NAME) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("""
                    INSERT INTO spoofing_alerts 
                    (location, sensor_aqi, ai_predicted_aqi, status, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (location.strip(), sensor_aqi, ai_predicted_aqi, status, timestamp))
            conn.commit()
    except sqlite3.Error as e:
        # In production, replace with proper logging system
        raise RuntimeError(f"Database error: {e}")

    return status


# Initialize DB on script load (safe for hackathon scope)
initialize_database()


# Example usage (can be removed in production)
if __name__ == "__main__":
    result = evaluate_and_log_sensor("Delhi Sector 21", 80, 140)
    print("Status:", result)