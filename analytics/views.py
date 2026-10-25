import csv

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from community.services import send_due_reminders
from core.choices import EcoCategory
from core.decorators import any_permission_required, backoffice_required, superuser_required
from core.permissions import VIEW_REPORTS
from gamification.models import PointTransaction
from gamification.services import user_points
from teams.services import get_user_team

from . import dashboards, services
from .models import ActivityLog

REPORT_PERIODS = {'week': '7 derniers jours', 'month': '30 derniers jours', 'quarter': '90 derniers jours',
                  'year': '12 derniers mois', 'all': 'Depuis le début'}


@login_required
def dashboard(request):
    """Each account category has its own dashboard; administrators use the control center."""
    user = request.user
    if user.is_superuser:
        return redirect('analytics:admin_dashboard')
    send_due_reminders(user)
    if user.organization_type == user.OrganizationType.EMPLOYEE:
        data = dashboards.employee_dashboard(user)
        return render(request, 'analytics/dashboard_employee.html', {
            'd': data, 'weekly_chart': data['weekly_points'], 'category_chart': data['categories'],
        })
    if user.organization_type == user.OrganizationType.ASSOCIATION:
        data = dashboards.association_dashboard(user)
        return render(request, 'analytics/dashboard_association.html', {
            'd': data, 'registrations_chart': data.get('weekly_registrations', []),
        })
    stats = services.user_dashboard(user)
    return render(request, 'analytics/dashboard_student.html', {
        'stats': stats,
        'daily_chart': stats['daily_points'],
        'weekly_chart': stats['weekly_points'],
    })


@login_required
def leaderboard(request):
    period = request.GET.get('period', 'all')
    period = period if period in services.PERIODS else 'all'
    category = request.GET.get('category', '')
    category = category if category in EcoCategory.values else ''
    sort = request.GET.get('sort', 'points')
    sort = sort if sort in services.LEADERBOARD_SORTS else 'points'
    scope = request.GET.get('scope', '')
    organization = None
    if scope == 'org':
        organization = request.user.affiliation
        if organization is None:
            scope = ''
    rows = services.team_leaderboard(period=period, category=category, sort=sort, organization=organization,
                                     viewer=request.user)
    podium = sorted([row for row in rows if row.points > 0], key=lambda team: team.rank)[:3]
    return render(request, 'analytics/leaderboard.html', {
        'rows': rows,
        'podium': podium,
        'my_team': get_user_team(request.user),
        'top_users': services.user_leaderboard(period=period, limit=10),
        'period': period, 'category': category, 'sort': sort, 'scope': scope, 'organization': organization,
        'periods': services.PERIODS, 'sorts': services.LEADERBOARD_SORTS, 'categories': EcoCategory.choices,
        'chart': [{'label': row.name, 'value': row.points} for row in sorted(rows, key=lambda t: t.rank)[:8]],
    })


@login_required
def history(request):
    tab = request.GET.get('tab', 'activity')
    user = request.user
    context = {'tab': tab, 'points': user_points(user)}
    if tab == 'points':
        entries = PointTransaction.objects.filter(user=user).select_related('team', 'submission', 'challenge')
        reason = request.GET.get('reason', '')
        if reason in PointTransaction.Reason.values:
            entries = entries.filter(reason=reason)
        context.update({
            'page': Paginator(entries, 15).get_page(request.GET.get('page')),
            'reason': reason, 'reasons': PointTransaction.Reason.choices,
        })
    else:
        activities = ActivityLog.objects.filter(actor=user).select_related('team')
        context['page'] = Paginator(activities, 15).get_page(request.GET.get('page'))
    context['weekly_chart'] = services.weekly_series(
        PointTransaction.objects.filter(user=user), 'created_at', 12, 'amount')
    return render(request, 'analytics/history.html', context)


@backoffice_required
def admin_dashboard(request):
    overview = services.admin_overview()
    overview.update(dashboards.admin_counters())
    return render(request, 'analytics/admin_dashboard.html', {
        'o': overview,
        'weekly_points_chart': overview['weekly_points'],
        'weekly_users_chart': overview['weekly_users'],
        'status_chart': overview['status_breakdown'],
        'category_chart': [{'label': row['label'], 'value': row['count']} for row in overview['categories']],
    })


@any_permission_required(VIEW_REPORTS)
def reports(request):
    period = request.GET.get('period', 'month')
    period = period if period in REPORT_PERIODS else 'month'
    report = services.engagement_report(period)
    return render(request, 'analytics/reports.html', {
        'r': report, 'period': period, 'periods': REPORT_PERIODS,
        'category_chart': [{'label': row['label'], 'value': float(row['co2'])} for row in report['categories']],
    })


@any_permission_required(VIEW_REPORTS)
def reports_export(request):
    period = request.GET.get('period', 'month')
    period = period if period in REPORT_PERIODS else 'month'
    report = services.engagement_report(period)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f'ecoteams-rapport-{period}-{timezone.localdate():%Y%m%d}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('﻿')
    writer = csv.writer(response, delimiter=';')
    writer.writerow([f'Rapport EcoTeams — {REPORT_PERIODS[period]}', f'généré le {timezone.localtime():%d/%m/%Y %H:%M}'])
    writer.writerow([])
    writer.writerow(['Équipes'])
    writer.writerow(['Rang', 'Équipe', 'Points (registre)', 'Membres', 'Actions validées', 'Défis réussis',
                     'CO₂ évité estimé (kg)'])
    for team in report['teams']:
        writer.writerow([team.rank, team.name, team.points, team.member_total, team.approved_actions,
                         team.completed_challenges, f'{team.co2_estimate:.2f}'.replace('.', ',')])
    writer.writerow([])
    writer.writerow(['Catégories'])
    writer.writerow(['Catégorie', 'Actions validées', 'Points', 'CO₂ évité estimé (kg)'])
    for row in report['categories']:
        writer.writerow([row['label'], row['count'], row['points'], f'{row["co2"]:.2f}'.replace('.', ',')])
    writer.writerow([])
    writer.writerow(['Défis'])
    writer.writerow(['Défi', 'Statut', 'Participants', 'Réussites', 'Taux de réussite (%)'])
    for row in report['challenges']:
        writer.writerow([row['challenge'].title, row['challenge'].get_status_display(), row['participants'],
                         row['completed'], row['rate']])
    writer.writerow([])
    writer.writerow(['Les valeurs de CO₂ sont des estimations calculées à partir des facteurs configurés.'])
    return response


@superuser_required
def admin_stats(request):
    stats = dashboards.admin_statistics()
    return render(request, 'analytics/admin_stats.html', {'s': stats})


@superuser_required
def audit_log(request):
    logs = ActivityLog.objects.select_related('actor', 'team')
    query = request.GET.get('q', '').strip()
    verb = request.GET.get('verb', '')
    if query:
        logs = logs.filter(Q(description__icontains=query) | Q(actor__username__icontains=query)
                           | Q(actor__first_name__icontains=query) | Q(actor__last_name__icontains=query))
    if verb in ActivityLog.Verb.values:
        logs = logs.filter(verb=verb)
    page = Paginator(logs, 25).get_page(request.GET.get('page'))
    return render(request, 'analytics/audit_log.html', {
        'page': page, 'query': query, 'verb': verb, 'verbs': ActivityLog.Verb.choices,
    })
