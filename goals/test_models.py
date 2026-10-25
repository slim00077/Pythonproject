"""Unit tests of the Goal model, its constraints, form validation, services and views."""
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.exceptions import BusinessRuleError
from core.testing import make_user
from gamification.services import award_points

from . import services
from .forms import GoalForm, ProgressForm
from .models import Goal


class GoalModelAndFormTests(TestCase):
    def setUp(self):
        self.user = make_user('model-user')
        self.today = timezone.localdate()

    def make(self, **extra):
        data = {'user': self.user, 'title': 'Objectif', 'target_value': 10, 'deadline': self.today + timedelta(days=5)}
        data.update(extra)
        return Goal.objects.create(**data)

    def test_database_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(deadline=self.today - timedelta(days=1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(target_value=0)

    def test_properties(self):
        goal = self.make(current_progress=5)
        self.assertEqual(goal.progress_percent, 50)
        self.assertEqual(goal.days_left, 5)
        self.assertFalse(goal.is_overdue)
        self.assertFalse(goal.is_automatic)
        late = self.make(start_date=self.today - timedelta(days=9), deadline=self.today - timedelta(days=1))
        self.assertTrue(late.is_overdue)
        self.assertTrue(self.make(tracking_mode='points').is_automatic)
        self.assertEqual(str(goal), 'Objectif')

    def test_form_validation(self):
        base = {'title': 'x', 'tracking_mode': 'points', 'target_value': 5, 'unit': 'kg', 'current_progress': 0,
                'start_date': self.today, 'deadline': self.today + timedelta(days=3)}
        form = GoalForm(base)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['unit'], 'points')  # automatic modes force the unit
        self.assertFalse(GoalForm({**base, 'target_value': 0}).is_valid())
        self.assertFalse(GoalForm({**base, 'target_value': 100001}).is_valid())
        self.assertFalse(GoalForm({**base, 'deadline': self.today - timedelta(days=1)}).is_valid())
        self.assertFalse(GoalForm({**base, 'start_date': self.today + timedelta(days=9)}).is_valid())
        self.assertFalse(ProgressForm({'value': -1}).is_valid())

    def test_services_enforce_ownership_and_state(self):
        other = make_user('intruder')
        goal = self.make()
        with self.assertRaises(BusinessRuleError):
            services.update_manual_progress(other, goal, 3)
        with self.assertRaises(BusinessRuleError):
            services.set_abandoned(other, goal, True)
        services.update_manual_progress(self.user, goal, 10)
        goal.refresh_from_db()
        self.assertEqual(goal.status, Goal.Status.COMPLETED)
        with self.assertRaises(BusinessRuleError):
            services.set_abandoned(self.user, goal, True)  # a completed goal cannot be abandoned
        goal.status = Goal.Status.ABANDONED
        with self.assertRaises(BusinessRuleError):
            services.update_manual_progress(self.user, goal, 3)

    def test_completed_goal_reopens_when_progress_drops(self):
        goal = self.make()
        services.update_manual_progress(self.user, goal, 10)
        services.update_manual_progress(self.user, goal, 4)
        goal.refresh_from_db()
        self.assertEqual((goal.status, goal.completed_at), (Goal.Status.ACTIVE, None))

    def test_points_goal_counts_the_ledger(self):
        goal = self.make(tracking_mode='points', target_value=30, start_date=self.today - timedelta(days=3))
        award_points(user=self.user, amount=20, reason='manual_adjustment', reference='g:1', description='x')
        goal.refresh_from_db()
        self.assertEqual(goal.current_progress, 20)

    def test_views_require_login_and_list_filters(self):
        self.make(title='En cours')
        self.make(title='Fini', status=Goal.Status.COMPLETED, current_progress=10)
        for name in ('goals:list', 'goals:create'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('goals:list')), 'En cours')
        self.assertNotContains(self.client.get(reverse('goals:list')), 'Fini')
        self.assertContains(self.client.get(reverse('goals:list') + '?status=completed'), 'Fini')
        self.assertContains(self.client.get(reverse('goals:list') + '?status=all'), 'Fini')
        self.assertEqual(self.client.get(reverse('goals:create')).status_code, 200)

    def test_delete_needs_confirmation_and_toggle_needs_post(self):
        goal = self.make()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('goals:delete', args=[goal.pk])).status_code, 200)
        self.assertTrue(Goal.objects.filter(pk=goal.pk).exists())
        self.client.post(reverse('goals:progress', args=[goal.pk]), {'value': -5})
        goal.refresh_from_db()
        self.assertEqual(goal.current_progress, 0)
        self.assertEqual(self.client.get(reverse('goals:toggle', args=[goal.pk])).status_code, 405)
