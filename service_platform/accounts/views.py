from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .forms import (
    RegistrationForm, EmailLoginForm, EmailVerificationForm,
    PasswordResetRequestForm, PasswordResetConfirmForm,
)
from .models import User, EmailVerification
from .utils import send_verification_email


def register_view(request):
    """Handle new user registration."""
    if request.user.is_authenticated:
        return redirect('posts:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user)
            messages.success(
                request,
                'Registration successful! Please check your email for the verification code.'
            )
            # Save email in session so verification page can find the user
            request.session['pending_verify_email'] = user.email
            return redirect('accounts:verify_email')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email_view(request):
    """Verify the 6-digit code to activate the account."""
    email = request.session.get('pending_verify_email')
    if not email:
        messages.error(request, 'No pending verification. Please register first.')
        return redirect('accounts:register')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:register')

    if user.is_email_verified:
        messages.info(request, 'Email already verified. You may login.')
        return redirect('accounts:login')

    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            ev = getattr(user, 'email_verification', None)
            if ev and not ev.is_used and ev.code == code:
                ev.is_used = True
                ev.save()
                user.is_email_verified = True

                # Staff accounts need admin approval; Normal users can be active right away
                if user.role == User.Role.STAFF:
                    user.is_active = False
                    messages.info(
                        request,
                        'Email verified! Your staff account is pending admin approval.'
                    )
                else:
                    user.is_active = True
                    messages.success(request, 'Email verified! You can now login.')

                user.save()
                request.session.pop('pending_verify_email', None)
                return redirect('accounts:login')
            else:
                messages.error(request, 'Invalid or already-used verification code.')
    else:
        form = EmailVerificationForm()

    return render(request, 'accounts/verify_email.html', {'form': form, 'email': email})


def resend_verification_view(request):
    """Resend verification code to pending user."""
    email = request.session.get('pending_verify_email')
    if not email:
        return redirect('accounts:register')
    try:
        user = User.objects.get(email=email)
        send_verification_email(user)
        messages.success(request, 'A new verification code has been sent.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    return redirect('accounts:verify_email')


def login_view(request):
    """Login using email and password."""
    if request.user.is_authenticated:
        return redirect('posts:home')

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_blocked:
                messages.error(request, 'Your account has been blocked. Please contact support.')
                return render(request, 'accounts/login.html', {'form': form})
            if not user.is_email_verified:
                messages.error(request, 'Please verify your email first.')
                request.session['pending_verify_email'] = user.email
                return redirect('accounts:verify_email')
            if not user.is_active:
                messages.error(request, 'Account is not active yet. Please verify your email or wait for approval.')
                return render(request, 'accounts/login.html', {'form': form})
            if user.role == User.Role.STAFF and not user.is_approved:
                messages.warning(request, 'Your staff account is pending admin approval.')
                return render(request, 'accounts/login.html', {'form': form})
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name}!')
            return redirect('posts:home')
    else:
        form = EmailLoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout current user."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


def password_reset_request_view(request):
    """Request a password reset code via email."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            user = User.objects.filter(email=email).first()
            if user:
                ev, _ = EmailVerification.objects.get_or_create(user=user)
                code = ev.regenerate()
                send_mail(
                    'Password reset code',
                    f'Your password reset code is: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            # Always show success (avoid email enumeration)
            messages.success(request, 'If the email exists, a reset code was sent.')
            request.session['reset_email'] = email
            return redirect('accounts:password_reset_confirm')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request):
    """Confirm password reset using code."""
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email=email).first()
            ev = getattr(user, 'email_verification', None) if user else None
            if user and ev and ev.code == form.cleaned_data['code']:
                p1 = form.cleaned_data['password1']
                p2 = form.cleaned_data['password2']
                if p1 != p2:
                    messages.error(request, 'Passwords do not match.')
                else:
                    user.set_password(p1)
                    user.save()
                    ev.is_used = True
                    ev.save()
                    request.session.pop('reset_email', None)
                    messages.success(request, 'Password reset successful. Please login.')
                    return redirect('accounts:login')
            else:
                messages.error(request, 'Invalid code.')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})