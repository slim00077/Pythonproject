"""Business rules of ecological challenges (member 2)."""
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from accounts.services import users_with_perm
from actions.models import ActionSubmission
from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.exceptions import BusinessRuleError
from core.permissions import REVIEW_CHALLENGES
from core.utils import percent
from gamification.models import PointTransaction
from gamification.services import award_points, evaluate_badges
from notifications.models import Notification
from notifications.services import notify, notify_many
from teams.services import get_user_team

from .models import MAX_REWARD_POINTS, Challenge, ChallengeParticipation


def can_review(user):
    return user.is_authenticated and user.is_active and user.has_perm(REVIEW_CHALLENGES)


def can_edit(user, challenge):
    if can_review(user):
        return challenge.status != Challenge.Status.ARCHIVED
    return challenge.creator_id == user.pk and challenge.status == Challenge.Status.DRAFT


def can_delete(user, challenge):
    if challenge.participations.exists():
        return False
    if can_review(user):
        return True
    return challenge.creator_id == user.pk and challenge.status == Challenge.Status.DRAFT


def can_view(user, challenge):
    if challenge.status in (Challenge.Status.ACTIVE, Challenge.Status.COMPLETED):
        return True
    return challenge.creator_id == user.pk or can_review(user) or challenge.participations.filter(user=user).exists()


def approved_count(user, challenge):
    return ActionSubmission.objects.filter(
        user=user, challenge=challenge, status=ActionSubmission.Status.APPROVED
    ).count()


def participation_progress(participation):
    done = approved_count(participation.user, participation.challenge)
    required = participation.challenge.required_actions
    return {'approved': done, 'required': required, 'percent': percent(done, required), 'ready': done >= required}


@transaction.atomic
def create_challenge(user, form):
    challenge = form.save(commit=False)
    challenge.creator = user
    challenge.organization = user.affiliation if user.can_manage_organization else None
    challenge.status = Challenge.Status.DRAFT
    challenge.save()
    log_activity(user, ActivityLog.Verb.CHALLENGE_CREATED, f'Brouillon de défi « {challenge.title} » créé.',
                 link=challenge.get_absolute_url())
    return challenge


def update_challenge(user, challenge, form):
    if not can_edit(user, challenge):
        raise BusinessRuleError('Vous ne pouvez modifier que vos propres brouillons.')
    return form.save()


@transaction.atomic
def submit_for_review(user, challenge):
    if challenge.creator_id != user.pk:
        raise BusinessRuleError('Seul le créateur peut soumettre ce défi à validation.')
    if challenge.status != Challenge.Status.DRAFT:
        raise BusinessRuleError('Seul un brouillon peut être soumis à validation.')
    challenge.status = Challenge.Status.PENDING
    challenge.save(update_fields=['status', 'updated_at'])
    log_activity(user, ActivityLog.Verb.CHALLENGE_SUBMITTED, f'Défi « {challenge.title} » soumis à validation.',
                 link=challenge.get_absolute_url())
    notify_many(
        users_with_perm(REVIEW_CHALLENGES).exclude(pk=user.pk), Notification.Kind.CHALLENGE,
        'Défi à valider', f'{user.display_name} propose le défi « {challenge.title} ».', '/admin/challenges/',
    )


