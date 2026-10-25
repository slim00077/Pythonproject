from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .permissions import has_backoffice_access, is_admin


def _guard(test):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not test(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def superuser_required(view_func):
    """Only an active Django superuser may run the view (403 otherwise)."""
    return _guard(is_admin)(view_func)


def backoffice_required(view_func):
    return _guard(has_backoffice_access)(view_func)


def any_permission_required(*perms):
    """Allow the view when the user holds at least one of ``perms``."""
    return _guard(lambda user: user.is_active and any(user.has_perm(perm) for perm in perms))
