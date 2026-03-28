# AeroGuard AI: Next-Gen Physiological Air Intelligence

**Bridging the gap between macro-atmospheric data and micro-human health.**

AeroGuard AI is an enterprise-grade intelligence platform designed to solve the "last-mile" problem of urban air pollution. While legacy systems (CPCB) provide sparse, macro-level data, AeroGuard utilizes multi-modal sensor fusion and XGBoost-driven forecasting to provide street-level fidelity and actionable health-risk mitigation.

---

## 🚀 The Core Innovation: "Dose Over AQI"

Standard AQI is a legacy metric. AeroGuard AI introduces the **Toxicity Exposure Reduction Metric (TERM)**. Instead of routing by distance, our engine calculates the **Estimated Inhaled Dose (µg)** of particulate matter based on:
* **Micro-physics Nowcasting:** 100m-grid estimation using live traffic telematics and wind vectors.
* **Physiological Profiling:** Dynamic adjustment for transport modes (Pedestrian, Cyclist, Vehicle) and their respective **Infiltration Factors**.
* **Temporal Optimization:** Comparing "Dispatch Now" vs "Forecast-based Delay" to minimize total respiratory load.

---

## 🛠️ Key Technical Pillars

### 1. Multi-Modal ML Stack
* **Engine A (Nowcast):** Random Forest Regressor fusing TomTom traffic flow and OpenWeather API for real-time street-level estimation.
* **Engine B (Forecast):** XGBoost Time-Series model for 1–6 hour predictive hotspot modeling.
* **Satellite Fusion:** Sentinel-5P NO₂ data (via Google Earth Engine) downscaled through localized traffic density constraints.

### 2. Cryptographic Sensor Integrity (Audit Ledger)
To eliminate data spoofing and hardware drift, we implemented a **Hash-Chained Audit Ledger**. 
* Every sensor reading is validated against a physics baseline.
* Anomalies are logged in an append-only SQLite ledger.
* **SHA-256 Chaining:** Each log entry is cryptographically linked to the previous, ensuring a tamper-proof forensic trail for environmental audits.

### 3. Policy Digital Twin
A high-fidelity simulator for municipal authorities to stress-test **GRAP (Graded Response Action Plan)** interventions. Toggle Low Emission Zones (LEZ) or construction halts to see real-time projected impacts on city-wide toxicity.

---

## 📊 Scientific Validation (Ground-Truth)

We don't just predict; we validate. AeroGuard AI was backtested against **8,000+ hourly ground-truth records** from the OpenAQ/CPCB network.

| Metric | Score |
| :--- | :--- |
| **R² Correlation** | **0.92** |
| **Validation RMSE** | **±0.28** |
| **Hotspot Classification Accuracy** | **90.5%** |

*Our models demonstrate a 92% correlation with actual CPCB hardware, proving enterprise-grade reliability in high-density urban environments.*

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/AeroGuard-AI.git
   ```
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Configuration:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   OPENWEATHER_API_KEY=your_key
   TOMTOM_API_KEY=your_key
   WAQI_API_KEY=your_key
   ```
4. **Launch the Command Center:**
   ```bash
   streamlit run frontend/app.py
   ```

---

## 🌐 The Vision
AeroGuard AI is built for the future of smart cities. By integrating with fleet management systems, insurance providers, and public health dashboards, we are moving the needle from **monitoring pollution** to **actively preventing human exposure.**

---
