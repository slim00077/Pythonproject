"""Community events and campaigns rules (member 5)."""
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import User
from accounts.services import users_with_perm
from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.exceptions import BusinessRuleError
from core.permissions import REVIEW_EVENTS
from gamification.services import evaluate_badges
from notifications.models import Notification
from notifications.services import notify, notify_many
from teams.services import get_user_team

from .models import Event, EventParticipation


def can_review(user):
    return user.is_authenticated and user.is_active and user.has_perm(REVIEW_EVENTS)


def can_edit(user, event):
    if can_review(user):
        return event.status not in (Event.Status.CANCELLED, Event.Status.COMPLETED)
    return event.organizer_id == user.pk and event.status == Event.Status.DRAFT


def can_delete(user, event):
    if event.participations.exists():
        return False
    if can_review(user):
        return True
    return event.organizer_id == user.pk and event.status == Event.Status.DRAFT


def can_view(user, event):
    if event.status in (Event.Status.PUBLISHED, Event.Status.COMPLETED, Event.Status.CANCELLED):
        return True
    return event.organizer_id == user.pk or can_review(user)


def can_cancel(user, event):
    return event.status == Event.Status.PUBLISHED and (event.organizer_id == user.pk or can_review(user))


@transaction.atomic
def create_event(user, form):
    event = form.save(commit=False)
    event.organizer = user
    event.status = Event.Status.DRAFT
    event.save()
    log_activity(user, ActivityLog.Verb.EVENT_CREATED, f'Brouillon « {event.title} » créé.', link=event.get_absolute_url())
    return event


def update_event(user, event, form):
    if not can_edit(user, event):
        raise BusinessRuleError('Vous ne pouvez modifier que vos propres brouillons.')
    return form.save()


@transaction.atomic
def submit_for_review(user, event):
    if event.organizer_id != user.pk:
        raise BusinessRuleError('Seul l’organisateur peut soumettre cet événement.')
    if event.status != Event.Status.DRAFT:
        raise BusinessRuleError('Seul un brouillon peut être soumis à validation.')
    event.status = Event.Status.PENDING
    event.save(update_fields=['status', 'updated_at'])
    notify_many(users_with_perm(REVIEW_EVENTS).exclude(pk=user.pk), Notification.Kind.EVENT, 'Événement à valider',
                f'{user.display_name} propose « {event.title} ».', '/admin/events/')


@transaction.atomic
def publish_event(reviewer, event, notes=''):
    if not can_review(reviewer):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à publier des événements.')
    event = Event.objects.select_for_update().get(pk=event.pk)
    if event.status not in (Event.Status.DRAFT, Event.Status.PENDING):
        raise BusinessRuleError('Cet événement a déjà été traité.')
    if event.end_at < timezone.now():
        raise BusinessRuleError('Cet événement est déjà terminé : modifiez ses dates avant de le publier.')
    event.status = Event.Status.PUBLISHED
    event.review_notes = notes.strip()
    event.reviewed_by = reviewer
    event.published_at = timezone.now()
    event.save()
    log_activity(reviewer, ActivityLog.Verb.EVENT_PUBLISHED, f'« {event.title} » est publié.', team=None,
                 link=event.get_absolute_url())
    if event.organizer and event.organizer_id != reviewer.pk:
        notify(event.organizer, Notification.Kind.EVENT, 'Votre événement est publié !',
               f'« {event.title} » est désormais visible par la communauté.', event.get_absolute_url())
    label = 'Nouvel événement' if event.kind == Event.Kind.EVENT else 'Nouvelle campagne'
    notify_many(
        User.objects.filter(is_active=True).exclude(pk__in=[reviewer.pk, event.organizer_id or 0]),
        Notification.Kind.EVENT, f'{label} : {event.title}',
        f'Le {timezone.localtime(event.start_at):%d/%m/%Y} — inscrivez-vous dès maintenant.', event.get_absolute_url(),
    )
    return event


@transaction.atomic
def reject_event(reviewer, event, notes):
    if not can_review(reviewer):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à valider des événements.')
    if event.status != Event.Status.PENDING:
        raise BusinessRuleError('Seul un événement en attente peut être renvoyé en brouillon.')
    if not notes.strip():
        raise BusinessRuleError('Expliquez à l’organisateur ce qui doit être amélioré.')
    event.status = Event.Status.DRAFT
    event.review_notes = notes.strip()
    event.reviewed_by = reviewer
    event.save()
    if event.organizer:
        notify(event.organizer, Notification.Kind.EVENT, 'Votre événement doit être retravaillé', notes.strip(),
               event.get_absolute_url())


