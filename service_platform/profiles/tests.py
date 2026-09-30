from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class StaffDirectoryTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='customer@example.com', password='pass12345', full_name='Customer',
			role=User.Role.NORMAL, is_active=True,
		)
		self.other_user = User.objects.create_user(
			email='other@example.com', password='pass12345', full_name='Other Customer',
			role=User.Role.NORMAL, is_active=True,
		)
		self.staff = User.objects.create_user(
			email='staff@example.com', password='pass12345', full_name='Studio Staff',
			role=User.Role.STAFF, is_active=True,
		)

	def test_normal_user_can_search_staff_by_name_and_id(self):
		self.client.force_login(self.user)

		name_response = self.client.get(reverse('profiles:staff_directory'), {'q': 'Studio'})
		self.assertContains(name_response, 'Studio Staff')
		self.assertContains(name_response, str(self.staff.id))
		self.assertNotContains(name_response, 'Other Customer')

		id_response = self.client.get(reverse('profiles:staff_directory'), {'q': str(self.staff.id)})
		self.assertContains(id_response, 'Studio Staff')
		self.assertNotContains(id_response, 'Other Customer')

	def test_normal_user_cannot_view_another_normal_users_profile(self):
		self.client.force_login(self.user)

		response = self.client.get(reverse('profiles:normal_profile', args=[self.other_user.id]))

		self.assertEqual(response.status_code, 404)
