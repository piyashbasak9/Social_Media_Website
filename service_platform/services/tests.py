import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from chat.models import Message
from tokens.models import TokenBalance, TokenTransaction
from .models import Service, ServiceMedia, ServiceUnlock


class ServiceUnlockTests(TestCase):
	def setUp(self):
		media_root = tempfile.TemporaryDirectory()
		settings_override = override_settings(MEDIA_ROOT=media_root.name)
		settings_override.enable()
		self.addCleanup(media_root.cleanup)
		self.addCleanup(settings_override.disable)
		self.staff = User.objects.create_user(
			email='staff@example.com', password='pass12345', full_name='Staff',
			role=User.Role.STAFF, is_active=True,
		)
		self.user = User.objects.create_user(
			email='user@example.com', password='pass12345', full_name='User',
			role=User.Role.NORMAL, is_active=True,
		)
		self.service = Service.objects.create(
			staff=self.staff,
			title='Photo collection',
			description='A private gallery',
			token_price=12,
			service_type=Service.ServiceType.GENERAL,
			status=Service.Status.APPROVED,
		)
		TokenBalance.objects.create(user=self.user, balance=30)

	def test_unlock_deducts_tokens_once_and_opens_view(self):
		self.client.force_login(self.user)
		locked_response = self.client.get('/services/')

		self.assertContains(locked_response, 'Locked')
		self.assertContains(locked_response, 'Unlock for 12 tokens')

		response = self.client.post(f'/services/{self.service.id}/unlock/')

		self.assertRedirects(response, '/services/')
		self.assertEqual(TokenBalance.objects.get(user=self.user).balance, 18)
		self.assertTrue(ServiceUnlock.objects.filter(user=self.user, service=self.service).exists())
		self.assertEqual(TokenTransaction.objects.filter(user=self.user).count(), 1)
		list_response = self.client.get('/services/')
		self.assertContains(list_response, f'/services/{self.service.id}/view/')

		self.client.post(f'/services/{self.service.id}/unlock/')
		self.assertEqual(TokenBalance.objects.get(user=self.user).balance, 18)
		self.assertEqual(TokenTransaction.objects.filter(user=self.user).count(), 1)

	def test_unlocked_gallery_media_is_not_available_before_unlock(self):
		media = ServiceMedia.objects.create(
			service=self.service,
			media_type=ServiceMedia.MediaType.IMAGE,
			file=SimpleUploadedFile('photo.jpg', b'private photo', content_type='image/jpeg'),
		)
		self.client.force_login(self.user)

		response = self.client.get(f'/services/{self.service.id}/view/')
		file_response = self.client.get(f'/services/media/{media.id}/')

		self.assertRedirects(response, f'/services/{self.service.id}/')
		self.assertEqual(file_response.status_code, 403)

		ServiceUnlock.objects.create(user=self.user, service=self.service)
		file_response = self.client.get(f'/services/media/{media.id}/')
		self.assertEqual(file_response.status_code, 200)
		self.assertEqual(b''.join(file_response.streaming_content), b'private photo')

	def test_insufficient_balance_does_not_unlock(self):
		TokenBalance.objects.filter(user=self.user).update(balance=5)
		self.client.force_login(self.user)

		self.client.post(f'/services/{self.service.id}/unlock/')

		self.assertFalse(ServiceUnlock.objects.filter(user=self.user, service=self.service).exists())
		self.assertEqual(TokenBalance.objects.get(user=self.user).balance, 5)

	def test_only_photo_video_services_are_listed(self):
		Service.objects.create(
			staff=self.staff,
			title='Old call service',
			description='Legacy service',
			token_price=5,
			service_type=Service.ServiceType.AUDIO_CALL,
			status=Service.Status.APPROVED,
		)

		response = self.client.get('/services/')

		self.assertContains(response, 'Photo collection')
		self.assertNotContains(response, 'Old call service')

	def test_normal_users_only_browse_and_unlock_staff_services(self):
		normal_owned_service = Service.objects.create(
			staff=self.user,
			title='Private normal-user service',
			description='Not offered by staff',
			token_price=5,
			status=Service.Status.APPROVED,
		)
		self.client.force_login(self.user)

		list_response = self.client.get('/services/')
		detail_response = self.client.get(f'/services/{normal_owned_service.id}/')
		unlock_response = self.client.post(f'/services/{normal_owned_service.id}/unlock/')

		self.assertNotContains(list_response, normal_owned_service.title)
		self.assertEqual(detail_response.status_code, 404)
		self.assertEqual(unlock_response.status_code, 404)

	def test_service_owner_profile_can_be_opened_and_messaged(self):
		self.client.force_login(self.user)
		profile_url = reverse('profiles:staff_profile', args=[self.staff.id])
		conversation_url = reverse('chat:conversation', args=[self.staff.id])

		list_response = self.client.get('/services/')
		self.assertContains(list_response, profile_url)

		profile_response = self.client.get(profile_url)
		self.assertContains(profile_response, conversation_url)

		response = self.client.post(conversation_url, {'body': 'Hello'})

		self.assertRedirects(response, conversation_url)
		self.assertTrue(Message.objects.filter(
			sender=self.user, receiver=self.staff, body='Hello'
		).exists())


class ServiceStatusToggleTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			email='owner@example.com', password='pass12345', full_name='Owner',
			role=User.Role.STAFF, is_active=True,
		)
		self.other_staff = User.objects.create_user(
			email='other@example.com', password='pass12345', full_name='Other',
			role=User.Role.STAFF, is_active=True,
		)
		self.service = Service.objects.create(
			staff=self.owner,
			title='Managed gallery',
			description='A service the owner controls',
			token_price=8,
			service_type=Service.ServiceType.GENERAL,
			status=Service.Status.PENDING,
		)

	def test_owner_can_activate_and_deactivate_service(self):
		self.client.force_login(self.owner)

		self.client.post(f'/services/{self.service.id}/toggle-status/')
		self.service.refresh_from_db()
		self.assertEqual(self.service.status, Service.Status.APPROVED)
		self.assertTrue(Service.objects.filter(id=self.service.id, status=Service.Status.APPROVED).exists())

		self.client.post(f'/services/{self.service.id}/toggle-status/')
		self.service.refresh_from_db()
		self.assertEqual(self.service.status, Service.Status.DISABLED)

	def test_another_staff_member_cannot_toggle_service(self):
		self.client.force_login(self.other_staff)

		response = self.client.post(f'/services/{self.service.id}/toggle-status/')

		self.assertEqual(response.status_code, 404)
		self.service.refresh_from_db()
		self.assertEqual(self.service.status, Service.Status.PENDING)
