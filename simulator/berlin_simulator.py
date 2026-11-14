import time
import random
import requests

FLASK_INGEST_URL = "http://127.0.0.1:5001/api/v1/telemetry"
DJANGO_RIDERS_URL = "http://127.0.0.1:8000/api/riders/"

def load_initial_riders():
    print("Fetching active Berlin fleet from Django API...")
    response = requests.get(DJANGO_RIDERS_URL, timeout=5)
    response.raise_for_status()
    riders = response.json()
    fleet = {}
    for r in riders:
        fleet[r['rider_code']] = {
            "lat": r['last_lat'],
            "lng": r['last_lng'],
            "battery": r['battery_pct']
        }
    print(f"Loaded {len(fleet)} riders across Berlin hubs!")
    return fleet

def run_simulation():
    fleet = load_initial_riders()
    tick = 0

    print("\n--- STARTING LIVE BERLIN GPS TELEMETRY STREAM ---")
    print("Press Ctrl+C to stop.\n")

    while True:
        tick += 1
        for rider_code, state in fleet.items():
            # Simulate realistic movement along Berlin streets
            state["lat"] += random.uniform(-0.0008, 0.0008)
            state["lng"] += random.uniform(-0.0010, 0.0010)

            # Slowly drain battery every few ticks
            if tick % 5 == 0 and state["battery"] > 5:
                state["battery"] = max(5, state["battery"] - random.choice([0, 1]))

            # Occasional stall anomaly simulation (speed drops to 0.5 km/h)
            if random.random() < 0.04:
                speed = round(random.uniform(0.2, 1.5), 1)
            else:
                speed = round(random.uniform(16.0, 28.5), 1)

            payload = {
                "rider_code": rider_code,
                "latitude": round(state["lat"], 6),
                "longitude": round(state["lng"], 6),
                "speed_kmh": speed,
                "battery_pct": state["battery"]
            }

            try:
                res = requests.post(FLASK_INGEST_URL, json=payload, timeout=2)
                if res.status_code == 202:
                    status_tag = "⚠️ LOW BAT/STALL" if (state["battery"] < 20 or speed < 2.0) else "OK"
                    print(f"[Tick {tick}] {rider_code} -> ({payload['latitude']}, {payload['longitude']}) | {speed} km/h | Bat: {state['battery']}% [{status_tag}]")
            except Exception as e:
                print(f"Connection error to Flask: {e}")

        time.sleep(2)

if __name__ == "__main__":
    run_simulation()