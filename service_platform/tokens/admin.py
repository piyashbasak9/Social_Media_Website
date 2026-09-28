from django.contrib import admin
from .models import TokenBalance, TokenTransaction


@admin.register(TokenBalance)
class TokenBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')


@admin.register(TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'balance_after', 'performed_by', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('user__email',)