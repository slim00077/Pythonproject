from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from analytics.services import annotate_team_stats, team_dashboard, team_leaderboard
from core.exceptions import BusinessRuleError

from . import services
from .ai import TeamActivityGenerationError, generate_team_activity_ideas
from .forms import TeamFilterForm, TeamForm
from .models import Membership, Team


@login_required
def team_list(request):
    form = TeamFilterForm(request.GET or None)
    teams = annotate_team_stats(Team.objects.exclude(status=Team.Status.ARCHIVED).select_related('captain'))
    sort = 'points'
    if form.is_valid():
        data = form.cleaned_data
        if data['q']:
            teams = teams.filter(Q(name__icontains=data['q']) | Q(motto__icontains=data['q'])
                                 | Q(description__icontains=data['q']))
        if data['focus_area']:
            teams = teams.filter(focus_area=data['focus_area'])
        if data['open_only']:
            teams = teams.filter(status=Team.Status.ACTIVE, is_open=True, member_total__lt=F('max_members'))
        sort = data['sort'] or 'points'
    ordering = {'name': ['name'], 'members': ['-member_total', 'name'], 'recent': ['-created_at']}
    teams = teams.order_by(*ordering.get(sort, ['-points', 'name']))
    ranks = {team.pk: team.rank for team in team_leaderboard()}
    page = Paginator(teams, 9).get_page(request.GET.get('page'))
    for team in page:
        team.rank = ranks.get(team.pk)
    return render(request, 'teams/team_list.html', {
        'form': form, 'page': page, 'my_membership': services.get_membership(request.user),
    })


@login_required
def my_team(request):
    team = services.get_user_team(request.user)
    if team is None:
        messages.info(request, 'Vous ne faites encore partie d’aucune équipe : rejoignez-en une ou créez la vôtre.')
        return redirect('teams:list')
    return redirect(team)


@login_required
def team_create(request):
    current = services.get_user_team(request.user)
    if current is not None:
        messages.warning(request, f'Vous faites déjà partie de l’équipe « {current.name} ».')
        return redirect(current)
    form = TeamForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            team = services.create_team(request.user, form)
        except BusinessRuleError as error:
            messages.error(request, error.message)
        else:
            messages.success(request, f'L’équipe « {team.name} » est créée. Vous en êtes le capitaine !')
            return redirect(team)
    return render(request, 'teams/team_form.html', {'form': form, 'is_create': True})


@login_required
def team_detail(request, slug):
    team = get_object_or_404(Team.objects.select_related('captain'), slug=slug)
    return _render_team_detail(request, team)


def _render_team_detail(request, team, activity_ideas=None):
    membership = services.get_membership(request.user)
    is_member = membership is not None and membership.team_id == team.pk
    stats = team_dashboard(team)
    return render(request, 'teams/team_detail.html', {
        'team': team,
        'stats': stats,
        'category_chart': [{'label': row['label'], 'value': row['count']} for row in stats['categories']],
        'is_member': is_member,
        'is_captain': services.is_captain(request.user, team),
        'can_manage': services.can_manage_team(request.user, team),
        'can_join': membership is None and team.accepts_members,
        'my_membership': membership,
        'activity_ideas': activity_ideas,
    })


@login_required
@require_POST
def team_activity_ideas(request, slug):
    team = get_object_or_404(Team.objects.select_related('captain'), slug=slug)
    try:
        activity_ideas = generate_team_activity_ideas(team)
    except TeamActivityGenerationError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, 'Les idées d’activités ont été générées par le modèle local.')
        return _render_team_detail(request, team, activity_ideas=activity_ideas)
    return _render_team_detail(request, team)


def _managed_team(request, slug):
    team = get_object_or_404(Team, slug=slug)
    if not services.can_manage_team(request.user, team):
        raise PermissionDenied
    return team


@login_required
def team_update(request, slug):
    team = _managed_team(request, slug)
    form = TeamForm(request.POST or None, request.FILES or None, instance=team)
    if request.method == 'POST' and form.is_valid():
        services.update_team(request.user, team, form)
        messages.success(request, 'Les informations de l’équipe ont été mises à jour.')
        return redirect(team)
    return render(request, 'teams/team_form.html', {'form': form, 'team': team, 'is_create': False})


@login_required
def team_delete(request, slug):
    team = _managed_team(request, slug)
    if request.method == 'POST':
        name = team.name
        services.delete_team(request.user, team)
        messages.success(request, f'L’équipe « {name} » a été supprimée.')
        return redirect('teams:list')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'l’équipe « {team.name} »',
        'warning': 'Les membres seront retirés de l’équipe. Leurs points personnels sont conservés, '
                   'mais l’équipe disparaîtra du classement.',
        'cancel_url': team.get_absolute_url(),
    })


@login_required
@require_POST
def team_join(request, slug):
    team = get_object_or_404(Team, slug=slug)
    try:
        services.join_team(request.user, team)
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f'Bienvenue dans l’équipe « {team.name} » !')
    return redirect(team)


@login_required
@require_POST
def team_leave(request, slug):
    team = get_object_or_404(Team, slug=slug)
    membership = services.get_membership(request.user)
    if membership is None or membership.team_id != team.pk:
        messages.error(request, 'Vous ne faites pas partie de cette équipe.')
        return redirect(team)
    try:
        services.leave_team(request.user)
    except BusinessRuleError as error:
        messages.error(request, error.message)
        return redirect(team)
    messages.success(request, f'Vous avez quitté l’équipe « {team.name} ».')
    return redirect('teams:list')


@login_required
@require_POST
def member_remove(request, slug, user_id):
    team = _managed_team(request, slug)
    member = get_object_or_404(User, pk=user_id)
    try:
        services.remove_member(request.user, team, member)
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f'{member.display_name} a été retiré·e de l’équipe.')
    return redirect(team)


@login_required
@require_POST
def captain_transfer(request, slug, user_id):
    team = _managed_team(request, slug)
    member = get_object_or_404(Membership, team=team, user_id=user_id).user
    try:
        services.transfer_captaincy(request.user, team, member)
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f'{member.display_name} est désormais capitaine de l’équipe.')
    return redirect(team)
