import os
import sys
import time
from collections import deque
from flask import Flask, request, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_backend.settings')

import django
django.setup()

from logistics.models import Rider, Telemetrylog, DeliveryOrder
from logistics.tasks import dispatch_rescue_task
from ml_engine.predictor import FleetAIEngine
from ingestion_flask.stream_broker import HybridStreamBroker

app = Flask(__name__)
CORS(app)

ai_engine = FleetAIEngine()
broker = HybridStreamBroker()
stats_counter = {"total_events_ingested": 0, "anomalies_flagged": 0, "orders_reassigned": 0}
RECENT_DISPATCH_LOGS = deque(maxlen=20)


@app.route('/api/v1/telemetry', methods=['POST'])
def ingest_telemetry():
    data = request.get_json()
    if not data or 'rider_code' not in data:
        return jsonify({"error": "Invalid telemetry payload"}), 400

    rider_code = data['rider_code']
    lat = float(data['latitude'])
    lng = float(data['longitude'])
    speed = float(data.get('speed_kmh', 20.0))
    battery = int(data.get('battery_pct', 100))

    # Find active order for this rider
    active_order = DeliveryOrder.objects.filter(
        rider__rider_code=rider_code,
        status__in=['IN_TRANSIT', 'REASSIGNED']
    ).first()
    dist_km = active_order.distance_km if active_order else 3.0

    # 1. Run Scikit-learn AI Prediction (ETA + IsolationForest Anomaly Detection)
    ai_result = ai_engine.analyze_telemetry(dist_km, speed, battery)

    # 2. Update Hybrid Cache (Redis or RAM) & Publish to Stream (Kafka or Deque)
    rider_state = {
        "rider_code": rider_code,
        "lat": lat,
        "lng": lng,
        "speed_kmh": speed,
        "battery_pct": battery,
        "predicted_eta_mins": ai_result["predicted_eta_mins"],
        "is_anomaly": ai_result["is_anomaly"],
        "anomaly_score": ai_result["anomaly_score"]
    }
    broker.cache_rider_state(rider_code, rider_state)
    broker.publish_event("telemetry_stream", rider_state)
    stats_counter["total_events_ingested"] += 1

    # 3. Update Rider state in DB
    new_status = 'LOW_BATTERY' if battery < 20 else 'DELIVERING'
    Rider.objects.filter(rider_code=rider_code).update(
        last_lat=lat, last_lng=lng, battery_pct=battery, status=new_status
    )

    # 4. Trigger Celery + RabbitMQ Auto-Reassignment if AI flags an anomaly
    if active_order:
        active_order.predicted_eta_mins = ai_result["predicted_eta_mins"]
        active_order.save(update_fields=['predicted_eta_mins'])

        if ai_result["is_anomaly"] and active_order.status == 'IN_TRANSIT':
            stats_counter["anomalies_flagged"] += 1
            stats_counter["orders_reassigned"] += 1
            dispatch_rescue_task(active_order.order_code, rider_code)
            RECENT_DISPATCH_LOGS.appendleft({
                "timestamp": time.strftime("%H:%M:%S"),
                "order_code": active_order.order_code,
                "failed_rider": rider_code,
                "reason": "Low Battery (<20%)" if battery < 20 else f"Stall Detected ({speed} km/h)",
                "eta_mins": ai_result["predicted_eta_mins"]
            })

    # 5. Batch write historical telemetry logs
    batch_items = broker.drain_batch(batch_size=15)
    if batch_items:
        Telemetrylog.objects.bulk_create([
            Telemetrylog(
                rider_code=i['rider_code'],
                latitude=i['lat'],
                longitude=i['lng'],
                speed_kmh=i['speed_kmh'],
                battery_pct=i['battery_pct']
            ) for i in batch_items
        ])

    return jsonify({
        "status": "INGESTED",
        "rider_code": rider_code,
        "ai_prediction": ai_result
    }), 202


@app.route('/api/v1/live-map', methods=['GET'])
def get_live_map_positions():
    riders = broker.get_all_riders()
    return jsonify({
        "count": len(riders),
        "total_events_ingested": stats_counter["total_events_ingested"],
        "anomalies_flagged": stats_counter["anomalies_flagged"],
        "orders_reassigned": stats_counter["orders_reassigned"],
        "dispatch_feed": list(RECENT_DISPATCH_LOGS),
        "riders": riders
    }), 200


if __name__ == '__main__':
    print("Starting AI + Celery FleetPulse Engine on http://127.0.0.1:5001 ...")
    app.run(host='127.0.0.1', port=5001, debug=True)