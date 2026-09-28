from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Notification


@login_required
def list_notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_read_view(request, notification_id):
    n = get_object_or_404(Notification, id=notification_id, user=request.user)
    n.is_read = True
    n.save()
    if n.url:
        return redirect(n.url)
    return redirect('notifications:list')


@login_required
def mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications:list')