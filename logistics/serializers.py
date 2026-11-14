from rest_framework import serializers
from .models import WarehouseHub, Rider, DeliveryOrder, Telemetrylog


class WarehouseHubSerializer(serializers.ModelSerializer):
    rider_count = serializers.IntegerField(source='riders.count', read_only=True)

    class Meta:
        model = WarehouseHub
        fields = ['id', 'name', 'district', 'latitude', 'longitude', 'rider_count']

class RiderSerializer(serializers.ModelSerializer):
    hub_name = serializers.CharField(source='hub.name', read_only=True)

    class Meta:
        model = Rider
        fields = [
            'id', 'rider_code', 'full_name', 'hub', 'hub_name',
            'status', 'battery_pct', 'last_lat', 'last_lng', 'updated_at'
        ]

class DeliveryOrderSerializer(serializers.ModelSerializer):
    rider_code = serializers.CharField(source='rider.rider_code', read_only=True)

    class Meta:
        model = DeliveryOrder
        fields = [
            'id', 'order_code', 'rider', 'rider_code',
            'pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng',
            'distance_km', 'predicted_eta_mins', 'is_anomaly_flagged',
            'status', 'created_at'
        ]


class TelemetryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetrylog
        fields = '__all__'