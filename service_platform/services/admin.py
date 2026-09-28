from django.contrib import admin
from .models import Service, ServiceMedia


class ServiceMediaInline(admin.TabularInline):
    model = ServiceMedia
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'staff', 'token_price', 'duration_minutes', 'service_type', 'status', 'created_at')
    list_filter = ('status', 'service_type')
    search_fields = ('title', 'staff__email')
    inlines = [ServiceMediaInline]