@transaction.atomic
def cancel_event(actor, event, reason=''):
    if not can_cancel(actor, event):
        raise BusinessRuleError('Vous ne pouvez pas annuler cet événement.')
    event.status = Event.Status.CANCELLED
    event.review_notes = reason.strip()
    event.save(update_fields=['status', 'review_notes', 'updated_at'])
    log_activity(actor, ActivityLog.Verb.EVENT_STATUS, f'« {event.title} » a été annulé.', team=None,
                 link=event.get_absolute_url())
    notify_many(event.participants.all(), Notification.Kind.EVENT, 'Événement annulé',
                f'« {event.title} » a été annulé. {reason.strip()}'.strip(), event.get_absolute_url())


@transaction.atomic
def complete_event(reviewer, event):
    if not can_review(reviewer):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à clôturer des événements.')
    if event.status != Event.Status.PUBLISHED:
        raise BusinessRuleError('Seul un événement publié peut être clôturé.')
    event.status = Event.Status.COMPLETED
    event.save(update_fields=['status', 'updated_at'])
    log_activity(reviewer, ActivityLog.Verb.EVENT_STATUS, f'« {event.title} » est terminé.', team=None,
                 link=event.get_absolute_url())


def join_event(user, event):
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event.pk)
        if event.status != Event.Status.PUBLISHED:
            raise BusinessRuleError('Cet événement n’est pas ouvert aux inscriptions.')
        if event.has_ended:
            raise BusinessRuleError('Cet événement est terminé.')
        if EventParticipation.objects.filter(event=event, user=user).exists():
            raise BusinessRuleError('Vous êtes déjà inscrit·e à cet événement.')
        if event.capacity is not None and event.participations.count() >= event.capacity:
            raise BusinessRuleError('Il n’y a plus de place disponible.')
        team = get_user_team(user)
        try:
            with transaction.atomic():
                participation = EventParticipation.objects.create(event=event, user=user, team=team)
        except IntegrityError:
            raise BusinessRuleError('Vous êtes déjà inscrit·e à cet événement.')
        log_activity(user, ActivityLog.Verb.EVENT_JOINED, f'{user.display_name} participe à « {event.title} ».',
                     team=team, link=event.get_absolute_url())
        if event.organizer and event.organizer_id != user.pk:
            notify(event.organizer, Notification.Kind.EVENT, 'Nouvelle inscription',
                   f'{user.display_name} s’est inscrit·e à « {event.title} ».', event.get_absolute_url())
        evaluate_badges(user)
    return participation


@transaction.atomic
def leave_event(user, event):
    participation = EventParticipation.objects.filter(event=event, user=user).first()
    if participation is None:
        raise BusinessRuleError('Vous n’êtes pas inscrit·e à cet événement.')
    if event.has_started:
        raise BusinessRuleError('L’événement a commencé : la désinscription n’est plus possible.')
    participation.delete()
    log_activity(user, ActivityLog.Verb.EVENT_LEFT, f'{user.display_name} s’est désinscrit·e de « {event.title} ».',
                 link=event.get_absolute_url())


def send_due_reminders(user=None):
    """Notify participants of published events starting within the reminder window (once)."""
    now = timezone.now()
    window_end = now + timedelta(hours=settings.ECOTEAMS_EVENT_REMINDER_HOURS)
    participations = EventParticipation.objects.filter(
        reminder_sent=False, event__status=Event.Status.PUBLISHED,
        event__start_at__gt=now, event__start_at__lte=window_end,
    ).select_related('event', 'user')
    if user is not None:
        participations = participations.filter(user=user)
    sent = 0
    for participation in participations:
        event = participation.event
        notify(participation.user, Notification.Kind.EVENT, f'Bientôt : {event.title}',
               f'Rendez-vous le {timezone.localtime(event.start_at):%d/%m/%Y à %H:%M}'
               f'{" — " + event.location if event.location else ""}.', event.get_absolute_url())
        EventParticipation.objects.filter(pk=participation.pk).update(reminder_sent=True)
        sent += 1
    return sent
