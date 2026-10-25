from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from actions.services import approve_submission
from core.testing import make_action_type, make_submission, make_superuser, make_user
from notifications.models import Notification

from .models import Goal


class GoalTests(TestCase):
    def setUp(self):
        self.user = make_user('goal-owner')
        self.other = make_user('other')
        self.today = timezone.localdate()

    def goal_data(self, **extra):
        data = {'title': '10 trajets à vélo', 'description': 'Objectif du mois', 'category': 'transport',
                'tracking_mode': 'manual', 'target_value': 10, 'unit': 'trajets', 'current_progress': 0,
                'start_date': self.today.isoformat(), 'deadline': (self.today + timedelta(days=30)).isoformat()}
        data.update(extra)
        return data

    def test_create_goal(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('goals:create'), self.goal_data())
        goal = Goal.objects.get()
        self.assertRedirects(response, goal.get_absolute_url())
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.status, Goal.Status.ACTIVE)

    def test_deadline_must_follow_start(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('goals:create'), self.goal_data(
            deadline=(self.today - timedelta(days=1)).isoformat()))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Goal.objects.exists())

    def test_goals_are_private(self):
        goal = Goal.objects.create(user=self.user, title='Privé', target_value=5, deadline=self.today + timedelta(days=5))
        self.client.force_login(self.other)
        for name in ('goals:detail', 'goals:update', 'goals:delete'):
            self.assertEqual(self.client.get(reverse(name, args=[goal.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('goals:progress', args=[goal.pk]), {'value': 5}).status_code, 404)
        self.assertEqual(self.client.post(reverse('goals:delete', args=[goal.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('goals:list')), 'Privé')
        goal.refresh_from_db()
        self.assertEqual(goal.current_progress, 0)

    def test_update_and_delete_own_goal(self):
        goal = Goal.objects.create(user=self.user, title='Ancien', target_value=5, deadline=self.today + timedelta(days=5))
        self.client.force_login(self.user)
        self.client.post(reverse('goals:update', args=[goal.pk]), self.goal_data(title='Nouveau titre'))
        goal.refresh_from_db()
        self.assertEqual(goal.title, 'Nouveau titre')
        self.client.post(reverse('goals:delete', args=[goal.pk]))
        self.assertFalse(Goal.objects.exists())

    def test_manual_progress_and_completion(self):
        goal = Goal.objects.create(user=self.user, title='Manuel', target_value=4, deadline=self.today + timedelta(days=5))
        self.client.force_login(self.user)
        self.client.post(reverse('goals:progress', args=[goal.pk]), {'value': 2})
        goal.refresh_from_db()
        self.assertEqual(goal.progress_percent, 50)
        self.assertTrue(Notification.objects.filter(recipient=self.user, title='À mi-chemin de votre objectif').exists())
        self.client.post(reverse('goals:progress', args=[goal.pk]), {'value': 4})
        goal.refresh_from_db()
        self.assertEqual(goal.status, Goal.Status.COMPLETED)
        self.assertIsNotNone(goal.completed_at)
        self.assertTrue(Notification.objects.filter(recipient=self.user, title='Objectif atteint !').exists())

    def test_progress_percent_is_capped(self):
        goal = Goal(user=self.user, title='x', target_value=3, current_progress=7, deadline=self.today)
        self.assertEqual(goal.progress_percent, 100)

    def test_automatic_goal_tracks_only_approved_actions(self):
        goal = Goal.objects.create(
            user=self.user, title='Auto', tracking_mode=Goal.TrackingMode.ACTIONS, category='transport',
            target_value=2, start_date=self.today - timedelta(days=10), deadline=self.today + timedelta(days=10),
        )
        bike = make_action_type(points=10)
        water = make_action_type(name='Douche courte', category='water', points=5)
        moderator = make_superuser()
        first = make_submission(self.user, bike, days_ago=1)
        self.assertEqual(Goal.objects.get(pk=goal.pk).current_progress, 0)
        approve_submission(moderator, first)
        approve_submission(moderator, make_submission(self.user, water, days_ago=1))
        goal.refresh_from_db()
        self.assertEqual(goal.current_progress, 1)
        approve_submission(moderator, make_submission(self.user, bike, days_ago=2))
        goal.refresh_from_db()
        self.assertEqual(goal.status, Goal.Status.COMPLETED)

    def test_automatic_goal_progress_cannot_be_forced(self):
        goal = Goal.objects.create(user=self.user, title='Auto', tracking_mode=Goal.TrackingMode.POINTS,
                                   target_value=100, deadline=self.today + timedelta(days=10))
        self.client.force_login(self.user)
        self.client.post(reverse('goals:progress', args=[goal.pk]), {'value': 100})
        goal.refresh_from_db()
        self.assertEqual(goal.current_progress, 0)

    def test_pause_and_resume(self):
        goal = Goal.objects.create(user=self.user, title='Pause', target_value=5, deadline=self.today + timedelta(days=5))
        self.client.force_login(self.user)
        self.client.post(reverse('goals:toggle', args=[goal.pk]))
        goal.refresh_from_db()
        self.assertEqual(goal.status, Goal.Status.ABANDONED)
        self.client.post(reverse('goals:toggle', args=[goal.pk]))
        goal.refresh_from_db()
        self.assertEqual(goal.status, Goal.Status.ACTIVE)
