from django.conf import settings
from django.db import models


class TokenBalance(models.Model):
    """Current token balance for a user (typically a normal user)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_balance'
    )
    balance = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}: {self.balance}"


class TokenTransaction(models.Model):
    """Full history of every token credit / debit / refund / adjustment."""

    class Type(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'
        REFUND = 'refund', 'Refund'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_transactions'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='token_actions'
    )
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    amount = models.IntegerField()                # Positive for credits, negative for debits
    balance_after = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} {self.transaction_type} {self.amount}"