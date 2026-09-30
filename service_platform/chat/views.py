from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.http import Http404

from .models import Message
from .services import create_chat_message, mark_conversation_read

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
    if user.is_normal_user:
        partners = partners.filter(role=User.Role.STAFF)
    partners = partners.annotate(
        unread_count=Count(
            'sent_messages',
            filter=Q(sent_messages__receiver=user, sent_messages__is_read=False),
        )
    ).order_by('full_name', 'id')
    return render(request, 'chat/inbox.html', {'partners': partners})


@login_required
def conversation_view(request, user_id):
    partner = get_object_or_404(User, id=user_id)
    if partner == request.user:
        return redirect('chat:inbox')
    if request.user.is_normal_user and partner.role != User.Role.STAFF:
        raise Http404

    mark_conversation_read(request.user.id, partner.id)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body and len(body) <= 5000:
            create_chat_message(request.user.id, partner.id, body)
            return redirect('chat:conversation', user_id=partner.id)

    msgs = Message.objects.filter(
        Q(sender=request.user, receiver=partner) | Q(sender=partner, receiver=request.user)
    ).select_related('sender', 'receiver')
    return render(request, 'chat/conversation.html', {'partner': partner, 'messages': msgs})