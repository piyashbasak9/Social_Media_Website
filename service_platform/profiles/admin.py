from django.contrib import admin
from .models import NormalUserProfile, StaffProfile


@admin.register(NormalUserProfile)
class NormalUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'updated_at')


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'is_online', 'average_rating', 'total_reviews')
    list_filter = ('is_online',)