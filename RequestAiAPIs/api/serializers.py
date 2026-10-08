from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import DriverProfile, Ride


class CaseInsensitiveChoiceField(serializers.ChoiceField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = data.lower()
        return super().to_internal_value(data)


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        read_only_fields = ('username',)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class RideSerializer(serializers.ModelSerializer):
    rider = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ride
        fields = '__all__'
        read_only_fields = (
            'estimated_fare',
            'status',
            'rider',
            'driver',
            'created_at',
            'updated_at',
        )

    def validate_vehicle_type(self, value):
        vehicle_type = value.lower()
        if vehicle_type not in {'standard', 'premium', 'xl'}:
            raise serializers.ValidationError(
                'Vehicle type must be standard, premium, or xl.'
            )
        return vehicle_type


class AvailableDriverSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = DriverProfile
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'vehicle_type',
            'vehicle_number',
        )


class FareEstimateSerializer(serializers.Serializer):
    distance_km = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    vehicle_type = CaseInsensitiveChoiceField(
        choices=('standard', 'premium', 'xl'), default='standard'
    )

    def validate_vehicle_type(self, value):
        return value.lower()
