from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from profiles.models import NormalUserProfile, StaffProfile
from .decorators import staff_required, normal_user_required
from .models import User


class LoginAccessControlTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='pending@example.com',
            password='StrongPass123',
            full_name='Pending User',
            is_active=False,
            is_email_verified=False,
        )

    def test_unverified_user_cannot_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'pending@example.com', 'password': 'StrongPass123'},
            follow=True,
        )

        self.assertContains(response, 'Please verify your email first.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactive_user_cannot_login_even_if_email_is_verified(self):
        self.user.is_email_verified = True
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'pending@example.com', 'password': 'StrongPass123'},
            follow=True,
        )

        self.assertContains(response, 'Account is not active yet')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_normal_user_profile_is_created_on_user_creation(self):
        user = User.objects.create_user(
            email='normal@example.com',
            password='StrongPass123',
            full_name='Normal User',
            role=User.Role.NORMAL,
        )

        self.assertTrue(NormalUserProfile.objects.filter(user=user).exists())
        self.assertFalse(StaffProfile.objects.filter(user=user).exists())

    def test_staff_user_profile_is_created_on_user_creation(self):
        user = User.objects.create_user(
            email='staff@example.com',
            password='StrongPass123',
            full_name='Staff User',
            role=User.Role.STAFF,
        )

        self.assertTrue(StaffProfile.objects.filter(user=user).exists())
        self.assertFalse(NormalUserProfile.objects.filter(user=user).exists())

    def test_only_staff_can_access_staff_service_actions(self):
        @staff_required
        def dummy_staff_view(request):
            return 'ok'

        staff_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=User.Role.STAFF))
        normal_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=User.Role.NORMAL))
        admin_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=User.Role.SUPER_ADMIN))

        self.assertEqual(dummy_staff_view(staff_request), 'ok')
        with self.assertRaises(PermissionDenied):
            dummy_staff_view(normal_request)
        with self.assertRaises(PermissionDenied):
            dummy_staff_view(admin_request)

    def test_only_normal_users_can_access_service_purchase_actions(self):
        @normal_user_required
        def dummy_normal_view(request):
            return 'ok'

        normal_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=User.Role.NORMAL))
        staff_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=User.Role.STAFF))
        admin_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=User.Role.SUPER_ADMIN))

        self.assertEqual(dummy_normal_view(normal_request), 'ok')
        with self.assertRaises(PermissionDenied):
            dummy_normal_view(staff_request)
        with self.assertRaises(PermissionDenied):
            dummy_normal_view(admin_request)
