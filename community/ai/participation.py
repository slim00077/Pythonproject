"""Attendance forecasts based on recorded community event attendance."""
from collections import defaultdict
from dataclasses import dataclass

from django.db.models import Q
from django.utils import timezone

from community.models import Event, EventParticipation

ABSENCE_ALERT_THRESHOLD = 0.30
HISTORY_PRIOR_WEIGHT = 5


@dataclass(frozen=True)
class ParticipantAttendancePrediction:
    participation: EventParticipation
    attendance_probability: float
    absence_probability: float


@dataclass(frozen=True)
class EventAttendanceForecast:
    registrations: int
    expected_attendance: float
    absence_rate: float
    absence_percentage: int
    is_high_absence_risk: bool
    at_risk_participations: tuple[EventParticipation, ...]


def _lead_time_bucket(joined_at, starts_at):
    lead_days = max(0, (starts_at - joined_at).total_seconds() / 86400)
    if lead_days <= 1:
        return 'late'
    if lead_days <= 7:
        return 'medium'
    return 'early'


def predict_event_participation(event, now=None):
    """Predict expected attendance using category and registration lead-time history."""
    now = now or timezone.now()
    if event.status != Event.Status.PUBLISHED or event.end_at < now:
        return None

    history = EventParticipation.objects.filter(
        attended__isnull=False,
        event__status__in=(Event.Status.PUBLISHED, Event.Status.COMPLETED),
    ).filter(
        Q(event__end_at__lt=now) | Q(event__status=Event.Status.COMPLETED)
    ).values_list('attended', 'event__category', 'joined_at', 'event__start_at')
    category_counts = defaultdict(lambda: [0, 0])
    lead_time_counts = defaultdict(lambda: [0, 0])
    total = present = 0

    for attended, category, joined_at, starts_at in history.iterator():
        bucket = _lead_time_bucket(joined_at, starts_at)
        total += 1
        present += int(attended)
        category_counts[category][0] += 1
        category_counts[category][1] += int(attended)
        lead_time_counts[bucket][0] += 1
        lead_time_counts[bucket][1] += int(attended)

    if total == 0:
        return None

    global_rate = (present + 1) / (total + 2)
    category_total, category_present = category_counts[event.category]
    category_rate = (
        category_present + global_rate * HISTORY_PRIOR_WEIGHT
    ) / (category_total + HISTORY_PRIOR_WEIGHT)

    participations = list(
        event.participations.filter(attended__isnull=True).select_related('user').order_by('joined_at')
    )
    predictions = []
    for participation in participations:
        bucket = _lead_time_bucket(participation.joined_at, event.start_at)
        lead_total, lead_present = lead_time_counts[bucket]
        lead_rate = (lead_present + global_rate * HISTORY_PRIOR_WEIGHT) / (
            lead_total + HISTORY_PRIOR_WEIGHT
        )
        attendance_probability = 0.6 * category_rate + 0.3 * lead_rate + 0.1 * global_rate
        predictions.append(
            ParticipantAttendancePrediction(
                participation=participation,
                attendance_probability=attendance_probability,
                absence_probability=1 - attendance_probability,
            )
        )

    registrations = len(predictions)
    expected_attendance = sum(item.attendance_probability for item in predictions)
    absence_rate = (
        sum(item.absence_probability for item in predictions) / registrations
        if registrations else 0
    )
    at_risk = tuple(
        item.participation for item in predictions
        if item.absence_probability >= ABSENCE_ALERT_THRESHOLD
    )
    return EventAttendanceForecast(
        registrations=registrations,
        expected_attendance=round(expected_attendance, 1),
        absence_rate=round(absence_rate, 3),
        absence_percentage=round(absence_rate * 100),
        is_high_absence_risk=absence_rate >= ABSENCE_ALERT_THRESHOLD,
        at_risk_participations=at_risk,
    )
