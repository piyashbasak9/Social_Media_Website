def notification_counter(request):
    """Expose unread notification count to every template."""
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        unread_messages = request.user.received_messages.filter(is_read=False).count()
        unread_message_partners = request.user.received_messages.filter(
            is_read=False
        ).values_list('sender_id', flat=True).distinct()
        return {
            'unread_notifications': count,
            'unread_messages': unread_messages,
            'unread_message_partners': unread_message_partners,
        }
    return {'unread_notifications': 0, 'unread_messages': 0, 'unread_message_partners': []}