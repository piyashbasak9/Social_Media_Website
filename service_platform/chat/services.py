from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification
from .models import Message


def conversation_group_name(first_user_id, second_user_id):
    user_ids = sorted((first_user_id, second_user_id))
    return f'chat_{user_ids[0]}_{user_ids[1]}'


def notification_group_name(user_id):
    return f'notifications_{user_id}'


def create_chat_message(sender_id, receiver_id, body):
    sender = User.objects.get(pk=sender_id)
    receiver = User.objects.get(pk=receiver_id)
    if sender.is_normal_user and receiver.role != User.Role.STAFF:
        raise ValueError('Normal users can only message staff users.')

    message = Message.objects.create(sender=sender, receiver=receiver, body=body)
    conversation_url = reverse('chat:conversation', kwargs={'user_id': sender.id})
    notification = Notification.objects.create(
        user=receiver,
        message=f'New message from {sender.full_name}',
        url=conversation_url,
    )
    event = {
        'type': 'chat.message',
        'message_id': message.id,
        'sender_id': sender.id,
        'receiver_id': receiver.id,
        'sender_name': sender.full_name,
        'body': message.body,
        'created_at': timezone.localtime(message.created_at).strftime('%b %d, %I:%M %p'),
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        conversation_group_name(sender.id, receiver.id), event
    )
    async_to_sync(channel_layer.group_send)(
        notification_group_name(receiver.id),
        {
            'type': 'notification.message',
            'payload': {
                'type': 'new_message',
                'notification_id': notification.id,
                'sender_id': sender.id,
                'sender_name': sender.full_name,
                'url': conversation_url,
                'unread_count': receiver.notifications.filter(is_read=False).count(),
                'unread_message_count': receiver.received_messages.filter(is_read=False).count(),
            },
        },
    )
    return message


def mark_conversation_read(user_id, partner_id):
    Message.objects.filter(
        sender_id=partner_id, receiver_id=user_id, is_read=False
    ).update(is_read=True)
    conversation_url = reverse('chat:conversation', kwargs={'user_id': partner_id})
    Notification.objects.filter(
        user_id=user_id, url=conversation_url, is_read=False
    ).update(is_read=True)
    user = User.objects.get(pk=user_id)
    async_to_sync(get_channel_layer().group_send)(
        notification_group_name(user_id),
        {
            'type': 'notification.read',
            'unread_count': user.notifications.filter(is_read=False).count(),
            'unread_message_count': user.received_messages.filter(is_read=False).count(),
        },
    )