import os
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
ETA_MODEL_PATH = os.path.join(MODEL_DIR, "eta_predictor.joblib")
ANOMALY_MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_detector.joblib")

def train_and_save_models():
    print("Generating 5,000 synthetic Berlin delivery records for training...")
    np.random.seed(42)
    n_samples = 5000

    # Features: [distance_km, speed_kmh, hour_of_day, battery_pct]
    distance_km = np.random.uniform(0.5, 9.0, n_samples)
    speed_kmh = np.random.uniform(12.0, 28.0, n_samples)
    hour_of_day = np.random.randint(8, 23, n_samples)
    battery_pct = np.random.randint(15, 100, n_samples)

    # Rush hour penalty in Berlin (17:00 - 20:00 adds 3-6 mins)
    rush_hour_penalty = np.where((hour_of_day >= 17) & (hour_of_day <= 20), 4.5, 1.0)
    low_bat_penalty = np.where(battery_pct < 25, 3.0, 0.0)

    # True ETA in minutes + realistic street noise
    eta_minutes = (distance_km / speed_kmh) * 60.0 + rush_hour_penalty + low_bat_penalty + np.random.normal(0, 1.2, n_samples)
    eta_minutes = np.maximum(2.0, eta_minutes)

    X_eta = np.column_stack([distance_km, speed_kmh, hour_of_day, battery_pct])

    print("Training HistGradientBoostingRegressor for live ETA prediction...")
    eta_model = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.08, random_state=42)
    eta_model.fit(X_eta, eta_minutes)

    preds = eta_model.predict(X_eta[:500])
    mae = mean_absolute_error(eta_minutes[:500], preds)
    print(f"ETA Model Trained! Mean Absolute Error: +/- {mae:.2f} minutes")

    # 2. Train IsolationForest for Telemetry Anomaly Detection
    # Normal riders: speed 15-28 km/h, battery 25-100%
    normal_telemetry = np.column_stack([
        np.random.normal(21.0, 3.5, 4500),  # normal speed
        np.random.uniform(25, 100, 4500)    # healthy battery
    ])
    # Anomalous riders: stalled bikes (0-3 km/h) or critically low battery (< 18%)
    anomalous_telemetry = np.column_stack([
        np.random.uniform(0.1, 4.0, 500),
        np.random.uniform(5, 18, 500)
    ])
    X_anomaly = np.vstack([normal_telemetry, anomalous_telemetry])

    print("Training IsolationForest for e-bike telemetry anomaly detection...")
    anomaly_model = IsolationForest(contamination=0.10, random_state=42)
    anomaly_model.fit(X_anomaly)

    joblib.dump(eta_model, ETA_MODEL_PATH)
    joblib.dump(anomaly_model, ANOMALY_MODEL_PATH)
    print(f"Saved compiled models to:\n - {ETA_MODEL_PATH}\n - {ANOMALY_MODEL_PATH}")

if __name__ == "__main__":
    train_and_save_models()