"""Views, permissions and edge cases of the gamification module (back-office and participant pages)."""
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.exceptions import BusinessRuleError
from core.testing import make_superuser, make_team, make_user

from . import services
from .forms import PointAdjustmentForm
from .models import Badge, PointTransaction, UserBadge


def make_badge(**extra):
    data = {'name': 'Badge test', 'description': 'x', 'rule': Badge.Rule.ACTIONS_TOTAL, 'threshold': 1}
    data.update(extra)
    return Badge.objects.create(**data)


def user_with_permission(username, codename):
    user = make_user(username)
    group = Group.objects.create(name=f'role-{username}')
    group.permissions.add(Permission.objects.get(codename=codename))
    user.groups.add(group)
    return user


class AccessControlTests(TestCase):
    """Every gamification URL: anonymous -> login, simple user -> 403, no URL bypass."""

    def setUp(self):
        self.user = make_user('simple')
        self.badge = make_badge()
        self.admin_urls = [
            reverse('gamification:badge_list'), reverse('gamification:badge_create'),
            reverse('gamification:badge_update', args=[self.badge.pk]),
            reverse('gamification:badge_delete', args=[self.badge.pk]),
            reverse('gamification:ledger'), reverse('gamification:adjust'),
        ]

    def test_anonymous_is_redirected_to_login_everywhere(self):
        for url in self.admin_urls + [reverse('gamification:achievements')]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('login', response['Location'])

    def test_simple_user_gets_403_on_every_back_office_url(self):
        self.client.force_login(self.user)
        for url in self.admin_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(self.admin_urls[3]).status_code, 403)
        self.assertTrue(Badge.objects.filter(pk=self.badge.pk).exists())

    def test_badge_permission_does_not_open_the_ledger_and_vice_versa(self):
        badge_manager = user_with_permission('badger', 'change_badge')
        point_manager = user_with_permission('pointer', 'adjust_points')
        self.client.force_login(badge_manager)
        self.assertEqual(self.client.get(reverse('gamification:badge_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('gamification:ledger')).status_code, 403)
        self.client.force_login(point_manager)
        self.assertEqual(self.client.get(reverse('gamification:ledger')).status_code, 200)
        self.assertEqual(self.client.get(reverse('gamification:badge_list')).status_code, 403)

    def test_inactive_superuser_is_refused(self):
        admin = make_superuser('ghost')
        admin.is_active = False
        admin.save()
        self.assertFalse(self.client.login(username='ghost', password='Un-Mot-De-Passe-Solide-2026'))


class BadgeBackOfficeTests(TestCase):
    def setUp(self):
        self.admin = make_superuser()
        self.client.force_login(self.admin)

    def post_badge(self, url, **extra):
        data = {'name': 'Nouveau', 'description': 'desc', 'icon': 'award', 'tone': 'lime', 'rule': 'actions_total',
                'threshold': 3, 'is_active': 'on'}
        data.update(extra)
        return self.client.post(url, data)

    def test_create_update_and_list(self):
        response = self.post_badge(reverse('gamification:badge_create'))
        self.assertRedirects(response, reverse('gamification:badge_list'))
        badge = Badge.objects.get(name='Nouveau')
        self.assertEqual(badge.slug, 'nouveau')
        self.post_badge(reverse('gamification:badge_update', args=[badge.pk]), name='Renommé', threshold=7)
        badge.refresh_from_db()
        self.assertEqual((badge.name, badge.threshold), ('Renommé', 7))
        self.assertContains(self.client.get(reverse('gamification:badge_list')), 'Renommé')
        self.assertEqual(self.client.get(reverse('gamification:badge_update', args=[badge.pk])).status_code, 200)

    def test_invalid_badge_is_rejected(self):
        for bad in ({'threshold': 0}, {'name': ''}, {'rule': 'nope'}):
            with self.subTest(bad=bad):
                response = self.post_badge(reverse('gamification:badge_create'), **bad)
                self.assertEqual(response.status_code, 200)
        self.assertFalse(Badge.objects.exists())

    def test_duplicate_name_is_rejected(self):
        make_badge(name='Unique')
        self.assertEqual(self.post_badge(reverse('gamification:badge_create'), name='Unique').status_code, 200)
        self.assertEqual(Badge.objects.count(), 1)

    def test_unknown_badge_is_404(self):
        self.assertEqual(self.client.get(reverse('gamification:badge_update', args=[999])).status_code, 404)
        self.assertEqual(self.client.post(reverse('gamification:badge_delete', args=[999])).status_code, 404)

    def test_delete_flow(self):
        badge = make_badge()
        url = reverse('gamification:badge_delete', args=[badge.pk])
        self.assertEqual(self.client.get(url).status_code, 200)  # confirmation page
        self.assertTrue(Badge.objects.filter(pk=badge.pk).exists())
        self.assertRedirects(self.client.post(url), reverse('gamification:badge_list'))
        self.assertFalse(Badge.objects.filter(pk=badge.pk).exists())

    def test_awarded_badge_cannot_be_deleted(self):
        badge = make_badge()
        UserBadge.objects.create(user=make_user('winner'), badge=badge)
        self.client.post(reverse('gamification:badge_delete', args=[badge.pk]))
        self.assertTrue(Badge.objects.filter(pk=badge.pk).exists())

    def test_category_rule_requires_category_and_clears_it_otherwise(self):
        with self.assertRaises(ValidationError):
            Badge(name='c', description='x', rule=Badge.Rule.CATEGORY_ACTIONS, threshold=1).full_clean()
        badge = Badge(name='d', description='x', rule=Badge.Rule.POINTS_TOTAL, threshold=1, category='water')
        badge.full_clean()
        self.assertEqual(badge.category, '')
        self.assertEqual(str(badge), 'd')


class LedgerBackOfficeTests(TestCase):
    def setUp(self):
        self.admin = make_superuser()
        self.player = make_user('player')
        make_team(self.player, name='Les Verts')
        self.client.force_login(self.admin)
        services.award_points(user=self.player, amount=10, reason='action_approved', reference='r:1',
                              description='Trajet à vélo')
        services.award_points(user=self.player, amount=-4, reason='action_revoked', reference='r:2',
                              description='Annulation')

    def test_ledger_filters_and_totals(self):
        response = self.client.get(reverse('gamification:ledger'))
        self.assertEqual(response.context['totals'], {'awarded': 10, 'removed': -4})
        self.assertEqual(len(response.context['page']), 2)
        by_reason = self.client.get(reverse('gamification:ledger') + '?reason=action_revoked')
        self.assertEqual(len(by_reason.context['page']), 1)
        by_text = self.client.get(reverse('gamification:ledger') + '?q=vélo')
        self.assertEqual(len(by_text.context['page']), 1)
        by_team = self.client.get(reverse('gamification:ledger') + '?q=Verts')
        self.assertEqual(len(by_team.context['page']), 2)
        ignored = self.client.get(reverse('gamification:ledger') + '?reason=<script>')
        self.assertEqual(len(ignored.context['page']), 2)

    def test_ledger_is_paginated(self):
        for i in range(25):
            services.award_points(user=self.player, amount=1, reason='action_approved', reference=f'p:{i}',
                                  description='x')
        page = self.client.get(reverse('gamification:ledger') + '?page=2').context['page']
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page), 7)
        self.assertEqual(self.client.get(reverse('gamification:ledger') + '?page=abc').status_code, 200)

    def test_adjust_form_page_and_validation(self):
        self.assertEqual(self.client.get(reverse('gamification:adjust')).status_code, 200)
        for bad in ({'amount': 0}, {'amount': 1001}, {'reason': ''}, {'user': 9999}):
            with self.subTest(bad=bad):
                data = {'user': self.player.pk, 'amount': 5, 'reason': 'ok'}
                data.update(bad)
                response = self.client.post(reverse('gamification:adjust'), data)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(PointTransaction.objects.count(), 2)

    def test_business_error_is_shown_not_raised(self):
        response = self.client.post(reverse('gamification:adjust'),
                                    {'user': self.player.pk, 'amount': -500, 'reason': 'trop'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'négatif')
        self.assertEqual(services.user_points(self.player), 6)

    def test_adjustment_form_only_lists_active_users(self):
        gone = make_user('gone')
        gone.is_active = False
        gone.save()
        self.assertNotIn(gone, PointAdjustmentForm().fields['user'].queryset)

    def test_moderator_cannot_adjust_own_points_but_superuser_can(self):
        moderator = user_with_permission('mod', 'adjust_points')
        with self.assertRaisesMessage(BusinessRuleError, 'propres points'):
            services.adjust_points(admin=moderator, user=moderator, amount=5, reason='moi')
        self.assertTrue(services.adjust_points(admin=self.admin, user=self.admin, amount=5, reason='test'))

    def test_adjustment_limit(self):
        with self.assertRaises(BusinessRuleError):
            services.adjust_points(admin=self.admin, user=self.player, amount=services.MAX_ADJUSTMENT + 1, reason='x')

    def test_ledger_model_strings(self):
        entry = PointTransaction.objects.get(reference='r:1')
        self.assertIn('+10 pts', str(entry))
        self.assertIn('-4 pts', str(PointTransaction.objects.get(reference='r:2')))


class AchievementsPageTests(TestCase):
    def setUp(self):
        self.user = make_user('achiever')
        self.client.force_login(self.user)

    def test_page_without_badges(self):
        response = self.client.get(reverse('gamification:achievements'))
        self.assertContains(response, 'Aucun badge configuré')
        self.assertEqual(response.context['streak'], {'current': 0, 'best': 0, 'last_day': None})

    def test_team_rank_badge_progress_labels(self):
        badge = make_badge(rule=Badge.Rule.TEAM_RANK, threshold=1)
        rows = services.badge_progress(self.user)
        self.assertEqual(rows[0]['label'], 'Équipe non classée')
        make_team(self.user)
        rival = make_user('rival')
        make_team(rival, name='Rivaux')
        services.award_points(user=rival, amount=50, reason='manual_adjustment', reference='a', description='x')
        services.award_points(user=self.user, amount=25, reason='manual_adjustment', reference='b', description='x')
        row = services.badge_progress(self.user)[0]
        self.assertEqual((row['value'], row['progress'], row['label']), (2, 50, 'Rang actuel : 2'))
        self.assertEqual(badge.get_rule_display()[:5], 'Rang ')

    def test_points_by_reason_are_listed(self):
        services.award_points(user=self.user, amount=12, reason='challenge_completed', reference='c', description='x')
        by_reason = dict(self.client.get(reverse('gamification:achievements')).context['by_reason'])
        self.assertEqual(by_reason['Défi réussi'], 12)

    def test_award_ignores_duplicates_and_negative_team_notifications(self):
        make_team(self.user)
        services.award_points(user=self.user, amount=5, reason='manual_adjustment', reference='z', description='x')
        self.assertIsNone(services.award_points(user=self.user, amount=5, reason='manual_adjustment', reference='z',
                                                description='x'))
        self.assertEqual(services.team_points(None), 0)
        self.assertIsNone(services.team_rank(None))
