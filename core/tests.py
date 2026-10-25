from io import StringIO

from django.core.management import call_command
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from actions.models import ActionSubmission
from challenges.models import Challenge
from community.models import Event
from core.views import public_media
from gamification.models import Badge, PointTransaction, UserBadge
from goals.models import Goal
from notifications.models import Notification
from teams.models import Team

from .testing import make_superuser


class LandingPageTests(TestCase):
    def test_landing_page_is_public_and_french(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agir ensemble.')
        self.assertContains(response, 'Faire la différence.')
        self.assertContains(response, 'lang="fr"')

    def test_custom_404_page(self):
        response = self.client.get('/cette-page-n-existe-pas/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page introuvable', status_code=404)

    def test_private_evidence_is_never_served_as_public_media(self):
        request = RequestFactory().get('/media/evidence/2026/01/x.png')
        with self.assertRaises(Http404):
            public_media(request, 'evidence/2026/01/x.png')

    def test_django_admin_is_still_available(self):
        self.assertEqual(self.client.get('/django-admin/').status_code, 302)
        self.client.force_login(make_superuser())
        self.assertEqual(self.client.get('/django-admin/').status_code, 200)


class DemoDataSmokeTests(TestCase):
    """Seeds the demo data and renders every page for each access level."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo_data', password='Demo-Password-2026', force=True, stdout=StringIO())
        cls.admin = make_superuser()
        cls.member = User.objects.get(username='demo_amina')
        cls.moderator = User.objects.get(username='demo_moderateur')

    def counts(self):
        return [model.objects.count() for model in (
            User, Team, Challenge, ActionSubmission, PointTransaction, UserBadge, Goal, Event, Badge)]

    def test_seed_is_idempotent(self):
        before = self.counts()
        total_points = sum(PointTransaction.objects.values_list('amount', flat=True))
        call_command('seed_demo_data', password='Demo-Password-2026', force=True, stdout=StringIO())
        self.assertEqual(self.counts(), before)
        self.assertEqual(sum(PointTransaction.objects.values_list('amount', flat=True)), total_points)

    def test_seed_populates_every_module(self):
        self.assertGreaterEqual(Team.objects.count(), 4)
        self.assertTrue(ActionSubmission.objects.filter(status='approved').exists())
        self.assertTrue(ActionSubmission.objects.filter(status='pending').exists())
        self.assertTrue(PointTransaction.objects.filter(reason='challenge_completed').exists())
        self.assertTrue(UserBadge.objects.exists())
        self.assertTrue(Notification.objects.exists())
        self.assertTrue(Event.objects.filter(status='published').exists())
        self.assertTrue(self.moderator.has_perm('actions.moderate_actionsubmission'))
        self.assertFalse(self.moderator.is_superuser)

    def user_pages(self):
        team = Team.objects.get(name='Les Pédaleurs Verts')
        challenge = Challenge.objects.get(title='Mois du vélo')
        submission = ActionSubmission.objects.filter(user=self.member).first()
        goal = Goal.objects.filter(user=self.member).first()
        event = Event.objects.filter(status='published').first()
        notification = Notification.objects.filter(recipient=self.member).first()
        return [
            reverse('analytics:dashboard'), reverse('analytics:leaderboard'), reverse('analytics:history'),
            reverse('analytics:history') + '?tab=points', reverse('teams:list'), team.get_absolute_url(), reverse('challenges:list'), reverse('challenges:list') + '?status=all',
            reverse('challenges:mine'), reverse('challenges:create'), challenge.get_absolute_url(),
            reverse('actions:list'), reverse('actions:catalog'), reverse('actions:create'),
            submission.get_absolute_url(), reverse('goals:list'), reverse('goals:create'), goal.get_absolute_url(),
            reverse('goals:update', args=[goal.pk]), reverse('gamification:achievements'), reverse('community:list'),
            reverse('community:list') + '?when=past', reverse('community:mine'),
            event.get_absolute_url(), reverse('notifications:list'), reverse('notifications:preferences'),
            notification.get_absolute_url(), reverse('accounts:profile'), reverse('accounts:profile_edit'),
            reverse('accounts:password_change'), reverse('accounts:public_profile', args=['demo_sarra']),
        ]

    def admin_pages(self):
        submission = ActionSubmission.objects.filter(status='pending').first()
        challenge = Challenge.objects.filter(status='pending').first()
        event = Event.objects.filter(status='pending').first()
        return [
            reverse('analytics:admin_dashboard'), reverse('analytics:reports'),
            reverse('analytics:reports') + '?period=all', reverse('accounts:role_list'), reverse('accounts:role_create'),
            reverse('accounts:user_list'), reverse('accounts:user_edit', args=[self.member.pk]),
            reverse('actions_admin:moderation_list'), reverse('actions_admin:moderation_list') + '?tab=approved',
            reverse('actions_admin:moderation_detail', args=[submission.pk]), reverse('actions_admin:type_list'),
            reverse('actions_admin:type_create'), reverse('challenges_admin:review_list'),
            reverse('challenges_admin:review_detail', args=[challenge.slug]), reverse('community_admin:review_list'),
            reverse('community_admin:review_detail', args=[event.slug]), reverse('gamification:badge_list'),
            reverse('gamification:badge_create'), reverse('gamification:ledger'), reverse('gamification:adjust'),
        ]

    def test_member_pages_render(self):
        self.client.force_login(self.member)
        for url in self.user_pages():
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_member_is_denied_admin_pages(self):
        self.client.force_login(self.member)
        for url in self.admin_pages():
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_admin_pages_render_for_superuser(self):
        self.client.force_login(self.admin)
        extra = [reverse('core:home'), reverse('teams:create'), reverse('analytics:admin_stats'), reverse('analytics:audit_log'),
                 reverse('organizations:admin_list'), reverse('organizations:admin_create'), reverse('notifications:announce'),
                 reverse('community:create')]
        for url in self.admin_pages() + extra:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_student_cannot_create_events_and_admin_dashboard_redirects(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('community:create')).status_code, 403)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse('analytics:dashboard')), reverse('analytics:admin_dashboard'))

    def test_member_already_in_a_team_is_redirected_from_team_creation(self):
        self.client.force_login(self.member)
        self.assertRedirects(self.client.get(reverse('teams:create')),
                             Team.objects.get(captain=self.member).get_absolute_url())

    def test_moderator_role_sees_only_its_screens(self):
        self.client.force_login(self.moderator)
        for name in ('actions_admin:moderation_list', 'challenges_admin:review_list', 'community_admin:review_list',
                     'analytics:reports', 'analytics:admin_dashboard'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        for name in ('accounts:role_list', 'accounts:user_list', 'gamification:badge_list', 'gamification:ledger',
                     'actions_admin:type_list'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_landing_page_uses_real_data(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Les Pédaleurs Verts')
        self.assertEqual(response.context['stats']['actions'], ActionSubmission.objects.filter(status='approved').count())
