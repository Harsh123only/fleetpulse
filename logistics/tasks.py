import math
import threading
import socket
from celery import shared_task
from .models import Rider, DeliveryOrder


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calculates exact distance in kilometers between two GPS coordinates in Berlin.
    """
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@shared_task
def auto_reassign_anomalous_order(order_code: str, failed_rider_code: str):
    """
    Celery task triggered when Scikit-learn flags a dying battery or stalled rider.
    Finds the nearest healthy rider (battery > 50%) and reassigns the delivery.
    """
    try:
        order = DeliveryOrder.objects.select_related('rider').get(order_code=order_code)
    except DeliveryOrder.DoesNotExist:
        return f"Order {order_code} not found."

    if order.status == 'REASSIGNED':
        return f"Order {order_code} already reassigned."

    # Find candidate riders with healthy batteries (> 50%) excluding the stalled rider
    candidates = Rider.objects.filter(battery_pct__gte=50).exclude(rider_code=failed_rider_code)
    if not candidates.exists():
        return f"No healthy riders available to rescue {order_code}."

    # Pick the geographically closest rider using Haversine formula
    best_rider = min(
        candidates,
        key=lambda r: haversine_km(order.pickup_lat, order.pickup_lng, r.last_lat, r.last_lng)
    )
    rescue_dist = round(
        haversine_km(order.pickup_lat, order.pickup_lng, best_rider.last_lat, best_rider.last_lng), 2
    )

    # Update order and rider states in Database
    old_rider = order.rider.rider_code if order.rider else failed_rider_code
    order.rider = best_rider
    order.status = 'REASSIGNED'
    order.is_anomaly_flagged = True
    order.save(update_fields=['rider', 'status', 'is_anomaly_flagged'])

    best_rider.status = 'DELIVERING'
    best_rider.save(update_fields=['status'])

    msg = (
        f"[CELERY AUTO-DISPATCH] Rescued {order.order_code} from {old_rider} -> "
        f"Assigned to {best_rider.rider_code} ({best_rider.full_name}, {best_rider.battery_pct}% bat, {rescue_dist} km away)"
    )
    print(msg)
    return msg


def dispatch_rescue_task(order_code: str, failed_rider_code: str):
    """
    Smart Dispatcher: Uses RabbitMQ broker if running on port 5672;
    otherwise executes via background worker thread in local Option B mode.
    """
    try:
        sock = socket.create_connection(("127.0.0.1", 5672), timeout=0.3)
        sock.close()
        auto_reassign_anomalous_order.delay(order_code, failed_rider_code)
    except OSError:
        threading.Thread(
            target=auto_reassign_anomalous_order,
            args=(order_code, failed_rider_code),
            daemon=True
        ).start()