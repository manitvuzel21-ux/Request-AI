from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DriverProfile, Ride


class AuthenticationTests(APITestCase):
    def test_user_receives_jwt_tokens_when_registering(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-rider',
                'email': 'rider@example.com',
                'password': 'Strong-password-123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['message'],
            'Registration successful. Use the access token to authenticate.',
        )
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertTrue(User.objects.filter(username='new-rider').exists())

    def test_user_can_log_in_and_receive_jwt_tokens(self):
        user = User.objects.create_user(
            username='rider',
            password='Strong-password-123',
        )

        response = self.client.post(
            reverse('login'),
            {'username': user.username, 'password': 'Strong-password-123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            'Login successful. Use the access token to authenticate.',
        )
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    def test_legacy_token_obtain_endpoint_is_removed(self):
        response = self.client.post(
            '/api/token/',
            {'username': 'rider', 'password': 'Strong-password-123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileUpdateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rider',
            password='Strong-password-123',
        )
        self.client.force_authenticate(self.user)

    def test_profile_can_be_updated_with_put(self):
        response = self.client.put(
            reverse('profile'),
            {'first_name': 'Updated'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            'Profile updated successfully.',
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_profile_does_not_accept_post(self):
        response = self.client.post(
            reverse('profile'),
            {'first_name': 'Updated'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_password_can_be_changed_with_patch(self):
        payload = {
            'old_password': 'Strong-password-123',
            'new_password': 'New-strong-password-123',
        }

        response = self.client.patch(
            reverse('change-password'),
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            'Password changed successfully.',
        )

    def test_password_does_not_accept_post_or_put(self):
        payload = {
            'old_password': 'Strong-password-123',
            'new_password': 'New-strong-password-123',
        }

        post_response = self.client.post(
            reverse('change-password'),
            payload,
            format='json',
        )
        put_response = self.client.put(
            reverse('change-password'),
            payload,
            format='json',
        )

        self.assertEqual(post_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class DriverAvailabilityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rider',
            password='Strong-password-123',
        )
        self.client.force_authenticate(self.user)
        self.standard_driver = DriverProfile.objects.create(
            user=User.objects.create_user(username='standard-driver'),
            vehicle_type='standard',
            vehicle_number='STD-001',
        )
        DriverProfile.objects.create(
            user=User.objects.create_user(username='premium-driver'),
            vehicle_type='premium',
            vehicle_number='PRE-001',
        )
        DriverProfile.objects.create(
            user=User.objects.create_user(username='unavailable-driver'),
            vehicle_type='standard',
            vehicle_number='STD-002',
            is_available=False,
        )

    def test_rider_can_view_available_drivers_by_vehicle_type(self):
        response = self.client.get(
            reverse('available-drivers'),
            {'vehicle_type': 'standard'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            'Available drivers retrieved successfully.',
        )
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['username'], 'standard-driver')
        self.assertEqual(response.data['data'][0]['vehicle_number'], 'STD-001')

    def test_rider_creates_ride_without_assigning_driver(self):
        response = self.client.post(
            reverse('ride-list-create'),
            {
                'pickup_location': 'A',
                'dropoff_location': 'B',
                'distance_km': '5.00',
                'vehicle_type': 'standard',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['data']['driver'])

    def test_matching_driver_can_view_available_ride_requests(self):
        ride = Ride.objects.create(
            rider=self.user,
            pickup_location='A',
            dropoff_location='B',
            distance_km='5.00',
            vehicle_type='standard',
            estimated_fare='150.00',
        )
        self.client.force_authenticate(self.standard_driver.user)

        response = self.client.get(reverse('available-rides'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'][0]['id'], ride.pk)

    def test_regular_rider_cannot_view_driver_ride_requests(self):
        response = self.client.get(reverse('available-rides'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RideDeletionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rider',
            password='Strong-password-123',
        )
        self.client.force_authenticate(self.user)

    def test_authenticated_rider_can_delete_their_ride(self):
        ride = Ride.objects.create(
            rider=self.user,
            pickup_location='A',
            dropoff_location='B',
            distance_km='5.00',
            vehicle_type='standard',
            estimated_fare='150.00',
        )

        response = self.client.delete(
            reverse('ride-detail', kwargs={'pk': ride.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Ride deleted successfully.')
        self.assertFalse(Ride.objects.filter(pk=ride.pk).exists())

    def test_rider_cannot_delete_another_riders_ride(self):
        other_user = User.objects.create_user(username='other')
        ride = Ride.objects.create(
            rider=other_user,
            pickup_location='A',
            dropoff_location='B',
            distance_km='5.00',
            vehicle_type='standard',
            estimated_fare='150.00',
        )

        response = self.client.delete(
            reverse('ride-detail', kwargs={'pk': ride.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Ride.objects.filter(pk=ride.pk).exists())
