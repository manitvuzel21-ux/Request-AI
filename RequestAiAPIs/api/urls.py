from django.urls import path

from .views import (
    ApiRootView,
    AvailableDriverListView,
    AvailableRideListView,
    CancelRideView,
    ChangePasswordView,
    FareEstimateView,
    LoginView,
    RegistrationView,
    RideDetailView,
    RideListCreateView,
    UserProfileView,
)

urlpatterns = [
    path('', ApiRootView.as_view(), name='api-root'),
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('users/me/', UserProfileView.as_view(), name='profile'),
    path('users/me/password/', ChangePasswordView.as_view(), name='change-password'),
    path('drivers/available/', AvailableDriverListView.as_view(), name='available-drivers'),
    path('driver/rides/available/', AvailableRideListView.as_view(), name='available-rides'),
    path('rides/', RideListCreateView.as_view(), name='ride-list-create'),
    path('rides/<int:pk>/', RideDetailView.as_view(), name='ride-detail'),
    path('rides/<int:pk>/cancel/', CancelRideView.as_view(), name='ride-cancel'),
    path('fare-estimate/', FareEstimateView.as_view(), name='fare-estimate'),
]
