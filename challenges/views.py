from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from actions.models import ActionSubmission
from core.decorators import any_permission_required
from core.exceptions import BusinessRuleError
from core.permissions import REVIEW_CHALLENGES

from . import services
from .forms import ChallengeFilterForm, ChallengeForm, ChallengeReviewForm
from .models import Challenge, ChallengeParticipation

ACTIVE_PARTICIPANTS = Q(participations__status__in=['in_progress', 'completed'])


def _visible_challenge(request, slug):
    challenge = get_object_or_404(Challenge.objects.select_related('creator'), slug=slug)
    if not services.can_view(request.user, challenge):
        raise Http404
    return challenge


@login_required
def challenge_list(request):
    form = ChallengeFilterForm(request.GET or None)
    challenges = Challenge.objects.annotate(participant_total=Count('participations', filter=ACTIVE_PARTICIPANTS))
    scope = request.GET.get('scope', '')
    if scope == 'org':
        # « Défis d'entreprise »: only the challenges proposed by the user's own organization.
        challenges = challenges.filter(organization_id=request.user.affiliation_id) if request.user.affiliation_id             else challenges.none()
    status, sort = 'active', 'ending'
    if form.is_valid():
        data = form.cleaned_data
        status = data['status'] or 'active'
        sort = data['sort'] or 'ending'
        if data['q']:
            challenges = challenges.filter(Q(title__icontains=data['q']) | Q(description__icontains=data['q']))
        if data['category']:
            challenges = challenges.filter(category=data['category'])
        if data['difficulty']:
            challenges = challenges.filter(difficulty=data['difficulty'])
    visible = {
        'active': [Challenge.Status.ACTIVE],
        'completed': [Challenge.Status.COMPLETED],
        'all': [Challenge.Status.ACTIVE, Challenge.Status.COMPLETED],
    }[status]
    challenges = challenges.filter(status__in=visible)
    ordering = {
        'recent': ['-published_at', '-created_at'], 'points': ['-reward_points'],
        'popular': ['-participant_total', 'end_date'],
    }
    challenges = challenges.order_by(*ordering.get(sort, ['end_date', 'title']))
    page = Paginator(challenges, 9).get_page(request.GET.get('page'))
    mine = dict(
        ChallengeParticipation.objects.filter(user=request.user, challenge__in=list(page))
        .values_list('challenge_id', 'status')
    )
    return render(request, 'challenges/challenge_list.html', {'form': form, 'page': page, 'mine': mine, 'scope': scope})


@login_required
def my_challenges(request):
    participations = list(
        ChallengeParticipation.objects.filter(user=request.user).select_related('challenge').order_by('status', '-joined_at')
    )
    for participation in participations:
        participation.progress = services.participation_progress(participation)
    created = Challenge.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'challenges/my_challenges.html', {
        'participations': participations, 'created': created,
    })


@login_required
def challenge_detail(request, slug):
    challenge = _visible_challenge(request, slug)
    participation = ChallengeParticipation.objects.filter(challenge=challenge, user=request.user).first()
    progress = services.participation_progress(participation) if participation else None
    participations = challenge.participations.exclude(status=ChallengeParticipation.Status.ABANDONED)
    team_rows = (
        participations.filter(team__isnull=False).values('team__name', 'team__slug')
        .annotate(total=Count('pk'), done=Count('pk', filter=Q(status='completed'))).order_by('-done', '-total')[:6]
    )
    my_actions = ActionSubmission.objects.filter(user=request.user, challenge=challenge).select_related('action_type')
    return render(request, 'challenges/challenge_detail.html', {
        'challenge': challenge,
        'participation': participation,
        'progress': progress,
        'participant_total': participations.count(),
        'completed_total': participations.filter(status=ChallengeParticipation.Status.COMPLETED).count(),
        'recent_participants': participations.select_related('user', 'team')[:8],
        'team_rows': team_rows,
        'my_actions': my_actions,
        'instructions': [line.strip('-• ').strip() for line in challenge.instructions.splitlines() if line.strip()],
        'can_edit': services.can_edit(request.user, challenge),
        'can_delete': services.can_delete(request.user, challenge),
        'can_review': services.can_review(request.user),
        'is_creator': challenge.creator_id == request.user.pk,
    })


@login_required
def challenge_create(request):
    initial = {'start_date': timezone.localdate(), 'end_date': timezone.localdate() + timedelta(days=14)}
    form = ChallengeForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        challenge = services.create_challenge(request.user, form)
        messages.success(request, 'Brouillon enregistré. Soumettez-le à validation lorsqu’il est prêt.')
        return redirect(challenge)
    return render(request, 'challenges/challenge_form.html', {'form': form, 'is_create': True})


