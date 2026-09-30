from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model

from .services import (
    conversation_group_name,
    create_chat_message,
    mark_conversation_read,
    notification_group_name,
)

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.partner_id = self.scope['url_route']['kwargs']['user_id']
        if not self.user.is_authenticated or self.partner_id == self.user.id:
            await self.close(code=4401)
            return

        partner_role = await self.get_partner_role()
        if partner_role is None or (self.user.is_normal_user and partner_role != User.Role.STAFF):
            await self.close(code=4403)
            return

        self.group_name = conversation_group_name(self.user.id, self.partner_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'read':
            await self.mark_read()
            return

        if content.get('type') != 'message':
            return
        body = content.get('body', '').strip()
        if not body or len(body) > 5000:
            return
        await self.save_message(self.user.id, self.partner_id, body)

    async def chat_message(self, event):
        await self.send_json({key: value for key, value in event.items() if key != 'type'})

    @database_sync_to_async
    def get_partner_role(self):
        return User.objects.filter(pk=self.partner_id).values_list('role', flat=True).first()

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, body):
        create_chat_message(sender_id, receiver_id, body)

    @database_sync_to_async
    def mark_read(self):
        mark_conversation_read(self.user.id, self.partner_id)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = notification_group_name(self.user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        await self.send_json(event['payload'])

    async def notification_read(self, event):
        await self.send_json({
            'type': 'unread_count',
            'count': event['unread_count'],
            'unread_message_count': event['unread_message_count'],
        })