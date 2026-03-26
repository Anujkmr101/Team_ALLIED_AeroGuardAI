import sys
import os
import time 
import random
import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Python ko bata rahe hain ki main project folder kahan hai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.data_fetcher import get_live_weather, get_live_traffic, get_real_hardware_aqi
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
    .health-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border-left: 5px solid; margin-top: 10px; }
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
# HEALTH LOGIC HELPER FUNCTION
# ==========================================
def get_health_risk(aqi):
    if aqi <= 50:
        return "✅ Safe for All", "Unlimited", "Not Required", "#00E400"
    elif aqi <= 100:
        return "⚠️ Moderate (Sensitive groups take care)", "4-6 Hours", "Optional", "#FFFF00"
    elif aqi <= 200:
        return "❌ UNSAFE for Asthma/Kids", "Max 2 Hours", "Recommended", "#FF7E00"
    elif aqi <= 300:
        return "🚨 DANGER for All", "Max 45 Mins", "N95 Mandatory", "#FF0000"
    else:
        return "☠️ HAZARDOUS (Evacuate/Indoors)", "< 15 Mins", "Strict N95/Respirator", "#8F3F97"

# ==========================================
# 3. VIEW 1: LIVE AI ENGINE
# ==========================================
if app_mode == "Live Telemetry Engine":
    st.subheader("Real-Time Environmental Ingestion")
    
    # 🗺️ FIELD TEST ZONES
    TEST_LOCATIONS = {
        "Connaught Place (Street Canyon)": (28.6304, 77.2177),
        "ITO Crossing (Heavy Traffic)": (28.6276, 77.2404),
        "Anand Vihar (Industrial/Extreme)": (28.6469, 77.3160),
        "Lodhi Gardens (Clean Baseline)": (28.5866, 77.2210),
        "Sonipat (Home Base)": (28.9931, 77.0151) 
    }
    
    selected_zone = st.selectbox("📍 Select Field Test Zone:", list(TEST_LOCATIONS.keys()))
    lat, lon = TEST_LOCATIONS[selected_zone]
    
    if st.button(f"▶️ Run Telemetry for {selected_zone.split('(')[0].strip()}", type="primary"):
        with st.spinner("Initiating Satellite & Sensor Telemetry..."):
            time.sleep(1) 
            
            weather_data = get_live_weather(lat, lon)
            traffic_data = get_live_traffic(lat, lon)
            
            if "error" not in weather_data and "error" not in traffic_data:
                
                # --- TIER 1: TELEMETRY METRIC CARDS ---
                st.markdown("### 📡 Live Telemetry Feed")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(label="🌡️ Surface Temp", value=f"{weather_data.get('temperature', 0)} °C")
                with col2:
                    st.metric(label="💨 Wind Dispersion", value=f"{weather_data.get('wind_speed', 0)} m/s")
                with col3:
                    st.metric(label="🚗 Current Speed", value=f"{traffic_data.get('current_speed', 0)} km/h", delta="- Congested", delta_color="inverse")
                with col4:
                    st.metric(label="🚦 Congestion Level", value=f"{traffic_data.get('congestion_level', 0)} / 5")

                st.markdown("---")
                
                # --- TIER 2: THE AI CORE & EXPLAINABLE AI ---
                st.markdown("### 🧠 AI Hyper-Local Analysis & Explainable AI")
                ai_aqi = calculate_hyperlocal_aqi(weather_data, traffic_data)
                
                col_chart, col_info = st.columns([1, 1])
                
                with col_chart:
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = ai_aqi,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "AI Predicted AQI (Street-Level)", 'font': {'size': 16}},
                        gauge = {
                            'axis': {'range': [None, 500], 'tickwidth': 1, 'tickcolor': "darkblue"},
                            'bar': {'color': "rgba(255, 255, 255, 0.5)"},
                            'bgcolor': "rgba(0,0,0,0)",
                            'steps': [
                                {'range': [0, 50], 'color': "#00E400"},
                                {'range': [50, 100], 'color': "#FFFF00"},
                                {'range': [100, 200], 'color': "#FF7E00"},
                                {'range': [200, 300], 'color': "#FF0000"},
                                {'range': [300, 500], 'color': "#8F3F97"}
                            ]
                        }
                    ))
                    fig.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col_info:
                    real_sensor_data = get_real_hardware_aqi(lat, lon)
                    if "error" not in real_sensor_data:
                        station_name = real_sensor_data['station_name']
                        actual_hardware_aqi = real_sensor_data['sensor_aqi']
                        st.info(f"📍 **Physical Sensor ({station_name}):** AQI `{actual_hardware_aqi}`")
                    else:
                        station_name = f"Hardware near {selected_zone.split('(')[0].strip()}"
                        actual_hardware_aqi = 60 
                        st.warning(f"⚠️ **Physical Sensor (Fallback):** AQI `{actual_hardware_aqi}`")
                        
                    st.markdown("#### 🔍 Explainable AI (Why this prediction?)")
                    speed_drop = traffic_data.get('free_flow_speed', 40) - traffic_data.get('current_speed', 40)
                    wind = weather_data.get('wind_speed', 0)
                    
                    reason_traffic = f"Traffic congestion (Speed drop: {speed_drop:.1f} km/h) is trapping emissions." if speed_drop > 10 else "Traffic is flowing smoothly."
                    reason_wind = f"Low wind ({wind}m/s) is creating a Street Canyon Effect." if wind < 2.5 else f"Good wind dispersion ({wind}m/s)."
                    
                    st.write(f"- **Traffic Factor:** {reason_traffic}")
                    st.write(f"- **Weather Factor:** {reason_wind}")
                    
                    difference = actual_hardware_aqi - ai_aqi
                    if difference > 50:
                        st.info(f"💡 **Mismatch Insight:** Sensor is {int(difference)} points higher. Our AI isolates local traffic emissions; the excess is likely background/industrial pollution.")
                    elif difference < -50:
                        st.error(f"🚨 **Security Insight:** The sensor is reading artificially lower than the physics-based AI calculation. Potential Hardware Masking or Spoofing!")

                # --- GAP 3 FIX: HEALTH RISK ENGINE (NEW) ---
                asthma_status, time_limit, mask_status, hex_color = get_health_risk(ai_aqi)
                st.markdown(f"""
                <div class="health-card" style="border-color: {hex_color};">
                    <h4 style="margin-top:0px; color:{hex_color};">🚑 Consumer Health Risk & Exposure Engine</h4>
                    <table style="width:100%; text-align:left;">
                        <tr>
                            <td><strong>Vulnerable Groups (Asthma):</strong></td>
                            <td>{asthma_status}</td>
                        </tr>
                        <tr>
                            <td><strong>Time-to-Harm (Delivery Riders):</strong></td>
                            <td>⏳ {time_limit} before acute respiratory stress</td>
                        </tr>
                        <tr>
                            <td><strong>Protection Gear:</strong></td>
                            <td>😷 {mask_status}</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")
                
                # --- TIER 3: JIYA KA KAAM (Real Hardware Cyber Vault) ---
                st.markdown("### 🛡️ Zero-Trust Node Integrity Vault (SHA-256)")
                
                is_sensor_hacked = st.checkbox("🧨 Simulate Hardware Hack (Inject Fake 'Safe' AQI Data)", value=False)
                
                if is_sensor_hacked:
                    reporting_aqi = random.randint(40, 60)
                    st.error(f"🚨 HACK MODE ACTIVE: Hardware tampered! Reporting `{reporting_aqi}` instead of `{actual_hardware_aqi}`.")
                else:
                    reporting_aqi = actual_hardware_aqi
                
                status = evaluate_and_log_sensor(station_name, reporting_aqi, ai_aqi)
                
                if "CRITICAL" in status:
                    st.error(f"⚠️ {status} | Massive discrepancy detected between AI ({ai_aqi}) and reporting node ({reporting_aqi}). Cryptographic log generated.")
                else:
                    st.success(f"✅ {status} | Hardware node aligns with AI predictions. Cryptographic log generated.")
                    
            else:
                st.error("API Connection Failed. Please check API Keys in .env file.")

# ==========================================
# 4. VIEW 2: DATABASE AUDIT DASHBOARD 
# ==========================================
elif app_mode == "Node Integrity Audit (B2G)":
    st.subheader("Secure Database Logs (Government View)")
    st.caption("Fetching immutable records from SQLite Vault...")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM spoofing_alerts ORDER BY timestamp DESC", conn)
        conn.close()
        
        if not df.empty:
            def highlight_anomalies(row):
                if 'CRITICAL' in row['status']:
                    return ['background-color: rgba(217, 83, 79, 0.15)'] * len(row)
                return [''] * len(row)
            
            st.dataframe(df.style.apply(highlight_anomalies, axis=1), use_container_width=True)
        else:
            st.info("No audit logs found yet. Run the Telemetry Engine first.")
            
    except Exception as e:
        st.error(f"Database error: {e}. Make sure Jiya's database is initialized.")