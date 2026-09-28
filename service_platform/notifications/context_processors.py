def notification_counter(request):
    """Expose unread notification count to every template."""
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications': count}
    return {'unread_notifications': 0}