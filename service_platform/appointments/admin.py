from django.contrib import admin
from .models import Appointment, ServicePurchase, StaffAvailability


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff', 'service', 'scheduled_time', 'status')
    list_filter = ('status', 'appointment_type')


@admin.register(ServicePurchase)
class ServicePurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'tokens_spent', 'purchased_at', 'status')
    list_filter = ('status',)


admin.site.register(StaffAvailability)