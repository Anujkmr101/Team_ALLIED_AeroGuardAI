# 🌍 AeroGuard AI: Central Command
**Hyper-Local Telemetry & Node Integrity Validation System**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Enterprise-FF4B4B.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)
![Status](https://img.shields.io/badge/Status-Hackathon_MVP_Active-brightgreen.svg)

> **Submission for the National Hackathon at Shivalik College of Engineering, Dehradun.** > Built with 💻 & 🛡️ by **Team ALLIED**.

---

## 🚀 The Problem We Solve
City-level AQI (Air Quality Index) data lacks granularity. Current systems rely on physical sensors that cannot detect the **"Street-Canyon Effect"** (where pollution is trapped between tall buildings). Furthermore, physical sensors are highly vulnerable to **Eco-Spoofing** (tampering with local sensors to show fake "safe" data).

## 💡 The AeroGuard Solution
AeroGuard AI is not just a pollution tracker; it is a **Cybersecurity Shield for Environmental Data**.
1. **Hyper-Local AI Forecasting:** We correlate real-time traffic congestion (TomTom API) with wind telemetry (OpenWeather API) to predict trapped emissions at a micro-level.
2. **Immutable Node Audit (Anti-Spoofing):** Our AI acts as an auditor. If a physical sensor reports "Safe" AQI but our AI calculates a high concentration of trapped emissions, the system flags a **🚨 CRITICAL SPOOFING ANOMALY** and logs it securely for government/B2B review.

---

## 🏗️ System Architecture



Our architecture is divided into four robust micro-components:
* **The Ingestion Engine (`backend/api_fetcher.py`):** Fetches live wind and traffic congestion data.
* **The AI Core (`backend/ml_engine.py`):** Calculates hyper-local AQI based on physics and heuristic models (XGBoost ready).
* **The Cyber Vault (`database/audit_logger.py`):** Secures and validates sensor integrity using parameterized SQLite queries.
* **The Command Dashboard (`frontend/app.py`):** An enterprise-grade Streamlit B2G interface for monitoring anomalies.

---

## ⚙️ Installation & Deployment

Follow these steps to run the AeroGuard Central Command locally.

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/Team_ALLIED_AeroGuardAI.git](https://github.com/your-username/Team_ALLIED_AeroGuardAI.git)
cd Team_ALLIED_AeroGuardAI
```

### 2. Install Dependencies
```bash
pip install streamlit pandas requests python-dotenv folium
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your secure API keys:
```env
OPENWEATHER_API_KEY=your_openweather_api_key_here
TOMTOM_API_KEY=your_tomtom_api_key_here
```

### 4. Initialize the System
Run the Streamlit application. The system will automatically resolve module paths and initialize the secure database vault.
```bash
streamlit run frontend/app.py
```

---

## 👨‍💻 Team ALLIED
* **Anuj** - Tech Lead / Frontend & Cyber Architect
* **Hina** - Data Engineer (API Ingestion)
* **Jatin** - AI/ML Integrator
* **Jiya** - Cybersecurity & Database Engineer

---
*AeroGuard AI - Because breathing clean air shouldn't require blind trust.*
```

---

### 👑 The Impact:
Bhai, jab koi bhi judge ya investor is README ko dekhega, usko lagega ki ye bachhe nahi, balki ek actual tech company ki core team apna MVP present kar rahi hai. Ye tumhare GitHub repo ka look poora badal dega!

**Ab repo ekdum chamak chuki hai aur code live hai!** Kya ab hum **Option 1 (The Visual Upgrade - Live Map)** ki taraf chalein taaki dashboard aur bhi interactive lage, ya seedha **Option 3 (The Pitch Script)** shuru karein taaki tu aur teri team Discord pitch ki practice kar sako? Bata kya plan hai?