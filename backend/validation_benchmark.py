import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

def run_ground_truth_validation(csv_path):
    print("--- 📊 INITIATING GROUND-TRUTH VALIDATION ---")
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} raw records from CSV.")
    except Exception as e:
        print(f"⚠️ Error reading file: {e}")
        return

    # 1. CLEAN COLUMNS
    df.columns = df.columns.str.lower().str.strip()
    
    # Use datetimeutc for safe parsing without timezone errors
    date_col = 'datetimeutc' if 'datetimeutc' in df.columns else 'datetimelocal'
    val_col = 'value'
    
    if date_col not in df.columns or val_col not in df.columns:
        print("⚠️ Missing critical columns (datetime or value).")
        return

    # 2. SMART POLLUTANT DETECTOR
    top_param = "pollutant"
    if 'parameter' in df.columns:
        top_param = df['parameter'].value_counts().idxmax()
        df = df[df['parameter'] == top_param]
        print(f"✅ Auto-detected predominant pollutant: {top_param.upper()}")

    # 3. PARSE DATES AND NUMBERS SAFELY
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
    
    df = df.dropna(subset=[date_col, val_col])
    df = df[df[val_col] >= 0]
    df = df.sort_values(date_col)
    
    # 4. FEATURE ENGINEERING
    print("⚙️ Engineering time-series features (Hour, Day, Lag)...")
    df['hour'] = df[date_col].dt.hour
    df['day_of_week'] = df[date_col].dt.dayofweek
    df['previous_hour_val'] = df[val_col].shift(1)
    
    # THE FIX: Only drop NaNs if they are in the columns we actually need for the ML model!
    ml_columns = ['hour', 'day_of_week', 'previous_hour_val', val_col]
    df = df.dropna(subset=ml_columns)

    if len(df) < 50:
        print("⚠️ Data cleaning removed too many rows. The file might not have continuous hourly data.")
        return
        
    print(f"✅ Surviving clean data points: {len(df)}")
    print(f"🧠 Training XGBoost Forecaster on {top_param.upper()} data...")

    # 5. TRAIN / TEST SPLIT
    X = df[['hour', 'day_of_week', 'previous_hour_val']]
    y = df[val_col]
    
    train_size = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    # 6. BENCHMARK
    predictions = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    # Dynamic Hotspot Threshold (Statistically identifies spikes)
    threshold = y.mean() + y.std()
    actual_hotspots = (y_test > threshold).astype(int)
    pred_hotspots = (predictions > threshold).astype(int)
    
    hit_rate = np.mean(actual_hotspots == pred_hotspots) * 100 if len(y_test) > 0 else 0

    print("\n===========================================")
    print("🏆 VALIDATION BENCHMARK RESULTS")
    print("===========================================")
    print(f"Target Pollutant:                     {top_param.upper()}")
    print(f"Validation MAE (Mean Absolute Error): {mae:.2f}")
    print(f"Validation RMSE (Error Margin):       ±{rmse:.2f}")
    print(f"R² Correlation Score:                 {r2:.2f}")
    print(f"Hotspot Classification Accuracy:      {hit_rate:.1f}%")
    print("===========================================\n")
    print("📸 TAKE A SCREENSHOT OF THIS FOR YOUR DECK!")

if __name__ == "__main__":
    # Apne CSV ka path yahan daal de
    run_ground_truth_validation(r"C:\Users\kmran\OneDrive\Desktop\AeroGaurd\Team_ALLIED_AeroGuardAI\backend\openaq_location_5613_measurments (1).csv")