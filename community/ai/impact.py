"""Transparent campaign impact estimates using editable local factors."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from community.models import CampaignImpactFactor, Event


@dataclass(frozen=True)
class CampaignImpactEstimate:
    participants: int
    duration_days: Decimal
    co2_saved_kg: Decimal
    potential_points: int


def estimate_campaign_impact(event):
    """Estimate impact from target participants, event duration, and category factor."""
    if event.kind != Event.Kind.CAMPAIGN:
        return None

    factor = CampaignImpactFactor.objects.filter(category=event.category, is_active=True).first()
    if factor is None:
        return None

    participants = event.participation_goal or event.capacity or event.participant_count
    duration_days = Decimal(str((event.end_at - event.start_at).total_seconds())) / Decimal('86400')
    duration_days = duration_days.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    if participants <= 0 or duration_days <= 0:
        return None

    co2_saved_kg = (
        factor.co2_kg_per_participant_day * participants * duration_days
    ).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    potential_points = int(
        (factor.points_per_participant_day * participants * duration_days)
        .quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    )
    return CampaignImpactEstimate(
        participants=participants,
        duration_days=duration_days,
        co2_saved_kg=co2_saved_kg,
        potential_points=potential_points,
    )


def compare_campaign_impact(event, estimate=None):
    """Return a readable actual-versus-estimated comparison when both exist."""
    estimate = estimate or estimate_campaign_impact(event)
    actual = event.actual_co2_saved_kg
    if estimate is None or actual is None:
        return None

    difference = actual - estimate.co2_saved_kg
    return {
        'difference_kg': abs(difference).quantize(Decimal('0.001')),
        'relation': 'above' if difference > 0 else 'below' if difference < 0 else 'equal',
    }
