"""Central list of the permissions that open parts of the EcoTeams back-office.

Superusers implicitly hold every permission (``User.has_perm`` returns True
for active superusers). Custom roles created by the administrator can be
granted a subset of these permissions.
"""

MODERATE_ACTIONS = 'actions.moderate_actionsubmission'
MANAGE_ACTION_TYPES = 'actions.change_ecoactiontype'
REVIEW_CHALLENGES = 'challenges.review_challenge'
REVIEW_EVENTS = 'community.review_event'
MANAGE_BADGES = 'gamification.change_badge'
ADJUST_POINTS = 'gamification.adjust_points'
VIEW_REPORTS = 'analytics.view_reports'

BACKOFFICE_PERMISSIONS = [
    MODERATE_ACTIONS,
    MANAGE_ACTION_TYPES,
    REVIEW_CHALLENGES,
    REVIEW_EVENTS,
    MANAGE_BADGES,
    ADJUST_POINTS,
    VIEW_REPORTS,
]


def is_admin(user):
    return bool(user.is_authenticated and user.is_active and user.is_superuser)


def has_backoffice_access(user):
    if not (user.is_authenticated and user.is_active):
        return False
    return user.is_superuser or any(user.has_perm(perm) for perm in BACKOFFICE_PERMISSIONS)
