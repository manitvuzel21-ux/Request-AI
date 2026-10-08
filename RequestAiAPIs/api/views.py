from decimal import Decimal

from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import DriverProfile, Ride
from .serializers import (
    ChangePasswordSerializer,
    FareEstimateSerializer,
    AvailableDriverSerializer,
    RegistrationSerializer,
    RideSerializer,
    UserProfileSerializer,
)


def message_response(message, data=None, status_code=status.HTTP_200_OK):
    response_data = {'message': message}
    if data is not None:
        response_data['data'] = data
    return Response(response_data, status=status_code)


@extend_schema(responses=OpenApiTypes.OBJECT)
class ApiRootView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response({
            'message': 'Welcome to Request AI API',
            'swagger': request.build_absolute_uri('/swagger/'),
        })


@extend_schema(tags=['1. Authentication'])
class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return message_response(
                'Login successful. Use the access token to authenticate.',
                response.data,
            )
        return response


@extend_schema(tags=['1. Authentication'])
class RefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return message_response('Token refreshed successfully.', response.data)
        return response


@extend_schema(tags=['1. Authentication'])
class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        responses=inline_serializer(
            name='RegistrationResponse',
            fields={
                'username': serializers.CharField(),
                'email': serializers.EmailField(allow_blank=True),
                'first_name': serializers.CharField(allow_blank=True),
                'last_name': serializers.CharField(allow_blank=True),
                'refresh': serializers.CharField(),
                'access': serializers.CharField(),
            },
        )
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response_data = {
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return message_response(
            'Registration successful. Use the access token to authenticate.',
            response_data,
            status.HTTP_201_CREATED,
        )


@extend_schema(tags=['2. User profile'])
class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return message_response('Profile retrieved successfully.', response.data)

    @extend_schema(request=UserProfileSerializer, responses=UserProfileSerializer)
    def _update(self, request):
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return message_response('Profile updated successfully.', serializer.data)

    patch = _update
    put = _update


@extend_schema(tags=['2. User profile'])
class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=ChangePasswordSerializer, responses={200: OpenApiTypes.OBJECT})
    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'detail': 'Old password is incorrect.'}, status=400)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return message_response('Password changed successfully.')


@extend_schema(tags=['4. Rides'])
class AvailableDriverListView(generics.ListAPIView):
    serializer_class = AvailableDriverSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = DriverProfile.objects.filter(is_available=True).select_related('user')
        vehicle_type = self.request.query_params.get('vehicle_type')
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type.lower())
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return message_response('Available drivers retrieved successfully.', response.data)


@extend_schema(tags=['4. Rides'])
class AvailableRideListView(generics.ListAPIView):
    serializer_class = RideSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        try:
            driver = self.request.user.driver_profile
        except DriverProfile.DoesNotExist as exc:
            raise PermissionDenied('Only drivers can view available ride requests.') from exc

        return Ride.objects.filter(
            driver__isnull=True,
            status=Ride.Status.REQUESTED,
            vehicle_type=driver.vehicle_type,
        ).select_related('rider')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return message_response('Available ride requests retrieved successfully.', response.data)


@extend_schema(tags=['4. Rides'])
class RideListCreateView(generics.ListCreateAPIView):
    serializer_class = RideSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Ride.objects.filter(rider=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return message_response('Rides retrieved successfully.', response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return message_response('Ride created successfully.', response.data, response.status_code)

    def perform_create(self, serializer):
        distance = serializer.validated_data['distance_km']
        vehicle = serializer.validated_data['vehicle_type']
        multiplier = {'standard': Decimal('1.0'), 'premium': Decimal('1.5'), 'xl': Decimal('1.8')}[vehicle]
        fare = (Decimal('50.00') + distance * Decimal('20.00')) * multiplier
        serializer.save(rider=self.request.user, estimated_fare=fare.quantize(Decimal('0.01')))


@extend_schema(tags=['4. Rides'])
class RideDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = RideSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Ride.objects.filter(rider=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return message_response('Ride retrieved successfully.', response.data)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return message_response('Ride deleted successfully.')


@extend_schema(tags=['4. Rides'])
class CancelRideView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RideSerializer

    @extend_schema(responses={200: RideSerializer})
    def post(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk, rider=request.user)
        except Ride.DoesNotExist:
            return Response({'detail': 'Ride not found.'}, status=404)
        if ride.status == Ride.Status.CANCELLED:
            return Response({'detail': 'Ride is already cancelled.'}, status=400)
        ride.status = Ride.Status.CANCELLED
        ride.save(update_fields=['status', 'updated_at'])
        return message_response(
            'Ride cancelled successfully.',
            RideSerializer(ride).data,
        )

@extend_schema(tags=['3. Fare estimate'])
class FareEstimateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    response_serializer = inline_serializer(
        name='FareEstimateResponse',
        fields={
            'distance_km': serializers.DecimalField(max_digits=8, decimal_places=2),
            'vehicle_type': serializers.CharField(),
            'estimated_fare': serializers.DecimalField(max_digits=8, decimal_places=2),
        },
    )

    @extend_schema(
        parameters=[
            OpenApiParameter('distance_km', OpenApiTypes.DECIMAL, required=True),
            OpenApiParameter(
                'vehicle_type',
                OpenApiTypes.STR,
                enum=['standard', 'premium', 'xl'],
                default='standard',
            ),
        ],
        responses=response_serializer,
    )
    def get(self, request):
        return self._estimate(request.query_params)

    def _estimate(self, data):
        serializer = FareEstimateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        distance = serializer.validated_data['distance_km']
        vehicle = serializer.validated_data['vehicle_type']
        multiplier = {'standard': Decimal('1.0'), 'premium': Decimal('1.5'), 'xl': Decimal('1.8')}[vehicle]
        fare = ((Decimal('50.00') + distance * Decimal('20.00')) * multiplier).quantize(Decimal('0.01'))
        return message_response(
            'Fare estimated successfully.',
            {
                'distance_km': distance,
                'vehicle_type': vehicle,
                'estimated_fare': fare,
            },
        )
