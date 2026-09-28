from django.contrib import admin
from .models import Report, Block


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reported_user', 'reason', 'status', 'created_at')
    list_filter = ('reason', 'status')


admin.site.register(Block)