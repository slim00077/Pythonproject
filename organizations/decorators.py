from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def org_manager_required(view_func):
    """Active, non-administrator manager of an organization (403 otherwise).

    Administrators use the global control center, which has its own views.
    The view receives the manager's own organization: it is never read from the URL,
    so a manager cannot reach another organization's records.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.can_manage_organization:
            raise PermissionDenied
        return view_func(request, request.user.affiliation, *args, **kwargs)

    return wrapper
