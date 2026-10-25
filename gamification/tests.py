from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from actions.services import approve_submission
from core.exceptions import BusinessRuleError
from core.testing import add_member, make_action_type, make_submission, make_superuser, make_team, make_user

from . import services
from .models import Badge, PointTransaction, UserBadge


class LedgerTests(TestCase):
    def setUp(self):
        self.user = make_user('scorer')
        self.team = make_team(self.user)

    def award(self, amount=10, reference='test:1'):
        return services.award_points(user=self.user, amount=amount, reason=PointTransaction.Reason.ACTION_APPROVED,
                                     reference=reference, description='Test')

    def test_award_records_current_team_and_is_idempotent(self):
        entry = self.award()
        self.assertEqual(entry.team, self.team)
        self.assertIsNone(self.award())
        self.assertEqual(services.user_points(self.user), 10)
        self.assertEqual(services.team_points(self.team), 10)

    def test_ledger_rows_are_immutable(self):
        entry = self.award()
        entry.amount = 9999
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            entry.delete()
        self.assertEqual(PointTransaction.objects.get().amount, 10)

    def test_reference_is_unique_in_database(self):
        self.award()
        with self.assertRaises(IntegrityError), transaction.atomic():
            PointTransaction.objects.create(user=self.user, amount=5, reason='action_approved', reference='test:1',
                                            description='duplicate')

    def test_zero_amount_is_refused(self):
        with self.assertRaises(ValueError):
            self.award(amount=0)

    def test_team_milestone_notification(self):
        member = make_user('member')
        add_member(self.team, member)
        self.award(amount=120)
        self.assertTrue(member.notifications.filter(kind='leaderboard', title__contains='100').exists())


class AdjustmentTests(TestCase):
    def setUp(self):
        self.admin = make_superuser()
        self.user = make_user('player')

    def test_regular_user_cannot_adjust_points(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('gamification:ledger')).status_code, 403)
        response = self.client.post(reverse('gamification:adjust'), {'user': self.user.pk, 'amount': 500, 'reason': 'moi'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PointTransaction.objects.exists())
        with self.assertRaises(BusinessRuleError):
            services.adjust_points(admin=self.user, user=self.user, amount=500, reason='moi')

    def test_admin_adjustment_is_audited(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('gamification:adjust'), {'user': self.user.pk, 'amount': 30, 'reason': 'Événement hors ligne'})
        entry = PointTransaction.objects.get()
        self.assertEqual((entry.amount, entry.reason, entry.created_by), (30, 'manual_adjustment', self.admin))
        self.assertIn('Événement hors ligne', entry.description)
        self.assertTrue(self.user.notifications.filter(kind='points').exists())

    def test_adjustment_cannot_make_balance_negative(self):
        with self.assertRaises(BusinessRuleError):
            services.adjust_points(admin=self.admin, user=self.user, amount=-10, reason='Correction')
        with self.assertRaises(BusinessRuleError):
            services.adjust_points(admin=self.admin, user=self.user, amount=10, reason='  ')


class BadgeTests(TestCase):
    def setUp(self):
        self.moderator = make_superuser()
        self.user = make_user('badger')
        self.bike = make_action_type(points=10)

    def approve(self, days_ago, action_type=None):
        approve_submission(self.moderator, make_submission(self.user, action_type or self.bike, days_ago=days_ago))

    def test_first_action_badge_is_unlocked_once(self):
        badge = Badge.objects.create(name='Premier geste', description='x', rule=Badge.Rule.ACTIONS_TOTAL, threshold=1)
        self.approve(1)
        self.approve(2)
        self.assertEqual(UserBadge.objects.filter(user=self.user, badge=badge).count(), 1)
        self.assertEqual(self.user.notifications.filter(kind='badge').count(), 1)

    def test_category_and_points_badges(self):
        category = Badge.objects.create(name='Cycliste', description='x', rule=Badge.Rule.CATEGORY_ACTIONS,
                                        category='transport', threshold=2)
        points = Badge.objects.create(name='50 points', description='x', rule=Badge.Rule.POINTS_TOTAL, threshold=50)
        water = make_action_type(name='Douche', category='water', points=40)
        self.approve(1, water)
        self.approve(1)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=points).exists())
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=category).exists())
        self.approve(2)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=category).exists())

    def test_inactive_badges_are_not_awarded(self):
        Badge.objects.create(name='Inactif', description='x', rule=Badge.Rule.ACTIONS_TOTAL, threshold=1, is_active=False)
        self.approve(1)
        self.assertFalse(UserBadge.objects.exists())

    def test_streak_computation(self):
        for days_ago in (1, 2, 3, 5):
            self.approve(days_ago)
        streak = services.compute_streaks(self.user)
        self.assertEqual((streak['current'], streak['best']), (3, 3))

    def test_team_rank_badge(self):
        badge = Badge.objects.create(name='Champion', description='x', rule=Badge.Rule.TEAM_RANK, threshold=1)
        make_team(self.user)
        rival = make_user('rival')
        make_team(rival, name='Rivaux')
        services.award_points(user=rival, amount=100, reason='manual_adjustment', reference='rival', description='x')
        self.approve(1)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=badge).exists())
        services.award_points(user=self.user, amount=200, reason='manual_adjustment', reference='me', description='x')
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=badge).exists())

    def test_badge_management_is_restricted(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('gamification:badge_list')).status_code, 403)
        self.client.post(reverse('gamification:badge_create'), {
            'name': 'Auto-attribué', 'description': 'x', 'icon': 'star', 'tone': 'lime', 'rule': 'actions_total',
            'threshold': 1, 'is_active': 'on'})
        self.assertFalse(Badge.objects.exists())
        self.client.force_login(self.moderator)
        self.client.post(reverse('gamification:badge_create'), {
            'name': 'Officiel', 'description': 'x', 'icon': 'star', 'tone': 'lime', 'rule': 'category_actions',
            'threshold': 1, 'is_active': 'on'})
        self.assertFalse(Badge.objects.exists())  # category is required for this rule
        self.client.post(reverse('gamification:badge_create'), {
            'name': 'Officiel', 'description': 'x', 'icon': 'star', 'tone': 'lime', 'rule': 'actions_total',
            'threshold': 1, 'is_active': 'on'})
        self.assertTrue(Badge.objects.filter(name='Officiel').exists())

    def test_achievements_page_shows_progress(self):
        Badge.objects.create(name='Trois actions', description='x', rule=Badge.Rule.ACTIONS_TOTAL, threshold=3)
        self.approve(1)
        self.client.force_login(self.user)
        response = self.client.get(reverse('gamification:achievements'))
        self.assertContains(response, 'Trois actions')
        self.assertContains(response, '1 / 3')
