"""Creation of in-app notifications, respecting each user's preferences."""
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Notification, NotificationPreference


def _allowed_recipient_ids(recipients, kind):
    ids = {user.pk for user in recipients if user is not None and user.is_active}
    if not ids or kind not in NotificationPreference.KIND_FIELDS:
        return ids
    muted = NotificationPreference.objects.filter(user_id__in=ids, **{kind: False}).values_list('user_id', flat=True)
    return ids - set(muted)


def notify(recipient, kind, title, message='', link=''):
    return notify_many([recipient], kind, title, message, link)


def notify_many(recipients, kind, title, message='', link=''):
    """Create one notification per recipient (bulk insert). Returns the count."""
    if link and not (link.startswith('/') and url_has_allowed_host_and_scheme(link, allowed_hosts=set())):
        link = ''
    ids = _allowed_recipient_ids(list(recipients), kind)
    Notification.objects.bulk_create(
        [
            Notification(recipient_id=user_id, kind=kind, title=title[:140], message=message[:600], link=link)
            for user_id in ids
        ]
    )
    return len(ids)


def get_preferences(user):
    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    return preference
