from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WarehouseHub, Rider, DeliveryOrder, Telemetrylog
from .serializers import (
    WarehouseHubSerializer,
    RiderSerializer,
    DeliveryOrderSerializer,
    TelemetryLogSerializer
)


class WarehouseHubViewSet(viewsets.ModelViewSet):
    queryset = WarehouseHub.objects.all()
    serializer_class = WarehouseHubSerializer


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.select_related('hub').all()
    serializer_class = RiderSerializer


class DeliveryOrderViewSet(viewsets.ModelViewSet):
    queryset = DeliveryOrder.objects.select_related('rider').order_by('-created_at')
    serializer_class = DeliveryOrderSerializer


@api_view(['GET'])
def dashboard_overview(request):
    
    total_riders = Rider.objects.count()
    active_riders = Rider.objects.filter(status='DELIVERING').count()
    low_battery_riders = Rider.objects.filter(battery_pct__lt=20).count()
    active_orders = DeliveryOrder.objects.filter(status='IN_TRANSIT').count()
    anomalies = DeliveryOrder.objects.filter(is_anomaly_flagged=True).count()

    return Response({
        "total_riders": total_riders,
        "active_riders": active_riders,
        "low_battery_alerts": low_battery_riders,
        "orders_in_transit": active_orders,
        "anomalies_detected": anomalies,
    })