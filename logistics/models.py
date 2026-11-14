from django.db import models

class WarehouseHub(models.Model):
    name = models.CharField(max_length=100)  
    district = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.district})"

class Rider(models.Model):
    STATUS_CHOICES = [
        ('IDLE', 'Idle'),
        ('DELIVERING', 'Delivering'),
        ('LOW_BATTERY', 'Low Battery Alert'),
        ('OFFLINE', 'Offline'),
    ]

    rider_code = models.CharField(max_length=20, unique=True, db_index=True) 
    full_name = models.CharField(max_length=100)
    hub = models.ForeignKey(WarehouseHub, on_delete=models.SET_NULL, null=True, related_name='riders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IDLE', db_index=True)
    battery_pct = models.IntegerField(default=100)
    last_lat = models.FloatField(default=52.5200)
    last_lng = models.FloatField(default=13.4050)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rider_code} - {self.full_name} ({self.battery_pct}%)"


class DeliveryOrder(models.Model):
    ORDER_STATUS = [
        ('PENDING', 'Pending Dispatch'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('REASSIGNED', 'Reassigned (Anomaly)'),
    ]
    order_code = models.CharField(max_length=30, unique=True, db_index=True) 
    rider = models.ForeignKey(Rider, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()
    distance_km = models.FloatField()
    predicted_eta_mins = models.FloatField(null=True, blank=True)
    is_anomaly_flagged = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)   

    def __str__(self):
        return f"{self.order_code} ({self.status})"


class Telemetrylog(models.Model):
    rider_code = models.CharField(max_length=20, db_index=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed_kmh = models.FloatField()
    battery_pct = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta :
        indexes = [
            models.Index(fields=['rider_code' , '-timestamp']),
        
        ]