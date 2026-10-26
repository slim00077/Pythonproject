"""Background execution of the AI call and category-filtered automatic goals."""
from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from actions.services import approve_submission
from core.testing import make_action_type, make_submission, make_superuser, make_user

from . import services
from .models import Goal, GoalAdvice


@override_settings(ECOTEAMS_AI_BACKGROUND=True, ECOTEAMS_AI_ENABLED=True)
class BackgroundTests(TestCase):
    def setUp(self):
        self.user = make_user('bg-user')
        self.goal = Goal.objects.create(user=self.user, title='Bg', target_value=5,
                                        deadline=timezone.localdate() + timedelta(days=5))

    def test_request_returns_pending_immediately_and_starts_a_daemon_thread(self):
        with mock.patch.object(services.threading, 'Thread') as thread:
            advice = services.request_advice(self.user, self.goal)
        self.assertEqual(advice.status, GoalAdvice.Status.PENDING)
        thread.assert_called_once()
        self.assertTrue(thread.call_args.kwargs['daemon'])
        thread.return_value.start.assert_called_once()

    def test_worker_function_runs_the_call_and_releases_connections(self):
        advice = GoalAdvice.objects.create(goal=self.goal, user=self.user)
        with mock.patch.object(services, 'run_advice') as run, mock.patch.object(services, 'close_old_connections') as close:
            services._run_in_thread(advice.pk)
        run.assert_called_once_with(advice.pk)
        self.assertEqual(close.call_count, 2)


class CategoryGoalTests(TestCase):
    def test_automatic_goals_only_count_their_category(self):
        user = make_user('cat-user')
        today = timezone.localdate()
        bike = make_action_type(points=10)
        water = make_action_type(name='Douche courte', category='water', points=5)
        moderator = make_superuser()
        goal = Goal.objects.create(user=user, title='Points eau', tracking_mode='points', category='water',
                                   target_value=100, start_date=today - timedelta(days=5),
                                   deadline=today + timedelta(days=5))
        approve_submission(moderator, make_submission(user, bike, days_ago=1))
        approve_submission(moderator, make_submission(user, water, days_ago=1))
        goal.refresh_from_db()
        self.assertEqual(goal.current_progress, 5)
