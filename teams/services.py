"""Business rules of teams and memberships (member 1)."""
from django.db import IntegrityError, transaction

from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.exceptions import BusinessRuleError
from notifications.models import Notification
from notifications.services import notify, notify_many

from .models import Membership, Team


def get_membership(user):
    if not user or not user.is_authenticated:
        return None
    return Membership.objects.filter(user=user).select_related('team').first()


def get_user_team(user):
    membership = get_membership(user)
    return membership.team if membership else None


def is_captain(user, team):
    return bool(user.is_authenticated and team.captain_id == user.pk)


def can_manage_team(user, team):
    return is_captain(user, team) or (user.is_authenticated and user.is_superuser)


def _team_users(team, exclude=None):
    qs = team.members.filter(is_active=True)
    if exclude is not None:
        qs = qs.exclude(pk=exclude.pk)
    return list(qs)


@transaction.atomic
def create_team(user, form):
    """Save a validated ``TeamForm``; the creator becomes the captain."""
    if Membership.objects.filter(user=user).exists():
        raise BusinessRuleError('Vous faites déjà partie d’une équipe. Quittez-la avant d’en créer une nouvelle.')
    team = form.save(commit=False)
    team.captain = user
    team.save()
    Membership.objects.create(team=team, user=user, role=Membership.Role.CAPTAIN)
    log_activity(user, ActivityLog.Verb.TEAM_CREATED, f'{user.display_name} a créé l’équipe « {team.name} ».',
                 team=team, link=team.get_absolute_url())
    return team


def update_team(user, team, form):
    if not can_manage_team(user, team):
        raise BusinessRuleError('Seul le capitaine peut modifier les informations de l’équipe.')
    team = form.save()
    log_activity(user, ActivityLog.Verb.TEAM_UPDATED, f'Informations de l’équipe « {team.name} » mises à jour.',
                 team=team, link=team.get_absolute_url())
    return team


def join_team(user, team):
    with transaction.atomic():
        team = Team.objects.select_for_update().get(pk=team.pk)
        if Membership.objects.filter(user=user).exists():
            raise BusinessRuleError('Vous faites déjà partie d’une équipe : une seule équipe par participant.')
        if team.status != Team.Status.ACTIVE:
            raise BusinessRuleError('Cette équipe n’accepte pas de nouveaux membres pour le moment.')
        if not team.is_open:
            raise BusinessRuleError('Cette équipe est fermée aux nouvelles inscriptions.')
        if team.memberships.count() >= team.max_members:
            raise BusinessRuleError('Cette équipe est complète.')
        try:
            with transaction.atomic():
                Membership.objects.create(team=team, user=user, role=Membership.Role.MEMBER)
        except IntegrityError:
            raise BusinessRuleError('Vous faites déjà partie d’une équipe.')
        log_activity(user, ActivityLog.Verb.TEAM_JOINED, f'{user.display_name} a rejoint l’équipe « {team.name} ».',
                     team=team, link=team.get_absolute_url())
        notify_many(
            _team_users(team, exclude=user), Notification.Kind.TEAM, 'Nouveau membre dans l’équipe',
            f'{user.display_name} a rejoint « {team.name} ». Souhaitez-lui la bienvenue !', team.get_absolute_url(),
        )
    return team


@transaction.atomic
def leave_team(user):
    membership = get_membership(user)
    if membership is None:
        raise BusinessRuleError('Vous ne faites partie d’aucune équipe.')
    team = membership.team
    if team.captain_id == user.pk:
        raise BusinessRuleError(
            'Le capitaine ne peut pas quitter son équipe : transférez d’abord le rôle de capitaine '
            'ou supprimez l’équipe.'
        )
    membership.delete()
    log_activity(user, ActivityLog.Verb.TEAM_LEFT, f'{user.display_name} a quitté l’équipe « {team.name} ».',
                 team=team, link=team.get_absolute_url())
    notify(team.captain, Notification.Kind.TEAM, 'Un membre a quitté l’équipe',
           f'{user.display_name} a quitté « {team.name} ».', team.get_absolute_url())
    return team


@transaction.atomic
def remove_member(actor, team, member):
    if not can_manage_team(actor, team):
        raise BusinessRuleError('Seul le capitaine peut retirer un membre.')
    if member.pk == team.captain_id:
        raise BusinessRuleError('Le capitaine ne peut pas être retiré de l’équipe.')
    deleted, _ = Membership.objects.filter(team=team, user=member).delete()
    if not deleted:
        raise BusinessRuleError('Cette personne ne fait pas partie de l’équipe.')
    log_activity(actor, ActivityLog.Verb.MEMBER_REMOVED,
                 f'{member.display_name} a été retiré·e de l’équipe « {team.name} ».',
                 team=team, link=team.get_absolute_url())
    notify(member, Notification.Kind.TEAM, 'Vous avez été retiré·e d’une équipe',
           f'Le capitaine de « {team.name} » vous a retiré·e de l’équipe. Vous pouvez en rejoindre une autre.',
           '/teams/')


@transaction.atomic
def transfer_captaincy(actor, team, new_captain):
    if not can_manage_team(actor, team):
        raise BusinessRuleError('Seul le capitaine peut transférer son rôle.')
    target = Membership.objects.filter(team=team, user=new_captain).first()
    if target is None:
        raise BusinessRuleError('Le nouveau capitaine doit être membre de l’équipe.')
    if target.role == Membership.Role.CAPTAIN:
        raise BusinessRuleError('Cette personne est déjà capitaine.')
    # update() ne passe pas par Membership.save() : on libère explicitement
    # captain_of, sinon l'index unique refuserait le nouveau capitaine.
    Membership.objects.filter(team=team, role=Membership.Role.CAPTAIN).update(
        role=Membership.Role.MEMBER, captain_of=None
    )
    target.role = Membership.Role.CAPTAIN
    target.save(update_fields=['role'])
    team.captain = new_captain
    team.save(update_fields=['captain', 'updated_at'])
    log_activity(actor, ActivityLog.Verb.CAPTAIN_CHANGED,
                 f'{new_captain.display_name} est le nouveau capitaine de « {team.name} ».',
                 team=team, link=team.get_absolute_url())
    notify(new_captain, Notification.Kind.TEAM, 'Vous êtes capitaine !',
           f'Vous êtes désormais capitaine de l’équipe « {team.name} ».', team.get_absolute_url())


@transaction.atomic
def delete_team(actor, team):
    if not can_manage_team(actor, team):
        raise BusinessRuleError('Seul le capitaine peut supprimer l’équipe.')
    members = _team_users(team, exclude=actor)
    name = team.name
    log_activity(actor, ActivityLog.Verb.TEAM_DELETED, f'L’équipe « {name} » a été supprimée.', team=None)
    team.delete()
    notify_many(members, Notification.Kind.TEAM, 'Équipe supprimée',
                f'L’équipe « {name} » a été supprimée par son capitaine. Vos points personnels sont conservés.',
                '/teams/')
