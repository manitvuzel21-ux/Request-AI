from django.contrib import admin

from .models import DriverProfile, Ride


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'vehicle_number', 'is_available')
    list_filter = ('vehicle_type', 'is_available')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'vehicle_number',
    )


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider', 'driver', 'vehicle_type', 'status', 'created_at')
    list_filter = ('vehicle_type', 'status')
    search_fields = ('rider__username', 'driver__user__username')
