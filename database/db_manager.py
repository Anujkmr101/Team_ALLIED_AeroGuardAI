import sqlite3
import hashlib
import os
from datetime import datetime
from contextlib import closing

# ==========================================
# 1. THE ZERO-TRUST VAULT SETUP
# ==========================================
# Absolute path: Database humesha 'database' folder mein hi banegi
DB_NAME = os.path.join(os.path.dirname(__file__), "aeroguard_secure.db")

def initialize_database():
    """
    Initializes the SQLite database with a ZERO-TRUST architecture.
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
                    timestamp TEXT NOT NULL,
                    data_hash TEXT NOT NULL
                )
            """)
        conn.commit()

def generate_tamper_proof_hash(location, sensor_aqi, ai_aqi, status, timestamp):
    """
    Generates a SHA-256 cryptographic hash for the log entry.
    """
    record_string = f"{location}|{sensor_aqi}|{ai_aqi}|{status}|{timestamp}"
    return hashlib.sha256(record_string.encode('utf-8')).hexdigest()

def evaluate_and_log_sensor(location: str, sensor_aqi: float, ai_predicted_aqi: float) -> str:
    """
    Compares physical sensor AQI with AI-predicted AQI and logs it securely.
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
    record_hash = generate_tamper_proof_hash(location, sensor_aqi, ai_predicted_aqi, status, timestamp)

    # 🛠️ THE STREAMLIT FIX: Force table creation right before insertion
    initialize_database()

    # Secure DB insertion using parameterized query
    try:
        with sqlite3.connect(DB_NAME) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("""
                    INSERT INTO spoofing_alerts 
                    (location, sensor_aqi, ai_predicted_aqi, status, timestamp, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (location.strip(), sensor_aqi, ai_predicted_aqi, status, timestamp, record_hash))
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}")

    return status

# Initialize DB on script load just in case
initialize_database()

# Example usage (Test run)
if __name__ == "__main__":
    result = evaluate_and_log_sensor("Delhi Sector 21", 80, 140)
    print("Status:", result)