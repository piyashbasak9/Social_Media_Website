from .models import Notification


def create_notification(user, message, url=''):
    """Convenience helper to create a notification."""
    return Notification.objects.create(user=user, message=message, url=url)