import sys
import os

# Python ko bata rahe hain ki main project folder kahan hai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import sqlite3
import random
# ... (iske niche tera baaki saara purana code aayega) ...
import streamlit as st
import pandas as pd
import sqlite3
import random
import time

# Team members ke modules import kar rahe hain (The Magic Trick!)
from backend.data_fetcher import get_live_weather, get_live_traffic
from backend.ml_engine import calculate_hyperlocal_aqi
from database.db_manager import evaluate_and_log_sensor, DB_NAME

# ==========================================
# 1. PAGE SETUP (Enterprise Vibe)
# ==========================================
st.set_page_config(page_title="AeroGuard Central Command", layout="wide")

st.markdown("""
    <style>
    .system-header { font-size: 26px; font-weight: 600; color: #E0E0E0; }
    .status-online { color: #4CAF50; font-weight: 500; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="system-header">AeroGuard Central Command</p>', unsafe_allow_html=True)
st.markdown("Hyper-Local Telemetry & Node Integrity Validation System")

# ==========================================
# 2. SIDEBAR
# ==========================================
st.sidebar.markdown("### Navigation")
app_mode = st.sidebar.radio("", ["Live Telemetry Engine", "Node Integrity Audit (B2G)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Sub-System Status")
st.sidebar.markdown("Hina API Node: <span class='status-online'>[ ONLINE ]</span>", unsafe_allow_html=True)
st.sidebar.markdown("Jatin AI Core: <span class='status-online'>[ ONLINE ]</span>", unsafe_allow_html=True)
st.sidebar.markdown("Jiya Sec-Vault: <span class='status-online'>[ ONLINE ]</span>", unsafe_allow_html=True)

# ==========================================
# 3. VIEW 1: LIVE AI ENGINE (Connecting Hina + Jatin)
# ==========================================
if app_mode == "Live Telemetry Engine":
    st.subheader("Real-Time Environmental Ingestion")
    
    # Coordinates for Connaught Place, Delhi
    lat, lon = 28.6304, 77.2177
    
    if st.button("Run Live Telemetry & AI Prediction"):
        with st.spinner("Fetching Live APIs and running XGBoost logic..."):
            
            # 1. HINA KA KAAM (Fetching Data)
            weather_data = get_live_weather(lat, lon)
            traffic_data = get_live_traffic(lat, lon)
            
            # Displaying Hina's Data
            col1, col2 = st.columns(2)
            with col1:
                st.info("OpenWeather API (Hina)")
                st.json(weather_data)
            with col2:
                st.info("TomTom Traffic API (Hina)")
                st.json(traffic_data)
            
            # 2. JATIN KA KAAM (Running AI)
            if "error" not in weather_data and "error" not in traffic_data:
                ai_aqi = calculate_hyperlocal_aqi(weather_data, traffic_data)
                
                st.markdown("---")
                st.subheader("Jatin's AI Engine Output")
                st.metric(label="Calculated Hyper-Local AQI (Trapped Emissions)", value=ai_aqi)
                
                # 3. JIYA KA KAAM (Security Logging)
                # Let's assume a physical sensor is lying and showing 60 (Fake Safe)
                fake_sensor_aqi = random.randint(50, 70) 
                
                st.markdown("---")
                st.subheader("Jiya's Cybersecurity Validator")
                st.write(f"Physical Sensor is reporting: **{fake_sensor_aqi}**")
                
                # Sending to Jiya's Database
                status = evaluate_and_log_sensor("Connaught Place, Delhi", fake_sensor_aqi, ai_aqi)
                
                if "CRITICAL" in status:
                    st.error(f"SYSTEM ACTION: {status}")
                else:
                    st.success(f"SYSTEM ACTION: {status}")
            else:
                st.error("API Connection Failed. Please check API Keys in .env file.")

# ==========================================
# 4. VIEW 2: DATABASE AUDIT DASHBOARD (Reading Jiya's DB)
# ==========================================
elif app_mode == "Node Integrity Audit (B2G)":
    st.subheader("Secure Database Logs (Government View)")
    st.caption("Fetching immutable records from SQLite Vault...")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        # Fetch data from Jiya's table
        df = pd.read_sql_query("SELECT * FROM spoofing_alerts ORDER BY timestamp DESC", conn)
        conn.close()
        
        if not df.empty:
            # Color code critical alerts
            def highlight_anomalies(row):
                if 'CRITICAL' in row['status']:
                    return ['background-color: rgba(217, 83, 79, 0.15)'] * len(row)
                return [''] * len(row)
            
            st.dataframe(df.style.apply(highlight_anomalies, axis=1), use_container_width=True)
        else:
            st.info("No audit logs found yet. Run the Telemetry Engine first.")
            
    except Exception as e:
        st.error(f"Database error: {e}. Make sure Jiya's database is initialized.")