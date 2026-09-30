from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import Http404

from accounts.models import User
from .models import NormalUserProfile, StaffProfile
from .forms import NormalProfileForm, StaffProfileForm
from tokens.models import TokenBalance
from services.models import Service
from posts.models import Post
from reviews.models import Review


@login_required
def my_profile_view(request):
    """Redirect to the correct profile page based on the user's role."""
    user = request.user
    if user.is_super_admin or user.is_staff_user:
        return redirect('profiles:staff_profile', user_id=user.id)
    return redirect('profiles:normal_profile', user_id=user.id)


@login_required
def staff_directory_view(request):
    """List and search staff users by name or ID."""
    query = request.GET.get('q', '').strip()
    staff_users = User.objects.filter(role=User.Role.STAFF)
    if query:
        search_filter = Q(full_name__icontains=query)
        if query.isdecimal() and len(query) <= 18:
            search_filter |= Q(id=int(query))
        staff_users = staff_users.filter(search_filter)
    return render(request, 'profiles/staff_directory.html', {
        'staff_users': staff_users.order_by('full_name', 'id'),
        'query': query,
    })


@login_required
def edit_profile_view(request):
    """Edit profile for the currently logged-in user."""
    user = request.user
    if user.is_super_admin or user.is_staff_user:
        profile, _ = StaffProfile.objects.get_or_create(user=user)
        FormClass = StaffProfileForm
    else:
        profile, _ = NormalUserProfile.objects.get_or_create(user=user)
        FormClass = NormalProfileForm

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profiles:my_profile')
    else:
        form = FormClass(instance=profile)
    return render(request, 'profiles/edit_profile.html', {'form': form})


@login_required
def staff_profile_view(request, user_id):
    """Public staff profile view with About / Services / Posts / Reviews sections."""
    staff_user = get_object_or_404(User, id=user_id, role__in=[User.Role.STAFF, User.Role.SUPER_ADMIN])
    if request.user.is_normal_user and staff_user.role != User.Role.STAFF:
        raise Http404
    profile, _ = StaffProfile.objects.get_or_create(user=staff_user)

    approved_services = Service.objects.filter(
        staff=staff_user,
        status=Service.Status.APPROVED,
        service_type=Service.ServiceType.GENERAL,
    )
    posts = Post.objects.filter(staff=staff_user).order_by('-created_at')
    reviews = Review.objects.filter(staff=staff_user).order_by('-created_at')

    context = {
        'staff_user': staff_user,
        'profile': profile,
        'services': approved_services,
        'posts': posts,
        'reviews': reviews,
    }
    return render(request, 'profiles/staff_profile.html', context)


@login_required
def normal_profile_view(request, user_id):
    """View a normal user's personal profile (only owner can see full details)."""
    user = get_object_or_404(User, id=user_id, role=User.Role.NORMAL)
    if request.user.is_normal_user and request.user.id != user.id:
        raise Http404
    profile, _ = NormalUserProfile.objects.get_or_create(user=user)

    # Only owner (or super admin) can see token / purchase details
    is_owner = request.user.id == user.id or request.user.is_super_admin
    balance = None
    if is_owner:
        tb, _ = TokenBalance.objects.get_or_create(user=user)
        balance = tb.balance

    context = {
        'profile_user': user,
        'profile': profile,
        'balance': balance,
        'is_owner': is_owner,
    }
    return render(request, 'profiles/normal_profile.html', context)