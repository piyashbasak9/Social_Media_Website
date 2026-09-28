def token_balance(request):
    """Inject token balance into all templates for logged-in users."""
    if request.user.is_authenticated:
        try:
            return {'global_token_balance': request.user.token_balance.balance}
        except Exception:
            return {'global_token_balance': 0}
    return {'global_token_balance': None}