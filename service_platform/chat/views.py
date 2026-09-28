from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Message

User = get_user_model()


@login_required
def inbox_view(request):
    """Show list of conversations (unique users talked with)."""
    user = request.user
    msgs = Message.objects.filter(Q(sender=user) | Q(receiver=user))
    partner_ids = set()
    for m in msgs:
        partner_ids.add(m.receiver_id if m.sender_id == user.id else m.sender_id)
    partners = User.objects.filter(id__in=partner_ids)
    return render(request, 'chat/inbox.html', {'partners': partners})


@login_required
def conversation_view(request, user_id):
    partner = get_object_or_404(User, id=user_id)
    if partner == request.user:
        return redirect('chat:inbox')

    # Mark messages from partner as read
    Message.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(sender=request.user, receiver=partner, body=body)
            return redirect('chat:conversation', user_id=partner.id)

    msgs = Message.objects.filter(
        Q(sender=request.user, receiver=partner) | Q(sender=partner, receiver=request.user)
    )
    return render(request, 'chat/conversation.html', {'partner': partner, 'messages': msgs})