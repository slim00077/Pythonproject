from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import any_permission_required
from core.exceptions import BusinessRuleError
from core.permissions import ADJUST_POINTS, MANAGE_BADGES

from . import services
from .forms import BadgeForm, PointAdjustmentForm
from .models import Badge, PointTransaction


@login_required
def achievements(request):
    user = request.user
    rows = services.badge_progress(user)
    ledger = PointTransaction.objects.filter(user=user)
    by_reason = {
        row['reason']: row['total']
        for row in ledger.order_by().values('reason').annotate(total=Sum('amount'))
    }
    return render(request, 'gamification/achievements.html', {
        'rows': rows,
        'earned_total': sum(1 for row in rows if row['award']),
        'points': services.user_points(user),
        'streak': services.compute_streaks(user),
        'by_reason': [(label, by_reason.get(value, 0)) for value, label in PointTransaction.Reason.choices],
    })


# --- Back-office: badges -------------------------------------------------------

@any_permission_required(MANAGE_BADGES)
def badge_list(request):
    badges = Badge.objects.annotate(award_total=Count('awards')).order_by('rule', 'threshold')
    return render(request, 'gamification/admin/badge_list.html', {'badges': badges})


@any_permission_required(MANAGE_BADGES)
def badge_form(request, pk=None):
    badge = get_object_or_404(Badge, pk=pk) if pk else None
    form = BadgeForm(request.POST or None, instance=badge)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        messages.success(request, f'Badge « {saved.name} » enregistré.')
        return redirect('gamification:badge_list')
    return render(request, 'gamification/admin/badge_form.html', {'form': form, 'badge': badge})


@any_permission_required(MANAGE_BADGES)
def badge_delete(request, pk):
    badge = get_object_or_404(Badge, pk=pk)
    if badge.awards.exists():
        messages.error(request, 'Ce badge a déjà été obtenu : désactivez-le plutôt que de le supprimer.')
        return redirect('gamification:badge_list')
    if request.method == 'POST':
        badge.delete()
        messages.success(request, 'Badge supprimé.')
        return redirect('gamification:badge_list')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'le badge « {badge.name} »',
        'warning': 'Ce badge n’a encore été obtenu par personne.',
        'cancel_url': '/admin/badges/',
    })


# --- Back-office: points ledger ------------------------------------------------

@any_permission_required(ADJUST_POINTS)
def ledger(request):
    entries = PointTransaction.objects.select_related('user', 'team', 'created_by')
    reason = request.GET.get('reason', '')
    query = request.GET.get('q', '').strip()
    if reason in PointTransaction.Reason.values:
        entries = entries.filter(reason=reason)
    if query:
        entries = entries.filter(Q(user__username__icontains=query) | Q(description__icontains=query)
                                 | Q(team__name__icontains=query))
    totals = PointTransaction.objects.aggregate(
        awarded=Coalesce(Sum('amount', filter=Q(amount__gt=0)), 0),
        removed=Coalesce(Sum('amount', filter=Q(amount__lt=0)), 0),
    )
    page = Paginator(entries, 20).get_page(request.GET.get('page'))
    return render(request, 'gamification/admin/ledger.html', {
        'page': page, 'reason': reason, 'query': query, 'reasons': PointTransaction.Reason.choices,
        'totals': totals, 'form': PointAdjustmentForm(),
    })


@any_permission_required(ADJUST_POINTS)
def adjust(request):
    form = PointAdjustmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.adjust_points(
                admin=request.user, user=form.cleaned_data['user'],
                amount=form.cleaned_data['amount'], reason=form.cleaned_data['reason'],
            )
        except BusinessRuleError as error:
            messages.error(request, error.message)
        else:
            messages.success(request, 'Correction enregistrée dans le registre des points.')
            return redirect('gamification:ledger')
    return render(request, 'gamification/admin/adjust_form.html', {'form': form})
