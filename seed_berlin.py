import os
import random
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_backend.settings')
django.setup()

from logistics.models import WarehouseHub, Rider, DeliveryOrder

def seed_data():
    print("Clearing old data...")
    DeliveryOrder.objects.all().delete()
    Rider.objects.all().delete()
    WarehouseHub.objects.all().delete()

    hubs_data = [
        {"name": "Moabit Logistics Hub", "district": "Moabit", "lat": 52.5256, "lng": 13.3418},
        {"name": "Alexanderplatz Central", "district": "Mitte", "lat": 52.5219, "lng": 13.4132},
        {"name": "Kottbusser Tor Depot", "district": "Kreuzberg", "lat": 52.4990, "lng": 13.4184},
        {"name": "Zoo West Station", "district": "Charlottenburg", "lat": 52.5065, "lng": 13.3327},
    ]

    hubs = []
    for h in hubs_data:
        hub = WarehouseHub.objects.create(
            name=h["name"],
            district=h["district"],
            latitude=h["lat"],
            longitude=h["lng"]
        )
        hubs.append(hub)

    names = [
        "Lukas Weber", "Matteo Rossi", "Arjun Sharma", "Felix Meyer", "Noah Wagner",
        "Leon Becker", "Yusuf Kaya", "Paul Hoffmann", "Jonas Schulz", "Elias Koch",
        "David Bauer", "Milan Richter", "jan Klein", "Tim Wolf", "Niklas Schröder"
    ]

    riders = []
    for i, name in enumerate(names, start=101):
        hub = random.choice(hubs)
        battery = random.choice([95, 88, 76, 64, 52, 45, 16, 12])
        status = 'LOW_BATTERY' if battery < 20 else 'DELIVERING'
        rider = Rider.objects.create(
            rider_code=f"R-{i}",
            full_name=name,
            hub=hub,
            status=status,
            battery_pct=battery,
            last_lat=hub.latitude + random.uniform(-0.015, 0.015),
            last_lng=hub.longitude + random.uniform(-0.015, 0.015),
        )
        riders.append(rider)

    for j in range(1, 13):
        rider = riders[j - 1]
        dist = round(random.uniform(1.2, 6.8), 2)
        is_anomaly = rider.battery_pct < 20
        DeliveryOrder.objects.create(
            order_code=f"ORD-{9000 + j}",
            rider=rider,
            pickup_lat=rider.last_lat,
            pickup_lng=rider.last_lng,
            dropoff_lat=rider.last_lat + random.uniform(-0.02, 0.02),
            dropoff_lng=rider.last_lng + random.uniform(-0.02, 0.02),
            distance_km=dist,
            predicted_eta_mins=round(dist * 3.4 + random.uniform(2, 6), 1),
            is_anomaly_flagged=is_anomaly,
            status='IN_TRANSIT'
        )

    print("Success! Created 4 Berlin hubs, 15 riders, and 12 active orders.")

if __name__ == '__main__':
    seed_data()