import asyncio

from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification
from service_platform.asgi import application
from .models import Message


class ChatVisibilityTests(TestCase):
	def setUp(self):
		self.normal_user = User.objects.create_user(
			email='customer@example.com', password='pass12345', full_name='Customer',
			role=User.Role.NORMAL, is_active=True,
		)
		self.other_normal_user = User.objects.create_user(
			email='other@example.com', password='pass12345', full_name='Other Customer',
			role=User.Role.NORMAL, is_active=True,
		)
		self.staff_user = User.objects.create_user(
			email='staff@example.com', password='pass12345', full_name='Studio Staff',
			role=User.Role.STAFF, is_active=True,
		)

	def test_normal_users_cannot_open_or_message_other_normal_users(self):
		self.client.force_login(self.normal_user)
		conversation_url = reverse('chat:conversation', args=[self.other_normal_user.id])

		get_response = self.client.get(conversation_url)
		post_response = self.client.post(conversation_url, {'body': 'Hello'})

		self.assertEqual(get_response.status_code, 404)
		self.assertEqual(post_response.status_code, 404)
		self.assertFalse(Message.objects.exists())

	def test_normal_users_can_message_staff_and_only_see_staff_in_inbox(self):
		Message.objects.create(
			sender=self.normal_user, receiver=self.other_normal_user, body='Old private message'
		)
		self.client.force_login(self.normal_user)

		response = self.client.post(
			reverse('chat:conversation', args=[self.staff_user.id]), {'body': 'Hello staff'}
		)
		inbox_response = self.client.get(reverse('chat:inbox'))

		self.assertEqual(response.status_code, 302)
		self.assertContains(inbox_response, 'Studio Staff')
		self.assertNotContains(inbox_response, 'Other Customer')
		self.assertTrue(Message.objects.filter(
			sender=self.normal_user, receiver=self.staff_user, body='Hello staff'
		).exists())
		self.assertTrue(Notification.objects.filter(
			user=self.staff_user, message='New message from Customer', is_read=False
		).exists())

	def test_inbox_marks_unread_conversations_bold(self):
		Message.objects.create(
			sender=self.staff_user, receiver=self.normal_user, body='Unread message',
		)
		self.client.force_login(self.normal_user)

		response = self.client.get(reverse('chat:inbox'))

		self.assertContains(response, 'fw-bold')
		self.assertContains(response, '1 unread')
		self.assertContains(response, 'id="nav-chat-unread"')
		self.assertContains(response, 'href="/notifications/"')
		self.assertContains(response, 'id="nav-notification-unread"')
		self.assertNotContains(response, 'live-message-toast')

	def test_message_string_representation_is_not_shown_as_a_label(self):
		message = Message.objects.create(
			sender=self.normal_user, receiver=self.staff_user, body='Hello',
		)

		self.assertEqual(str(message), '')
		self.assertNotIn('@', str(message))

	def test_conversation_ui_does_not_render_internal_message_label(self):
		Message.objects.create(
			sender=self.normal_user, receiver=self.staff_user, body='Hello',
		)
		self.client.force_login(self.staff_user)

		response = self.client.get(reverse('chat:conversation', args=[self.normal_user.id]))

		self.assertContains(response, 'Hello')
		self.assertNotContains(response, 'Chat message')
		self.assertNotContains(response, 'admin11@gmail.com -> admin@gmail.com')

	def test_staff_can_reply_to_a_normal_user(self):
		self.client.force_login(self.staff_user)

		response = self.client.get(reverse('chat:conversation', args=[self.normal_user.id]))

		self.assertContains(response, 'Back to messages')
		self.assertContains(response, reverse('chat:inbox'))


class ChatWebsocketTests(TransactionTestCase):
	def setUp(self):
		self.normal_user = User.objects.create_user(
			email='socket-customer@example.com', password='pass12345', full_name='Socket Customer',
			role=User.Role.NORMAL, is_active=True,
		)
		self.staff_user = User.objects.create_user(
			email='socket-staff@example.com', password='pass12345', full_name='Socket Staff',
			role=User.Role.STAFF, is_active=True,
		)
		self.other_normal_user = User.objects.create_user(
			email='socket-other@example.com', password='pass12345', full_name='Other Customer',
			role=User.Role.NORMAL, is_active=True,
		)

	def websocket_headers(self, user):
		client = Client()
		client.force_login(user)
		cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
		return [(b'cookie', f'{settings.SESSION_COOKIE_NAME}={cookie}'.encode())]

	def test_normal_users_cannot_open_other_normal_users_socket(self):
		headers = self.websocket_headers(self.normal_user)

		async def connect_to_normal_user():
			communicator = WebsocketCommunicator(
				application,
				f'/ws/chat/{self.other_normal_user.id}/',
				headers=headers,
			)
			connected, _ = await communicator.connect()
			self.assertFalse(connected)

		asyncio.run(connect_to_normal_user())

	def test_messages_and_notifications_are_delivered_over_websockets(self):
		sender_headers = self.websocket_headers(self.normal_user)
		receiver_headers = self.websocket_headers(self.staff_user)

		async def exercise_sockets():
			sender_socket = WebsocketCommunicator(
				application,
				f'/ws/chat/{self.staff_user.id}/',
				headers=sender_headers,
			)
			receiver_socket = WebsocketCommunicator(
				application,
				f'/ws/chat/{self.normal_user.id}/',
				headers=receiver_headers,
			)
			notification_socket = WebsocketCommunicator(
				application,
				'/ws/notifications/',
				headers=receiver_headers,
			)
			connected_sender, _ = await sender_socket.connect()
			connected_receiver, _ = await receiver_socket.connect()
			connected_notifications, _ = await notification_socket.connect()
			self.assertTrue(connected_sender)
			self.assertTrue(connected_receiver)
			self.assertTrue(connected_notifications)

			await sender_socket.send_json_to({'type': 'message', 'body': 'Live message'})
			sender_event = await sender_socket.receive_json_from(timeout=2)
			receiver_event = await receiver_socket.receive_json_from(timeout=2)
			notification_event = await notification_socket.receive_json_from(timeout=2)
			self.assertEqual(sender_event['body'], 'Live message')
			self.assertEqual(receiver_event['body'], 'Live message')
			self.assertEqual(notification_event['type'], 'new_message')
			self.assertEqual(notification_event['sender_name'], 'Socket Customer')
			self.assertEqual(notification_event['unread_count'], 1)
			self.assertEqual(notification_event['unread_message_count'], 1)

			await receiver_socket.send_json_to({'type': 'read'})
			read_event = await notification_socket.receive_json_from(timeout=2)
			self.assertEqual(read_event['type'], 'unread_count')
			self.assertEqual(read_event['count'], 0)
			self.assertEqual(read_event['unread_message_count'], 0)
			await sender_socket.disconnect()
			await receiver_socket.disconnect()
			await notification_socket.disconnect()

		asyncio.run(exercise_sockets())
		self.assertTrue(Message.objects.filter(body='Live message').exists())
		self.assertTrue(Notification.objects.filter(
			user=self.staff_user, message='New message from Socket Customer', is_read=True
		).exists())
