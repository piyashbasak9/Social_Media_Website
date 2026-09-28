from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Restrict view access to specific user roles."""

    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied('You do not have permission to access this page.')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def super_admin_required(view_func):
    return role_required('super_admin')(view_func)


def staff_required(view_func):
    # Staff users are the only ones allowed to create and manage services.
    return role_required('staff')(view_func)


def normal_user_required(view_func):
    # Normal users are the only ones allowed to purchase or book services.
    return role_required('normal')(view_func)