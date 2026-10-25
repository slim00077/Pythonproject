"""Personalized, explainable event recommendations without external services."""
from collections import Counter
from dataclasses import dataclass
from math import log1p

from django.db.models import Count
from django.utils import timezone

from actions.models import ActionSubmission
from challenges.models import ChallengeParticipation
from core.choices import EcoCategory
from gamification.models import UserBadge
from gamification.services import user_points
from teams.services import get_user_team

from community.models import Event, EventParticipation
from community.services import audience_allows


@dataclass(frozen=True)
class EventRecommendation:
    event: Event
    score: float
    reason: str


def _category_profile(user):
    scores = Counter()
    action_counts = Counter(
        dict(
            ActionSubmission.objects.filter(
                user=user, status=ActionSubmission.Status.APPROVED
            ).values_list('action_type__category').annotate(total=Count('pk'))
        )
    )
    challenge_counts = Counter(
        dict(
            ChallengeParticipation.objects.filter(user=user)
            .values_list('challenge__category').annotate(total=Count('pk'))
        )
    )
    badge_categories = Counter(
        dict(
            UserBadge.objects.filter(user=user, badge__category__gt='')
            .values_list('badge__category').annotate(total=Count('pk'))
        )
    )

    for category, count in action_counts.items():
        scores[category] += min(count, 4) * 1.5
    for category, count in challenge_counts.items():
        scores[category] += min(count, 3)
    for category, count in badge_categories.items():
        scores[category] += min(count, 3) * 0.75

    if user.favorite_category:
        scores[user.favorite_category] += 2

    team = get_user_team(user)
    if team:
        scores[team.focus_area] += 1.5

    organization = user.affiliation
    if organization and organization.focus_area:
        scores[organization.focus_area] += 1

    city = user.city.strip() or (organization.city.strip() if organization else '')
    return (
        scores, action_counts, challenge_counts, team, organization, badge_categories,
        user.favorite_category, city,
    )


def _explanation(event, profile):
    (
        _, action_counts, challenge_counts, team, organization, badge_categories,
        favorite_category, city,
    ) = profile
    category_label = dict(EcoCategory.choices).get(event.category, event.category).lower()

    if action_counts[event.category]:
        count = action_counts[event.category]
        return f'Parce que vous avez réalisé {count} action(s) de {category_label}.'
    if challenge_counts[event.category]:
        count = challenge_counts[event.category]
        label = dict(EcoCategory.choices).get(event.category, event.category)
        return f'Parce que vous suivez {count} défi(s) sur le thème « {label} ».'
    if badge_categories[event.category]:
        return f'Parce que votre badge est lié au thème {category_label}.'
    if event.category == getattr(team, 'focus_area', None):
        return f'Parce que le thème rejoint celui de votre équipe « {team.name} ».'
    if event.category == getattr(organization, 'focus_area', None):
        return f'Parce que le thème rejoint celui de votre organisation.'
    if event.category == favorite_category:
        return 'Parce que cette catégorie fait partie de vos thèmes préférés.'
    if organization and event.organization_id == organization.pk:
        return 'Parce que cet événement est proposé par votre organisation.'
    if city and city.casefold() in event.location.casefold():
        return f'Parce que cet événement se déroule près de {city}.'
    if event.recommendation_participant_count:
        return 'Parce que cet événement est populaire auprès de la communauté.'
    return 'Pour vous faire découvrir une initiative écologique à venir.'


def recommend_events(user, limit=3, now=None):
    """Return upcoming, joinable events ranked using the user's existing activity."""
    if not user.is_authenticated or limit <= 0:
        return []

    now = now or timezone.now()
    profile = _category_profile(user)
    category_scores, action_counts, challenge_counts, team, organization, badge_categories, _, city = profile
    points = max(0, user_points(user))
    badge_count = UserBadge.objects.filter(user=user).count()
    engagement = 1 + min(points, 1000) / 5000 + min(badge_count, 5) * 0.05

    joined_event_ids = EventParticipation.objects.filter(user=user).values('event_id')
    events = (
        Event.objects.filter(status=Event.Status.PUBLISHED, end_at__gte=now)
        .exclude(organizer=user)
        .exclude(pk__in=joined_event_ids)
        .select_related('organization')
        .annotate(recommendation_participant_count=Count('participations'))
        .order_by('start_at')
    )

    recommendations = []
    for event in events:
        if (
            (event.capacity is not None and event.recommendation_participant_count >= event.capacity)
            or (event.registration_deadline and event.registration_deadline < now)
            or not audience_allows(user, event)
        ):
            continue

        category_score = category_scores[event.category]
        organization_score = 2.5 if organization and event.organization_id == organization.pk else 0
        location_score = (
            1 if city and event.location and city.casefold() in event.location.casefold() else 0
        )
        popularity = min(event.recommendation_participant_count, 20)
        popularity_score = (2 * log1p(popularity) / log1p(20)) * engagement
        score = category_score + organization_score + location_score + popularity_score

        recommendations.append(
            EventRecommendation(
                event=event,
                score=round(score, 3),
                reason=_explanation(event, profile),
            )
        )

    recommendations.sort(key=lambda item: (-item.score, item.event.start_at, item.event.pk))
    return recommendations[:limit]
