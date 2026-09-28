from django.db import transaction
from django.core.exceptions import ValidationError
from .models import TokenBalance, TokenTransaction


@transaction.atomic
def credit_tokens(user, amount, performed_by=None, description='', tx_type=TokenTransaction.Type.CREDIT):
    """Add tokens to a user with row-level locking for concurrency safety."""
    if amount <= 0:
        raise ValidationError('Credit amount must be positive.')

    # Lock the row while we update it (prevents race conditions)
    tb, _ = TokenBalance.objects.select_for_update().get_or_create(user=user)
    tb.balance = tb.balance + amount
    tb.save()

    TokenTransaction.objects.create(
        user=user,
        performed_by=performed_by,
        transaction_type=tx_type,
        amount=amount,
        balance_after=tb.balance,
        description=description,
    )
    return tb.balance


@transaction.atomic
def debit_tokens(user, amount, performed_by=None, description=''):
    """Deduct tokens (used for purchases). Raises ValidationError on insufficient balance."""
    if amount <= 0:
        raise ValidationError('Debit amount must be positive.')

    tb, _ = TokenBalance.objects.select_for_update().get_or_create(user=user)
    if tb.balance < amount:
        raise ValidationError('Insufficient token balance.')

    tb.balance = tb.balance - amount
    tb.save()

    TokenTransaction.objects.create(
        user=user,
        performed_by=performed_by,
        transaction_type=TokenTransaction.Type.DEBIT,
        amount=-amount,
        balance_after=tb.balance,
        description=description,
    )
    return tb.balance