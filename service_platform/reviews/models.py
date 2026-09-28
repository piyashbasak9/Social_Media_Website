from django.conf import settings
from django.db import models


class Review(models.Model):
    """Rating + comment left by a normal user for a completed appointment."""

    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.CASCADE, related_name='review'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveSmallIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} -> {self.staff.email} ({self.rating}★)"