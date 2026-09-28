from django.conf import settings
from django.db import models


class NormalUserProfile(models.Model):
    """Profile for normal (customer) users."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='normal_profile'
    )
    profile_photo = models.ImageField(upload_to='profiles/normal/', blank=True, null=True)
    bio = models.TextField(blank=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Normal Profile: {self.user.email}"


class StaffProfile(models.Model):
    """Profile for staff (service provider) users."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile'
    )
    profile_photo = models.ImageField(upload_to='profiles/staff/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='profiles/staff/cover/', blank=True, null=True)
    bio = models.TextField(blank=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    location = models.CharField(max_length=150, blank=True)
    is_online = models.BooleanField(default=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Staff Profile: {self.user.email}"