from django.db import models
from django.contrib.auth.models import User


class DriverProfile(models.Model):
    VEHICLE_TYPES = (
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('xl', 'XL'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    vehicle_type = models.CharField(max_length=30, choices=VEHICLE_TYPES)
    vehicle_number = models.CharField(max_length=20, unique=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} ({self.vehicle_type})'


class Ride(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides')
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rides',
    )
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    vehicle_type = models.CharField(max_length=30, default='standard')
    estimated_fare = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