@transaction.atomic
def approve_challenge(reviewer, challenge, reward_points, notes=''):
    if not can_review(reviewer):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à publier des défis.')
    challenge = Challenge.objects.select_for_update().get(pk=challenge.pk)
    if challenge.status not in (Challenge.Status.DRAFT, Challenge.Status.PENDING):
        raise BusinessRuleError('Ce défi a déjà été traité.')
    if not 0 <= reward_points <= MAX_REWARD_POINTS:
        raise BusinessRuleError(f'Les points de récompense doivent être compris entre 0 et {MAX_REWARD_POINTS}.')
    if challenge.end_date < timezone.localdate():
        raise BusinessRuleError('La date de fin de ce défi est dépassée : modifiez-la avant de le publier.')
    challenge.status = Challenge.Status.ACTIVE
    challenge.reward_points = reward_points
    challenge.review_notes = notes
    challenge.reviewed_by = reviewer
    challenge.published_at = timezone.now()
    challenge.save()
    log_activity(reviewer, ActivityLog.Verb.CHALLENGE_PUBLISHED, f'Le défi « {challenge.title} » est maintenant actif.',
                 team=None, link=challenge.get_absolute_url())
    if challenge.creator and challenge.creator_id != reviewer.pk:
        notify(challenge.creator, Notification.Kind.CHALLENGE, 'Votre défi est publié !',
               f'« {challenge.title} » a été validé avec {reward_points} points de récompense.',
               challenge.get_absolute_url())
    notify_many(
        User.objects.filter(is_active=True).exclude(pk__in=[reviewer.pk, challenge.creator_id or 0]),
        Notification.Kind.CHALLENGE, 'Nouveau défi disponible',
        f'« {challenge.title} » vient d’être lancé. Relevez-le avec votre équipe !', challenge.get_absolute_url(),
    )
    return challenge


@transaction.atomic
def reject_challenge(reviewer, challenge, notes):
    if not can_review(reviewer):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à valider des défis.')
    if challenge.status != Challenge.Status.PENDING:
        raise BusinessRuleError('Seul un défi en attente peut être renvoyé en brouillon.')
    if not notes.strip():
        raise BusinessRuleError('Expliquez au créateur ce qui doit être amélioré.')
    challenge.status = Challenge.Status.DRAFT
    challenge.review_notes = notes.strip()
    challenge.reviewed_by = reviewer
    challenge.save()
    log_activity(reviewer, ActivityLog.Verb.CHALLENGE_REJECTED, f'Défi « {challenge.title} » renvoyé en brouillon.',
                 team=None, link=challenge.get_absolute_url())
    if challenge.creator:
        notify(challenge.creator, Notification.Kind.CHALLENGE, 'Votre défi doit être retravaillé',
               notes.strip(), challenge.get_absolute_url())


ALLOWED_TRANSITIONS = {
    Challenge.Status.COMPLETED: {Challenge.Status.ACTIVE},
    Challenge.Status.ARCHIVED: {Challenge.Status.DRAFT, Challenge.Status.PENDING, Challenge.Status.ACTIVE,
                                Challenge.Status.COMPLETED},
    Challenge.Status.ACTIVE: {Challenge.Status.COMPLETED},
}


@transaction.atomic
def change_status(reviewer, challenge, new_status):
    if not can_review(reviewer):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à modifier le statut des défis.')
    if challenge.status not in ALLOWED_TRANSITIONS.get(new_status, set()):
        raise BusinessRuleError('Ce changement de statut n’est pas autorisé.')
    if new_status == Challenge.Status.ACTIVE and challenge.end_date < timezone.localdate():
        raise BusinessRuleError('Impossible de rouvrir un défi dont la date de fin est dépassée.')
    challenge.status = new_status
    challenge.save(update_fields=['status', 'updated_at'])
    log_activity(reviewer, ActivityLog.Verb.CHALLENGE_STATUS,
                 f'Défi « {challenge.title} » : statut « {challenge.get_status_display()} ».', team=None,
                 link=challenge.get_absolute_url())
    if new_status == Challenge.Status.COMPLETED:
        participants = User.objects.filter(
            challenge_participations__challenge=challenge,
            challenge_participations__status=ChallengeParticipation.Status.IN_PROGRESS,
        )
        notify_many(participants, Notification.Kind.CHALLENGE, 'Défi clôturé',
                    f'Le défi « {challenge.title} » est terminé. Validez votre réussite si vous avez atteint l’objectif.',
                    challenge.get_absolute_url())


