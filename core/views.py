from django.conf import settings
from django.http import Http404, HttpResponseServerError
from django.shortcuts import redirect, render
from django.template import loader
from django.utils import timezone
from django.views.static import serve

from analytics.services import landing_stats, team_leaderboard
from challenges.models import Challenge
from community.models import Event

PRIVATE_MEDIA_PREFIXES = ('evidence/',)


def home(request):
    upcoming = (
        Event.objects.filter(status=Event.Status.PUBLISHED, end_at__gte=timezone.now()).order_by('start_at')[:3]
    )
    challenges = Challenge.objects.filter(
        status=Challenge.Status.ACTIVE, end_date__gte=timezone.localdate()
    ).order_by('end_date')[:3]
    campaigns = Event.objects.filter(
        kind=Event.Kind.CAMPAIGN, status=Event.Status.PUBLISHED, end_at__gte=timezone.now()
    ).order_by('start_at')[:3]
    return render(request, 'core/home.html', {
        'showcase_challenges': challenges,
        'showcase_campaigns': campaigns,
        'stats': landing_stats(),
        'top_teams': [team for team in team_leaderboard(public_only=True) if team.points > 0][:3],
        'upcoming_events': upcoming,
    })


def admin_root(request):
    return redirect('analytics:admin_dashboard')


def public_media(request, path):
    """Development media server that never exposes private evidence photos."""
    if path.startswith(PRIVATE_MEDIA_PREFIXES):
        raise Http404
    return serve(request, path, document_root=settings.MEDIA_ROOT)


def permission_denied(request, exception=None):
    return render(request, '403.html', status=403)


def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)


def server_error(request):
    # No request context: context processors query the database, which may be the cause of the error.
    return HttpResponseServerError(loader.render_to_string('500.html'))
