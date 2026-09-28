from django.conf import settings
from django.db import models
from django.utils import timezone


class Service(models.Model):
    """A service offered by a staff user."""

    class ServiceType(models.TextChoices):
        GENERAL = 'general', 'Photo/Video Showcase Service'
        AUDIO_CALL = 'audio_call', 'Audio Call Service'
        VIDEO_CALL = 'video_call', 'Video Call Service'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        DISABLED = 'disabled', 'Disabled'

    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='services'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    token_price = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(default=30)
    service_type = models.CharField(
        max_length=20, choices=ServiceType.choices, default=ServiceType.GENERAL
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.token_price} tokens"


class ServiceMedia(models.Model):
    """Media (image/video) attached to a service."""

    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to='services/media/')
    thumbnail = models.ImageField(upload_to='services/thumbnails/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.media_type} for {self.service.title}"