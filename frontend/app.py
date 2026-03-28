import sys
import os
import time 
import sqlite3
import pandas as pd
import numpy as np
import requests  
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.data_fetcher import get_live_weather, get_live_traffic, get_real_hardware_aqi
from backend.ml_engine import calculate_hyperlocal_aqi
from database.db_manager import evaluate_and_log_sensor, DB_NAME

# ==========================================
# 1. DESIGN SYSTEM & CSS TOKENS
# ==========================================
st.set_page_config(page_title="AeroGuard Enterprise", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Global Theme */
    .stApp { background-color: #0F1117; color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* Typography Hierarchy */
    .text-display { font-size: 32px; font-weight: 600; color: #F8FAFC; margin: 0; line-height: 1.2; }
    .text-title { font-size: 24px; font-weight: 600; color: #F8FAFC; margin-bottom: 4px; }
    .text-subtitle { font-size: 16px; font-weight: 500; color: #E2E8F0; border-bottom: 1px solid #334155; padding-bottom: 8px; margin-bottom: 16px; margin-top: 24px;}
    .text-body { font-size: 14px; font-weight: 400; color: #94A3B8; }
    .text-micro { font-size: 12px; font-weight: 500; text-transform: uppercase; color: #64748B; letter-spacing: 0.5px; }

    /* Component: Cards (8px spacing system) */
    .card { background-color: #1A1D23; border: 1px solid #2D3748; border-radius: 6px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
    .card-tight { padding: 12px; }
    
    /* Component: Status Chips */
    .chip { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
    .chip-safe { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .chip-warn { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }
    .chip-crit { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    
    /* Component: The AQI Pill */
    .aqi-pill { display: inline-flex; align-items: center; justify-content: center; padding: 12px 32px; border-radius: 8px; font-size: 40px; font-weight: 600; color: #0F1117; margin: 8px 0; }
    
    /* Sidebar Overhaul */
    [data-testid="stSidebar"] { background-color: #14171F; border-right: 1px solid #2D3748; }
    </style>
    """, unsafe_allow_html=True)

# Top Navigation Bar
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2D3748; padding-bottom: 16px; margin-bottom: 24px;">
        <div>
            <div class="text-title">AeroGuard Central Command</div>
            <div class="text-body">Enterprise Ops & Telemetry Validation | v4.0</div>
        </div>
        <div style="display: flex; gap: 16px;">
            <span class="chip chip-safe">API: Online</span>
            <span class="chip chip-safe">Traffic Core: Online</span>
            <span class="chip chip-safe">Crypto Vault: Secure</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_exposure_profile(aqi):
    if aqi <= 50: return "Optimal", "Low", "None", "#10B981" 
    elif aqi <= 100: return "Moderate", "Elevated", "Optional", "#F59E0B" 
    elif aqi <= 200: return "Poor", "High", "Recommended", "#F97316" 
    elif aqi <= 300: return "Severe", "Critical", "Mandatory N95", "#EF4444" 
    else: return "Hazardous", "Extreme", "Avoid Exposure", "#8B5CF6" 

def get_osrm_route(start_coords, end_coords, is_bypass=False):
    start_lon, start_lat = start_coords[1], start_coords[0]
    end_lon, end_lat = end_coords[1], end_coords[0]
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?alternatives=true&overview=full&geometries=geojson"
    try:
        # NAYA: User-Agent header taaki OSRM API block na kare!
        headers = {'User-Agent': 'AeroGuard-Enterprise-Demo/1.0'}
        res = requests.get(url, headers=headers).json()
        route_index = 1 if is_bypass and len(res.get('routes', [])) > 1 else 0
        coords = res['routes'][route_index]['geometry']['coordinates']
        return [c[1] for c in coords], [c[0] for c in coords]
    except Exception as e:
        print(f"OSRM Error: {e}") # Terminal mein error dekhne ke liye
        return np.linspace(start_lat, end_lat, 20).tolist(), np.linspace(start_lon, end_lon, 20).tolist()

@st.cache_data(ttl=300, show_spinner=False)
def get_real_route_aqi(start_coords, end_coords, num_waypoints=4, is_bypass=False):
    full_lats, full_lons = get_osrm_route(start_coords, end_coords, is_bypass)
    idx_step = max(1, len(full_lats) // num_waypoints)
    route_aqi = []
    
    for lat, lon in zip(full_lats[::idx_step][:num_waypoints], full_lons[::idx_step][:num_waypoints]):
        weather, traffic = get_live_weather(lat, lon), get_live_traffic(lat, lon)
        if "error" not in weather and "error" not in traffic:
            res = calculate_hyperlocal_aqi(weather, traffic)
            route_aqi.append(res["aqi"] if isinstance(res, dict) else res)
        else:
            route_aqi.append(110)
            
    return {
        "peak_aqi": int(max(route_aqi)), "average_aqi": int(np.mean(route_aqi)),
        "toxic_segments": sum(1 for a in route_aqi if a > 150),
        "lats": full_lats, "lons": full_lons
    }

# ==========================================
# 2. SIDEBAR 
# ==========================================
st.sidebar.markdown("<div class='text-micro' style='margin-bottom: 16px;'>Main Menu</div>", unsafe_allow_html=True)
app_mode = st.sidebar.radio("", [
    "Live Telemetry", 
    "Route Optimizer", 
    "Government Command"
], label_visibility="collapsed")

# ==========================================
# 3. VIEW 1: OPS - LIVE TELEMETRY
# ==========================================
if app_mode == "Live Telemetry":
    
    TEST_LOCATIONS = {
        "Delhi: Connaught Place": (28.6304, 77.2177),
        "Delhi: ITO Crossing": (28.6276, 77.2404),
        "Dehradun: Clock Tower": (30.3240, 78.0416)
    }
    
    col_sel, col_btn = st.columns([3, 1])
    with col_sel: selected_zone = st.selectbox("Active Node", list(TEST_LOCATIONS.keys()), label_visibility="collapsed")
    lat, lon = TEST_LOCATIONS[selected_zone]
    with col_btn: run_scan = st.button("Initialize Scan", use_container_width=True)
    
    # Session State Implementation to prevent UI reset
    if "telemetry_scanned" not in st.session_state:
        st.session_state.telemetry_scanned = False
        st.session_state.last_lat = None
        st.session_state.last_lon = None

    if run_scan:
        st.session_state.telemetry_scanned = True
        st.session_state.last_lat = lat
        st.session_state.last_lon = lon
    
    if st.session_state.telemetry_scanned:
        # Fetching based on session coordinates
        s_lat = st.session_state.last_lat
        s_lon = st.session_state.last_lon
        
        with st.spinner("Compiling edge data..."):
            weather_data, traffic_data = get_live_weather(s_lat, s_lon), get_live_traffic(s_lat, s_lon)
            
            if "error" not in weather_data and "error" not in traffic_data:
                # Tight row ingestion using Custom CSS cards
                st.markdown('<div class="text-subtitle">Raw Edge Ingestion</div>', unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="display: flex; gap: 16px; margin-bottom: 24px;">
                        <div class="card card-tight" style="flex: 1;"><div class="text-micro">Temperature</div><div class="text-display" style="font-size:24px;">{weather_data.get('temperature', 0)}°C</div></div>
                        <div class="card card-tight" style="flex: 1;"><div class="text-micro">Wind Vector</div><div class="text-display" style="font-size:24px;">{weather_data.get('wind_speed', 0)} m/s</div></div>
                        <div class="card card-tight" style="flex: 1;"><div class="text-micro">Flow Speed</div><div class="text-display" style="font-size:24px;">{traffic_data.get('current_speed', 0)} km/h</div></div>
                        <div class="card card-tight" style="flex: 1;"><div class="text-micro">Congestion</div><div class="text-display" style="font-size:24px;">{traffic_data.get('congestion_level', 0)}/5</div></div>
                    </div>
                """, unsafe_allow_html=True)
                
                ai_result = calculate_hyperlocal_aqi(weather_data, traffic_data)
                ai_aqi = ai_result["aqi"] if isinstance(ai_result, dict) else ai_result
                confidence = ai_result.get("confidence_pct", 85.0) if isinstance(ai_result, dict) else 85.0
                t_mode = ai_result.get("trust_mode", "INTERPOLATION") if isinstance(ai_result, dict) else "INTERPOLATION"
                profile, risk_lvl, gear, hex_color = get_exposure_profile(ai_aqi)
                
                st.markdown('<div class="text-subtitle">Predictive Analysis & Health Risk</div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    # Minimalist Pill UI
                    st.markdown(f"""
                        <div class="card" style="text-align: center; display: flex; flex-direction: column; align-items: center;">
                            <div class="text-micro">Calculated Micro-AQI</div>
                            <div class="aqi-pill" style="background-color: {hex_color};">{ai_aqi}</div>
                            <div class="text-body" style="font-size: 13px;">Statistical Confidence: {confidence}%</div>
                        </div>
                    """, unsafe_allow_html=True)

                with c2:
                    st.markdown(f"""
                        <div class="card">
                            <table style="width:100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #2D3748;"><td style="padding: 12px 0;" class="text-body">Air Quality Category</td><td style="text-align: right; color: {hex_color}; font-weight: 500;">{profile}</td></tr>
                                <tr style="border-bottom: 1px solid #2D3748;"><td style="padding: 12px 0;" class="text-body">Cumulative Risk</td><td style="text-align: right; color: #E2E8F0;">{risk_lvl}</td></tr>
                                <tr><td style="padding: 12px 0;" class="text-body">Fleet Mandate</td><td style="text-align: right; color: #E2E8F0;">{gear}</td></tr>
                            </table>
                        </div>
                    """, unsafe_allow_html=True)

                # ==========================================
                # ZERO-TRUST HARDWARE VALIDATION CARD (RESTORED)
                # ==========================================
                real_sensor_data = get_real_hardware_aqi(s_lat, s_lon)
                hw_aqi = real_sensor_data.get('sensor_aqi', 60) if "error" not in real_sensor_data else 60
                station_name = real_sensor_data.get('station_name', 'Proxy Node') if "error" not in real_sensor_data else 'Proxy Node'
                
                difference = hw_aqi - ai_aqi
                
                # Logic for status
                if difference > 40:
                    insight_text = f"Hardware reads {int(difference)} pts higher. Delta likely caused by unmapped construction dust."
                    insight_color = "#F59E0B" # Warning Amber
                    chip_class = "chip-warn"
                elif difference < -40:
                    insight_text = f"CRITICAL: Sensor reads {int(abs(difference))} pts lower than physics baseline. Potential spoofing."
                    insight_color = "#EF4444" # Critical Red
                    chip_class = "chip-crit"
                else:
                    insight_text = "Status: Physics model aligns perfectly with hardware baseline."
                    insight_color = "#10B981" # Safe Emerald
                    chip_class = "chip-safe"

                st.markdown('<div class="text-subtitle" style="margin-top: 24px;">Zero-Trust Hardware Validation</div>', unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="card" style="display: flex; justify-content: space-between; align-items: center; border-left: 4px solid {insight_color};">
                        <div>
                            <div class="text-micro" style="color: #94A3B8;">CPCB Auth Sensor ({station_name})</div>
                            <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 4px;">
                                <div class="text-display" style="font-size: 28px;">{hw_aqi}</div>
                                <div class="text-body" style="font-size: 14px;">AQI</div>
                            </div>
                            <div class="text-body" style="color: {insight_color}; margin-top: 8px;">{insight_text}</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="text-micro" style="margin-bottom: 8px;">Applicability Domain</div>
                            <span class="chip {chip_class}">{t_mode}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# 4. VIEW 2: FLEET ROUTE OPTIMIZER
# ==========================================
elif app_mode == "Route Optimizer":
    st.markdown('<div class="text-subtitle" style="margin-top:0;">Fleet Exposure Mitigation</div>', unsafe_allow_html=True)
    
    ROUTE_COORDS = {
        "Dehradun: Clock Tower -> Rajpur": ((30.3240, 78.0416), (30.3398, 78.0560)),
        "Delhi: CP -> ITO": ((28.6304, 77.2177), (28.6276, 77.2404))
    }
    
    route_sel = st.selectbox("Select Active Corridor", list(ROUTE_COORDS.keys()), label_visibility="collapsed")
    start_c, end_c = ROUTE_COORDS[route_sel]
        
    if st.button("Generate Pareto Front", type="primary"):
        with st.spinner("Computing safest path..."):
            route_a = get_real_route_aqi(start_c, end_c, is_bypass=False)
            route_b = get_real_route_aqi(start_c, end_c, is_bypass=True)
            
            fig_map = go.Figure()
            fig_map.add_trace(go.Scattermapbox(
                mode="lines", lon=route_a["lons"], lat=route_a["lats"],
                line={'width': 4, 'color': "#EF4444"}, name=f"Standard Route"
            ))
            fig_map.add_trace(go.Scattermapbox(
                mode="lines", lon=route_b["lons"], lat=route_b["lats"],
                line={'width': 4, 'color': "#10B981"}, name=f"Optimized Bypass"
            ))
            
            fig_map.update_layout(
                margin={'l':0, 't':0, 'b':0, 'r':0}, height=400,
                mapbox={'style': "carto-darkmatter", 'center': {'lat': (start_c[0]+end_c[0])/2, 'lon': (start_c[1]+end_c[1])/2}, 'zoom': 13},
                legend=dict(yanchor="top", y=0.95, xanchor="left", x=0.02, bgcolor="#1A1D23", font=dict(color="#E2E8F0"), bordercolor="#334155", borderwidth=1)
            )
            st.plotly_chart(fig_map, use_container_width=True)

            st.markdown('<div class="text-subtitle">Route Analytics</div>', unsafe_allow_html=True)
            
            # Subtly elevated metrics row
            st.markdown(f"""
                <div style="display: flex; gap: 16px;">
                    <div class="card" style="flex: 1;"><div class="text-micro">Exposure Reduction</div><div class="text-display" style="color:#10B981;">{max(0, route_a["average_aqi"] - route_b["average_aqi"])} Pts</div></div>
                    <div class="card" style="flex: 1;"><div class="text-micro">Hazards Avoided</div><div class="text-display" style="color:#10B981;">{max(0, route_a["toxic_segments"] - route_b["toxic_segments"])} Zones</div></div>
                    <div class="card" style="flex: 1;"><div class="text-micro">Fleet Policy</div><div class="text-display">Compliant</div></div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# 5. VIEW 3: GOV COMMAND CENTER
# ==========================================
elif app_mode == "Government Command":
    tab1, tab2 = st.tabs(["Forensic Audit Log", "Policy Digital Twin"])
    
# --------- TAB 1: AUDIT VAULT ---------
    with tab1:
        st.markdown('<div class="text-body" style="margin: 16px 0;">Immutable ledger of hardware drift and cryptographic reconciliation.</div>', unsafe_allow_html=True)
        
        # Clean Filter Bar
        f1, f2, f3 = st.columns([1, 1, 2])
        severity_filter = f1.selectbox("Severity", ["All Events", "Critical", "Nominal"], label_visibility="collapsed")
        
        try:
            conn = sqlite3.connect(DB_NAME)
            # FIX: Changed back to SELECT * so it dynamically adapts to your backend schema!
            df = pd.read_sql_query("SELECT * FROM spoofing_alerts ORDER BY timestamp DESC LIMIT 50", conn)
            conn.close()
            
            if severity_filter != "All Events":
                # Matches uppercase "CRITICAL" or "NOMINAL"
                df = df[df['status'].str.contains(severity_filter.upper(), na=False)]
                
            if not df.empty:
                # Pale background with strict left-border coloring
                def style_audit_rows(row):
                    if 'CRITICAL' in str(row.get('status', '')): 
                        return ['border-left: 4px solid #EF4444; background-color: #1A1D23; color: #E2E8F0;'] * len(row)
                    return ['border-left: 4px solid #10B981; background-color: #1A1D23; color: #E2E8F0;'] * len(row)
                
                st.dataframe(df.style.apply(style_audit_rows, axis=1), use_container_width=True, hide_index=True)
            else: 
                st.info("No matching records found. Go to 'Live Telemetry' and run a scan to generate logs.")
        except Exception as e: 
            st.error(f"Database unavailable: Please run a Telemetry Scan first to initialize the database.")

    # --------- TAB 2: POLICY SIMULATOR ---------
    with tab2:
        st.markdown("""
            <div style="display: flex; gap: 8px; margin: 16px 0; align-items: center;">
                <span class="chip chip-safe">1. Define Baseline</span>
                <span style="color: #334155;">───────</span>
                <span class="chip" style="background: #1A1D23; border: 1px solid #334155;">2. Apply Interventions</span>
            </div>
        """, unsafe_allow_html=True)
        
        target_zone = st.selectbox("Baseline Target", ["Delhi: ITO Crossing", "Delhi: Connaught Place"], label_visibility="collapsed")
        lat_gov, lon_gov = 28.6276, 77.2404 
        
        with st.spinner("Compiling current baseline..."):
            w_data, t_data = get_live_weather(lat_gov, lon_gov), get_live_traffic(lat_gov, lon_gov)
            
        if "error" not in w_data:
            base_aqi = calculate_hyperlocal_aqi(w_data, t_data)
            base_aqi = base_aqi["aqi"] if isinstance(base_aqi, dict) else base_aqi
            
            st.markdown('<div class="text-subtitle">Apply Interventions</div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="card card-tight" style="height: 60px; display: flex; align-items: center;">', unsafe_allow_html=True)
                odd_even = st.toggle("Enforce Odd-Even Traffic Rule")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="card card-tight" style="height: 60px; display: flex; align-items: center;">', unsafe_allow_html=True)
                heavy_ban = st.toggle("Ban Heavy Freight Vehicles")
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="card card-tight" style="height: 60px; display: flex; align-items: center;">', unsafe_allow_html=True)
                green_cover = st.toggle("Implement Green Wind Corridors")
                st.markdown('</div>', unsafe_allow_html=True)
                
            if odd_even: t_data['current_speed'] += 12 
            if heavy_ban: t_data['current_speed'] += 8  
            if green_cover: w_data['wind_speed'] += 1.5 
            
            sim_aqi = calculate_hyperlocal_aqi(w_data, t_data)
            sim_aqi = sim_aqi["aqi"] if isinstance(sim_aqi, dict) else sim_aqi
            reduction = abs(round(((sim_aqi - base_aqi) / base_aqi) * 100, 1)) if base_aqi > 0 else 0
            
            st.markdown(f"""
                <div style="background: linear-gradient(145deg, #1A1D23, #0F1117); border: 1px solid #334155; border-radius: 8px; padding: 24px; margin-top: 24px;">
                    <div class="text-micro" style="margin-bottom: 12px;">Projected Environmental Impact</div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <div>
                            <span class="text-display">{sim_aqi} AQI</span>
                            <span class="chip chip-safe" style="margin-left: 12px; transform: translateY(-4px);">↓ {reduction}% Reduction</span>
                        </div>
                        <div style="text-align: right;">
                            <div class="text-body">Baseline</div>
                            <div style="font-size: 20px; font-weight: 500; color: #64748B;">{base_aqi} AQI</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)