@transaction.atomic
def join_challenge(user, challenge):
    challenge = Challenge.objects.select_for_update().get(pk=challenge.pk)
    if not challenge.is_joinable:
        raise BusinessRuleError('Ce défi n’est pas ouvert aux inscriptions.')
    participation = ChallengeParticipation.objects.filter(challenge=challenge, user=user).first()
    team = get_user_team(user)
    if participation is not None:
        if participation.status != ChallengeParticipation.Status.ABANDONED:
            raise BusinessRuleError('Vous participez déjà à ce défi.')
        participation.status = ChallengeParticipation.Status.IN_PROGRESS
        participation.team = team
        participation.save(update_fields=['status', 'team'])
    else:
        participation = ChallengeParticipation.objects.create(challenge=challenge, user=user, team=team)
    log_activity(user, ActivityLog.Verb.CHALLENGE_JOINED, f'{user.display_name} relève le défi « {challenge.title} ».',
                 team=team, link=challenge.get_absolute_url())
    return participation


@transaction.atomic
def leave_challenge(user, challenge):
    participation = ChallengeParticipation.objects.filter(
        challenge=challenge, user=user, status=ChallengeParticipation.Status.IN_PROGRESS
    ).first()
    if participation is None:
        raise BusinessRuleError('Vous ne participez pas à ce défi.')
    participation.status = ChallengeParticipation.Status.ABANDONED
    participation.save(update_fields=['status'])
    log_activity(user, ActivityLog.Verb.CHALLENGE_LEFT, f'{user.display_name} a abandonné le défi « {challenge.title} ».',
                 link=challenge.get_absolute_url())


def complete_challenge(user, challenge):
    """Mark the challenge as completed if the conditions are met, and reward once."""
    with transaction.atomic():
        participation = (
            ChallengeParticipation.objects.select_for_update()
            .filter(challenge=challenge, user=user).first()
        )
        if participation is None:
            raise BusinessRuleError('Rejoignez d’abord ce défi.')
        if participation.status == ChallengeParticipation.Status.COMPLETED:
            raise BusinessRuleError('Vous avez déjà réussi ce défi : la récompense a été attribuée.')
        if participation.status != ChallengeParticipation.Status.IN_PROGRESS:
            raise BusinessRuleError('Réinscrivez-vous à ce défi pour le valider.')
        if challenge.status not in (Challenge.Status.ACTIVE, Challenge.Status.COMPLETED):
            raise BusinessRuleError('Ce défi ne peut plus être validé.')
        progress = participation_progress(participation)
        if not progress['ready']:
            raise BusinessRuleError(
                f'Conditions non remplies : {progress["approved"]} action(s) validée(s) sur '
                f'{progress["required"]} requise(s) pour ce défi.'
            )
        team = get_user_team(user)
        participation.status = ChallengeParticipation.Status.COMPLETED
        participation.completed_at = timezone.now()
        participation.team = team
        participation.save(update_fields=['status', 'completed_at', 'team'])
        log_activity(user, ActivityLog.Verb.CHALLENGE_COMPLETED,
                     f'{user.display_name} a réussi le défi « {challenge.title} ».', team=team,
                     link=challenge.get_absolute_url())
        notify(user, Notification.Kind.CHALLENGE, 'Défi réussi !',
               f'Bravo, vous avez réussi « {challenge.title} ».', challenge.get_absolute_url())
        if challenge.reward_points:
            award_points(
                user=user, amount=challenge.reward_points, reason=PointTransaction.Reason.CHALLENGE_COMPLETED,
                reference=f'challenge:{challenge.pk}:user:{user.pk}', challenge=challenge, team=team,
                description=f'Défi réussi : {challenge.title}',
            )
        else:
            evaluate_badges(user)
    return participation


def notify_if_ready(user, challenge):
    participation = ChallengeParticipation.objects.filter(
        challenge=challenge, user=user, status=ChallengeParticipation.Status.IN_PROGRESS
    ).select_related('challenge').first()
    if participation and approved_count(user, challenge) == challenge.required_actions:
        notify(user, Notification.Kind.CHALLENGE, 'Défi prêt à être validé',
               f'Vous avez rempli les conditions du défi « {challenge.title} ». Validez votre réussite !',
               challenge.get_absolute_url())
