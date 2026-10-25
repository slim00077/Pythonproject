from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.utils import safe_next_url

from .forms import PreferenceForm
from .models import Notification
from .services import get_preferences


def _own_notification(request, pk):
    # Filtering on the recipient makes other users' notifications return 404.
    return get_object_or_404(Notification, pk=pk, recipient=request.user)


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    show = request.GET.get('show', 'all')
    kind = request.GET.get('kind', '')
    if show == 'unread':
        notifications = notifications.filter(is_read=False)
    if kind in Notification.Kind.values:
        notifications = notifications.filter(kind=kind)
    page = Paginator(notifications, 15).get_page(request.GET.get('page'))
    return render(request, 'notifications/notification_list.html', {
        'page': page, 'show': show, 'kind': kind, 'kinds': Notification.Kind.choices,
    })


@login_required
def notification_detail(request, pk):
    notification = _own_notification(request, pk)
    notification.mark_read()
    return render(request, 'notifications/notification_detail.html', {'notification': notification})


@login_required
@require_POST
def notification_read(request, pk):
    notification = _own_notification(request, pk)
    notification.mark_read()
    if request.POST.get('follow') and notification.link:
        return redirect(notification.link)
    return redirect(safe_next_url(request, '/notifications/'))


@login_required
@require_POST
def notification_read_all(request):
    updated = Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    messages.success(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    return redirect(safe_next_url(request, '/notifications/'))


@login_required
@require_POST
def notification_delete(request, pk):
    _own_notification(request, pk).delete()
    messages.success(request, 'Notification supprimée.')
    return redirect(safe_next_url(request, '/notifications/'))


@login_required
def preferences(request):
    preference = get_preferences(request.user)
    form = PreferenceForm(request.POST or None, instance=preference)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Préférences de notification enregistrées.')
        return redirect('notifications:preferences')
    return render(request, 'notifications/preferences.html', {'form': form})
