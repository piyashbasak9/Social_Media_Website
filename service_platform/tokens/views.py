from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import super_admin_required, staff_required
from accounts.models import User
from .models import TokenBalance, TokenTransaction
from .services import credit_tokens, debit_tokens


@login_required
def my_tokens_view(request):
    """Show current token balance and full transaction history for the current user."""
    tb, _ = TokenBalance.objects.get_or_create(user=request.user)
    txs = TokenTransaction.objects.filter(user=request.user)
    return render(request, 'tokens/my_tokens.html', {'balance': tb.balance, 'transactions': txs})


@staff_required
def give_tokens_view(request):
    """Staff or Super Admin can give tokens to a Normal user."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            amount = int(request.POST.get('amount', 0))
        except ValueError:
            amount = 0
        description = request.POST.get('description', '').strip() or f'Granted by {request.user.email}'

        if amount <= 0:
            messages.error(request, 'Amount must be positive.')
            return render(request, 'tokens/give_tokens.html')

        target = User.objects.filter(email=email, role=User.Role.NORMAL).first()
        if not target:
            messages.error(request, 'Normal user not found with that email.')
            return render(request, 'tokens/give_tokens.html')

        credit_tokens(target, amount, performed_by=request.user, description=description)
        messages.success(request, f'{amount} tokens given to {target.email}.')
        return redirect('tokens:my_tokens')
    return render(request, 'tokens/give_tokens.html')


@super_admin_required
def adjust_tokens_view(request):
    """Super admin manual adjustment (positive or negative)."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            amount = int(request.POST.get('amount', 0))
        except ValueError:
            amount = 0
        target = User.objects.filter(email=email).first()
        if not target:
            messages.error(request, 'User not found.')
        elif amount == 0:
            messages.error(request, 'Amount cannot be zero.')
        else:
            try:
                if amount > 0:
                    credit_tokens(target, amount, performed_by=request.user,
                                  description='Admin adjustment')
                else:
                    debit_tokens(target, -amount, performed_by=request.user,
                                 description='Admin adjustment')
                messages.success(request, 'Adjustment applied.')
            except Exception as e:
                messages.error(request, str(e))
        return redirect('tokens:all_transactions')
    return render(request, 'tokens/adjust.html')


@super_admin_required
def all_transactions_view(request):
    """Super admin view of all token transactions."""
    txs = TokenTransaction.objects.all().select_related('user', 'performed_by')
    return render(request, 'tokens/all_transactions.html', {'transactions': txs})