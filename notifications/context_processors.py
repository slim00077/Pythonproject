from .models import Notification


def notifications(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    qs = Notification.objects.filter(recipient=user)
    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'latest_notifications': list(qs[:6]),
    }
