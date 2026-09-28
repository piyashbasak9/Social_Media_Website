from django.core.mail import send_mail
from django.conf import settings
from .models import EmailVerification


def send_verification_email(user):
    """Generate and send a 6-digit verification code to the user's email."""
    ev, _ = EmailVerification.objects.get_or_create(user=user)
    code = ev.regenerate()

    subject = 'Verify your account'
    message = (
        f"Hello {user.full_name},\n\n"
        f"Your verification code is: {code}\n\n"
        f"Enter this code on the verification page to activate your account.\n"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    return code