@login_required
def challenge_update(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)
    if not services.can_edit(request.user, challenge):
        raise PermissionDenied
    form = ChallengeForm(request.POST or None, request.FILES or None, instance=challenge)
    if request.method == 'POST' and form.is_valid():
        services.update_challenge(request.user, challenge, form)
        messages.success(request, 'Le défi a été mis à jour.')
        return redirect(challenge)
    return render(request, 'challenges/challenge_form.html', {'form': form, 'challenge': challenge, 'is_create': False})


@login_required
def challenge_delete(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)
    if not services.can_delete(request.user, challenge):
        raise PermissionDenied
    if request.method == 'POST':
        title = challenge.title
        challenge.delete()
        messages.success(request, f'Le défi « {title} » a été supprimé.')
        return redirect('challenges:mine')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'le défi « {challenge.title} »',
        'warning': 'Cette suppression est définitive.',
        'cancel_url': challenge.get_absolute_url(),
    })


def _run(request, action, success_message, challenge, *args):
    try:
        action(request.user, challenge, *args)
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, success_message)
    return redirect(challenge)


@login_required
@require_POST
def challenge_submit(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug, creator=request.user)
    return _run(request, services.submit_for_review, 'Défi soumis à validation. Vous serez notifié·e de la décision.',
                challenge)


@login_required
@require_POST
def challenge_join(request, slug):
    challenge = _visible_challenge(request, slug)
    return _run(request, services.join_challenge, 'C’est parti ! Déclarez vos actions en les liant à ce défi.', challenge)


@login_required
@require_POST
def challenge_leave(request, slug):
    challenge = _visible_challenge(request, slug)
    return _run(request, services.leave_challenge, 'Vous avez abandonné ce défi.', challenge)


@login_required
@require_POST
def challenge_complete(request, slug):
    challenge = _visible_challenge(request, slug)
    return _run(request, services.complete_challenge, 'Défi réussi ! Votre récompense a été ajoutée au registre.',
                challenge)


# --- Back-office --------------------------------------------------------------

@any_permission_required(REVIEW_CHALLENGES)
def review_list(request):
    tab = request.GET.get('tab', 'pending')
    tabs = {
        'pending': [Challenge.Status.PENDING],
        'active': [Challenge.Status.ACTIVE],
        'drafts': [Challenge.Status.DRAFT],
        'closed': [Challenge.Status.COMPLETED, Challenge.Status.ARCHIVED],
    }
    statuses = tabs.get(tab, tabs['pending'])
    challenges = (
        Challenge.objects.filter(status__in=statuses).select_related('creator')
        .annotate(participant_total=Count('participations', filter=ACTIVE_PARTICIPANTS))
        .order_by('-updated_at')
    )
    counts = {key: Challenge.objects.filter(status__in=value).count() for key, value in tabs.items()}
    page = Paginator(challenges, 15).get_page(request.GET.get('page'))
    return render(request, 'challenges/admin/review_list.html', {'page': page, 'tab': tab, 'counts': counts})


@any_permission_required(REVIEW_CHALLENGES)
def review_detail(request, slug):
    challenge = get_object_or_404(Challenge.objects.select_related('creator', 'reviewed_by'), slug=slug)
    form = ChallengeReviewForm(request.POST or None, initial={'reward_points': challenge.reward_points})
    if request.method == 'POST':
        decision = request.POST.get('decision')
        try:
            if decision in ('approve', 'reject'):
                if not form.is_valid():
                    raise BusinessRuleError('Vérifiez le formulaire de validation.')
                if decision == 'approve':
                    services.approve_challenge(request.user, challenge, form.cleaned_data['reward_points'],
                                               form.cleaned_data['notes'])
                    messages.success(request, f'« {challenge.title} » est publié.')
                else:
                    services.reject_challenge(request.user, challenge, form.cleaned_data['notes'])
                    messages.success(request, f'« {challenge.title} » a été renvoyé en brouillon.')
            elif decision in ('completed', 'archived', 'active'):
                services.change_status(request.user, challenge, decision)
                messages.success(request, 'Statut du défi mis à jour.')
            else:
                raise BusinessRuleError('Décision inconnue.')
        except BusinessRuleError as error:
            messages.error(request, error.message)
        else:
            return redirect('challenges_admin:review_list')
    return render(request, 'challenges/admin/review_detail.html', {
        'challenge': challenge, 'form': form,
        'participant_total': challenge.participations.exclude(status='abandoned').count(),
    })
