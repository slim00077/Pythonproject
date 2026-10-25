from .permissions import (
    ADJUST_POINTS,
    MANAGE_ACTION_TYPES,
    MANAGE_BADGES,
    MODERATE_ACTIONS,
    REVIEW_CHALLENGES,
    REVIEW_EVENTS,
    VIEW_REPORTS,
    has_backoffice_access,
    is_admin,
)


def navigation(request):
    """Expose the back-office capabilities of the current user to templates.

    These flags only decide which links are displayed: every view performs
    its own server-side permission check.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'nav': {'backoffice': False}}
    nav = {
        'backoffice': has_backoffice_access(user),
        'is_admin': is_admin(user),
        'moderate_actions': user.has_perm(MODERATE_ACTIONS),
        'manage_action_types': user.has_perm(MANAGE_ACTION_TYPES),
        'review_challenges': user.has_perm(REVIEW_CHALLENGES),
        'review_events': user.has_perm(REVIEW_EVENTS),
        'manage_badges': user.has_perm(MANAGE_BADGES),
        'adjust_points': user.has_perm(ADJUST_POINTS),
        'view_reports': user.has_perm(VIEW_REPORTS),
    }
    if nav['moderate_actions']:
        from actions.models import ActionSubmission
        nav['pending_actions'] = ActionSubmission.objects.filter(status=ActionSubmission.Status.PENDING).count()
    if nav['review_challenges']:
        from challenges.models import Challenge
        nav['pending_challenges'] = Challenge.objects.filter(status=Challenge.Status.PENDING).count()
    if nav['review_events']:
        from community.models import Event
        nav['pending_events'] = Event.objects.filter(status=Event.Status.PENDING).count()
    return {'nav': nav}
