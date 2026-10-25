from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from actions.models import ActionSubmission
from actions.services import approve_submission
from core.testing import add_member, make_action_type, make_submission, make_superuser, make_team, make_user
from gamification.models import PointTransaction
from gamification.services import award_points

from . import services


class LeaderboardTests(TestCase):
    def setUp(self):
        self.moderator = make_superuser()
        self.alice, self.bob, self.carl = make_user('alice'), make_user('bob'), make_user('carl')
        self.green = make_team(self.alice, name='Green')
        self.blue = make_team(self.bob, name='Blue')
        add_member(self.green, self.carl)
        self.bike = make_action_type(points=20)

    def award(self, user, amount, reference, **extra):
        return award_points(user=user, amount=amount, reason=PointTransaction.Reason.MANUAL_ADJUSTMENT,
                            reference=reference, description='test', **extra)

    def ranking(self, **kwargs):
        return [(team.name, team.rank, team.points) for team in services.team_leaderboard(**kwargs)]

    def test_scores_come_from_the_ledger(self):
        approve_submission(self.moderator, make_submission(self.alice, self.bike))
        approve_submission(self.moderator, make_submission(self.carl, self.bike))
        self.award(self.bob, 30, 'bob-1')
        self.assertEqual(self.ranking(), [('Green', 1, 40), ('Blue', 2, 30)])
        green = services.team_leaderboard()[0]
        self.assertEqual((green.member_total, green.approved_actions), (2, 2))

    def test_ranking_updates_when_points_change(self):
        self.award(self.alice, 10, 'a')
        self.award(self.bob, 20, 'b')
        self.assertEqual(self.ranking()[0][0], 'Blue')
        self.award(self.carl, 15, 'c')
        self.assertEqual(self.ranking(), [('Green', 1, 25), ('Blue', 2, 20)])

    def test_ties_share_the_same_rank(self):
        self.award(self.alice, 10, 'a')
        self.award(self.bob, 10, 'b')
        self.assertEqual([rank for _, rank, _ in self.ranking()], [1, 1])

    def test_points_stay_with_the_team_they_were_earned_for(self):
        self.award(self.carl, 50, 'before-move')
        self.carl.memberships.all().delete()
        add_member(self.blue, self.carl)
        self.award(self.carl, 5, 'after-move')
        self.assertEqual(dict((n, p) for n, _, p in self.ranking()), {'Green': 50, 'Blue': 5})

    def test_period_and_category_filters(self):
        old = self.award(self.alice, 100, 'old')
        PointTransaction.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=60))
        self.award(self.bob, 10, 'recent')
        self.assertEqual(self.ranking(period='month')[0][:1], ('Blue',))
        approve_submission(self.moderator, make_submission(self.bob, self.bike))
        self.assertEqual(dict((n, p) for n, _, p in self.ranking(category='transport')), {'Blue': 20, 'Green': 0})

    def test_user_rank(self):
        self.award(self.alice, 10, 'a')
        self.award(self.bob, 30, 'b')
        self.assertEqual(services.user_rank(self.bob), 1)
        self.assertEqual(services.user_rank(self.alice), 2)
        self.assertIsNone(services.user_rank(self.carl))

    def test_leaderboard_page(self):
        self.award(self.alice, 10, 'a')
        self.client.force_login(self.carl)
        response = self.client.get(reverse('analytics:leaderboard'), {'period': 'week', 'sort': 'members'})
        self.assertContains(response, 'Green')
        self.assertContains(response, 'is-mine')


class StatisticsTests(TestCase):
    def setUp(self):
        self.moderator = make_superuser()
        self.user = make_user('stat-user')
        make_team(self.user)
        self.action_type = make_action_type(points=12)

    def test_admin_overview_matches_records(self):
        approve_submission(self.moderator, make_submission(self.user, self.action_type, days_ago=1))
        make_submission(self.user, self.action_type, days_ago=2)
        overview = services.admin_overview()
        self.assertEqual(overview['total_users'], 2)
        self.assertEqual(overview['total_teams'], 1)
        self.assertEqual(overview['pending_submissions'], 1)
        self.assertEqual(overview['approved_submissions'], 1)
        self.assertEqual(overview['points_awarded'], 12)
        self.assertEqual(sum(row['value'] for row in overview['weekly_points']), 12)
        self.assertEqual(ActionSubmission.objects.filter(status='approved').count(), overview['approved_submissions'])

    def test_user_dashboard_stats(self):
        approve_submission(self.moderator, make_submission(self.user, self.action_type, days_ago=0))
        stats = services.user_dashboard(self.user)
        self.assertEqual((stats['points'], stats['approved_count'], stats['rank']), (12, 1, 1))
        self.assertEqual(sum(day['value'] for day in stats['daily_points']), 12)

    def test_admin_dashboard_and_reports_are_protected(self):
        self.client.force_login(self.user)
        for name in ('analytics:admin_dashboard', 'analytics:reports', 'analytics:reports_export'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.get(reverse('analytics:admin_dashboard')).status_code, 200)
        response = self.client.get(reverse('analytics:reports_export'), {'period': 'all'})
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Équipes', response.content.decode('utf-8'))

    def test_reports_permission_through_custom_role(self):
        group = Group.objects.create(name='Analyste')
        group.permissions.add(Permission.objects.get(codename='view_reports'))
        self.user.groups.add(group)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('analytics:reports')).status_code, 200)
        self.assertEqual(self.client.get(reverse('analytics:admin_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('accounts:role_list')).status_code, 403)

    def test_history_shows_only_own_transactions(self):
        other = make_user('other')
        award_points(user=other, amount=99, reason='manual_adjustment', reference='other', description='Secret')
        award_points(user=self.user, amount=7, reason='manual_adjustment', reference='mine', description='À moi')
        self.client.force_login(self.user)
        response = self.client.get(reverse('analytics:history'), {'tab': 'points'})
        self.assertContains(response, 'À moi')
        self.assertNotContains(response, 'Secret')
