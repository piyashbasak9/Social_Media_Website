from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_email_verified', 'is_approved', 'is_active', 'is_blocked')
    list_filter = ('role', 'is_email_verified', 'is_approved', 'is_active', 'is_blocked')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('full_name',)}),
        ('Role & Status', {
            'fields': ('role', 'is_active', 'is_email_verified', 'is_approved', 'is_blocked',
                       'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'role', 'is_active', 'is_email_verified', 'is_approved'),
        }),
    )


admin.site.register(EmailVerification)