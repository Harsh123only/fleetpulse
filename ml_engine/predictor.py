import os
import datetime
import joblib
import numpy as np

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
ETA_MODEL_PATH = os.path.join(MODEL_DIR, "eta_predictor.joblib")
ANOMALY_MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_detector.joblib")

class FleetAIEngine:
    def __init__(self):
        self.eta_model = joblib.load(ETA_MODEL_PATH)
        self.anomaly_model = joblib.load(ANOMALY_MODEL_PATH)

    def analyze_telemetry(self, distance_km: float, speed_kmh: float, battery_pct: int):
        hour = datetime.datetime.now().hour
        safe_speed = max(5.0, float(speed_kmh))

        # 1. Predict ETA in minutes
        X_eta = np.array([[float(distance_km), safe_speed, hour, int(battery_pct)]])
        predicted_eta = float(self.eta_model.predict(X_eta)[0])

        # 2. Detect Anomaly (-1 = Anomaly, 1 = Normal in IsolationForest)
        X_anom = np.array([[float(speed_kmh), int(battery_pct)]])
        anom_pred = int(self.anomaly_model.predict(X_anom)[0])
        anom_score = float(self.anomaly_model.decision_function(X_anom)[0])

        is_anomaly = (anom_pred == -1) or (battery_pct < 20) or (speed_kmh < 2.5)
        return {
            "predicted_eta_mins": round(predicted_eta, 1),
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": round(anom_score, 3)
        }