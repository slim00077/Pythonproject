from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from core.testing import add_member, make_superuser, make_team, make_user
from notifications.models import Notification

from .models import Membership, Team


class TeamCrudTests(TestCase):
    def setUp(self):
        self.captain = make_user('captain')
        self.member = make_user('member')
        self.outsider = make_user('outsider')

    def team_data(self, **extra):
        data = {'name': 'Les Éco-Héros', 'motto': 'Ensemble', 'description': 'Une équipe engagée.',
                'focus_area': 'transport', 'max_members': 5, 'is_open': 'on'}
        data.update(extra)
        return data

    def test_create_team_makes_creator_captain(self):
        self.client.force_login(self.captain)
        response = self.client.post(reverse('teams:create'), self.team_data())
        team = Team.objects.get(name='Les Éco-Héros')
        self.assertRedirects(response, team.get_absolute_url())
        self.assertEqual(team.captain, self.captain)
        self.assertEqual(team.slug, 'les-eco-heros')
        self.assertTrue(Membership.objects.filter(team=team, user=self.captain, role='captain').exists())

    def test_user_already_in_a_team_cannot_create_another(self):
        make_team(self.captain)
        self.client.force_login(self.captain)
        self.client.post(reverse('teams:create'), self.team_data(name='Deuxième équipe'))
        self.assertFalse(Team.objects.filter(name='Deuxième équipe').exists())

    def test_team_name_is_unique_case_insensitively(self):
        make_team(self.captain, name='Les Éco-Héros')
        self.client.force_login(self.outsider)
        response = self.client.post(reverse('teams:create'), self.team_data(name='les éco-héros'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Team.objects.count(), 1)

    def test_reserved_slug_is_avoided(self):
        team = make_team(self.captain, name='Create')
        self.assertNotEqual(team.slug, 'create')

    def test_only_captain_can_update(self):
        team = make_team(self.captain)
        add_member(team, self.member)
        url = reverse('teams:update', args=[team.slug])
        for user in (self.member, self.outsider):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.team_data(name='Piratée', status='active')).status_code, 403)
        team.refresh_from_db()
        self.assertEqual(team.name, 'Équipe Test')
        self.client.force_login(self.captain)
        self.client.post(url, self.team_data(name='Nouveau nom', status='active'))
        team.refresh_from_db()
        self.assertEqual(team.name, 'Nouveau nom')

    def test_max_members_cannot_drop_below_current_size(self):
        team = make_team(self.captain)
        add_member(team, self.member)
        add_member(team, self.outsider)
        self.client.force_login(self.captain)
        response = self.client.post(reverse('teams:update', args=[team.slug]), self.team_data(max_members=2, status='active'))
        self.assertEqual(response.status_code, 200)
        team.refresh_from_db()
        self.assertEqual(team.max_members, 8)

    def test_only_captain_or_admin_can_delete(self):
        team = make_team(self.captain)
        add_member(team, self.member)
        url = reverse('teams:delete', args=[team.slug])
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Team.objects.filter(pk=team.pk).exists())
        self.client.force_login(self.captain)
        self.assertRedirects(self.client.post(url), reverse('teams:list'))
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.member, title='Équipe supprimée').exists())

    def test_admin_can_delete_any_team(self):
        team = make_team(self.captain)
        self.client.force_login(make_superuser())
        self.client.post(reverse('teams:delete', args=[team.slug]))
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())

    def test_list_search_and_detail(self):
        make_team(self.captain, name='Vélo Club', focus_area='transport')
        make_team(self.member, name='Eau Claire', focus_area='water')
        self.client.force_login(self.outsider)
        response = self.client.get(reverse('teams:list'), {'q': 'vélo'})
        self.assertContains(response, 'Vélo Club')
        self.assertNotContains(response, 'Eau Claire')
        response = self.client.get(reverse('teams:list'), {'focus_area': 'water'})
        self.assertContains(response, 'Eau Claire')
        self.assertEqual(self.client.get(Team.objects.get(name='Vélo Club').get_absolute_url()).status_code, 200)


class MembershipTests(TestCase):
    def setUp(self):
        self.captain = make_user('captain')
        self.user = make_user('joiner')
        self.team = make_team(self.captain, max_members=2)

    def test_join_team_notifies_captain(self):
        self.client.force_login(self.user)
        self.client.post(reverse('teams:join', args=[self.team.slug]))
        self.assertTrue(Membership.objects.filter(team=self.team, user=self.user, role='member').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.captain, kind='team').exists())

    def test_join_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('teams:join', args=[self.team.slug])).status_code, 405)

    def test_only_one_team_per_user(self):
        other = make_team(make_user('other-captain'), name='Autre équipe')
        self.client.force_login(self.user)
        self.client.post(reverse('teams:join', args=[self.team.slug]))
        self.client.post(reverse('teams:join', args=[other.slug]))
        self.assertEqual(Membership.objects.filter(user=self.user).count(), 1)

    def test_database_prevents_duplicate_memberships(self):
        add_member(self.team, self.user)
        other = make_team(make_user('other-captain'), name='Autre équipe')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.create(team=other, user=self.user)

    def test_full_or_closed_team_cannot_be_joined(self):
        add_member(self.team, make_user('second'))
        self.client.force_login(self.user)
        self.client.post(reverse('teams:join', args=[self.team.slug]))
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        closed = make_team(make_user('closed-captain'), name='Fermée', is_open=False)
        self.client.post(reverse('teams:join', args=[closed.slug]))
        self.assertFalse(Membership.objects.filter(user=self.user).exists())

    def test_member_can_leave_but_captain_cannot(self):
        add_member(self.team, self.user)
        self.client.force_login(self.user)
        self.client.post(reverse('teams:leave', args=[self.team.slug]))
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        self.client.force_login(self.captain)
        self.client.post(reverse('teams:leave', args=[self.team.slug]))
        self.assertTrue(Membership.objects.filter(user=self.captain, team=self.team).exists())

    def test_only_captain_can_remove_members(self):
        add_member(self.team, self.user)
        url = reverse('teams:member_remove', args=[self.team.slug, self.user.pk])
        intruder = make_user('intruder')
        self.client.force_login(intruder)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('teams:member_remove', args=[self.team.slug, self.captain.pk])).status_code, 403)
        self.assertTrue(Membership.objects.filter(user=self.user).exists())
        self.client.force_login(self.captain)
        self.client.post(url)
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user, kind='team').exists())

    def test_captaincy_transfer(self):
        add_member(self.team, self.user)
        self.client.force_login(self.captain)
        self.client.post(reverse('teams:captain_transfer', args=[self.team.slug, self.user.pk]))
        self.team.refresh_from_db()
        self.assertEqual(self.team.captain, self.user)
        self.assertEqual(Membership.objects.get(user=self.user).role, 'captain')
        self.assertEqual(Membership.objects.get(user=self.captain).role, 'member')
