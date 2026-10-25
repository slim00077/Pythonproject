"""Tests of the role-specific experiences: dashboards, navigation, organizations and authorization."""
from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from actions.models import ActionSubmission
from analytics import dashboards
from challenges.models import Challenge
from community.models import Event, EventParticipation
from core.choices import Audience
from core.permissions import MODERATE_ACTIONS
from core.testing import (
    add_member, make_action_type, make_challenge, make_event, make_submission, make_superuser, make_team, make_user,
)
from notifications.models import Notification
from organizations.models import Organization


def give_points(user, amount, reference):
    from gamification.models import PointTransaction
    from gamification.services import award_points
    return award_points(user=user, amount=amount, reason=PointTransaction.Reason.MANUAL_ADJUSTMENT,
                        reference=reference, description='Points de test', notify_user=False)


def make_org(name='Acme', kind=Organization.Kind.COMPANY, **extra):
    return Organization.objects.create(name=name, kind=kind, **extra)


def student(username='stu'):
    return make_user(username, organization_type='student')


def employee(username='emp', org=None):
    return make_user(username, organization_type='employee', affiliation=org)


def association(username='asso', org=None, manager=False):
    return make_user(username, organization_type='association', affiliation=org, is_org_manager=manager)


class DashboardSeparationTests(TestCase):
    def test_each_account_category_gets_its_own_dashboard_and_navigation(self):
        org = make_org()
        cases = [
            (student(), 'analytics/dashboard_student.html', 'Explorer les équipes'),
            (employee(org=org), 'analytics/dashboard_employee.html', 'Défis d’entreprise'),
            (association(org=make_org('Asso', Organization.Kind.ASSOCIATION), manager=True),
             'analytics/dashboard_association.html', 'Impact communautaire'),
        ]
        for user, template, nav_text in cases:
            self.client.force_login(user)
            response = self.client.get(reverse('analytics:dashboard'))
            self.assertEqual(response.status_code, 200, user.username)
            self.assertTemplateUsed(response, template)
            self.assertContains(response, nav_text)

    def test_navigation_differs_between_categories(self):
        org = make_org()
        self.client.force_login(student())
        student_page = self.client.get(reverse('analytics:dashboard')).content.decode()
        self.client.force_login(employee(org=org))
        employee_page = self.client.get(reverse('analytics:dashboard')).content.decode()
        self.assertIn('Explorer les équipes', student_page)
        self.assertNotIn('Explorer les équipes', employee_page)
        self.assertNotIn('Mes campagnes', student_page)
        self.assertNotIn('Mes campagnes', employee_page)
        self.assertIn('Mon entreprise', employee_page)

    def test_employee_without_organization_sees_no_company_links(self):
        self.client.force_login(employee())
        page = self.client.get(reverse('analytics:dashboard')).content.decode()
        self.assertNotIn('Mon entreprise', page)
        self.assertIn('n’est rattaché à aucune entreprise', page)

    def test_administrator_is_redirected_to_the_control_center(self):
        self.client.force_login(make_superuser())
        self.assertRedirects(self.client.get(reverse('analytics:dashboard')), reverse('analytics:admin_dashboard'))
        page = self.client.get(reverse('analytics:admin_dashboard')).content.decode()
        self.assertIn('Rôles et permissions', page)
        self.assertIn('Journaux d’audit', page)
        self.assertIn('Centre de contrôle', page)
        self.assertNotIn('Explorer les équipes', page)

    def test_empty_database_never_breaks_a_dashboard(self):
        org = make_org('Vide', Organization.Kind.ASSOCIATION)
        users = [student('a'), employee('b', make_org('Vide 2')), association('c', org, True), association('d'), employee('e')]
        users.append(make_superuser())
        for user in users:
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('analytics:dashboard'), follow=True).status_code, 200, user.username)
        self.client.force_login(users[-1])
        for name in ('analytics:admin_stats', 'analytics:audit_log', 'organizations:admin_list', 'notifications:announce'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)


class AccountCategoryTests(TestCase):
    def test_changing_category_never_grants_admin_rights(self):
        admin = make_superuser()
        target = student('target')
        org = make_org('Asso', Organization.Kind.ASSOCIATION)
        self.client.force_login(admin)
        response = self.client.post(reverse('accounts:user_edit', args=[target.pk]), {
            'organization_type': 'association', 'affiliation': org.pk, 'is_org_manager': 'on', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(target.organization_type, 'association')
        self.assertEqual(target.affiliation, org)
        self.assertTrue(target.is_org_manager)
        self.assertFalse(target.is_superuser)
        self.assertFalse(target.is_staff)
        self.assertFalse(target.has_perm(MODERATE_ACTIONS))
        self.client.force_login(target)
        self.assertEqual(self.client.get(reverse('analytics:admin_dashboard')).status_code, 403)

    def test_manager_flag_requires_an_organization(self):
        self.client.force_login(make_superuser())
        target = student('target')
        response = self.client.post(reverse('accounts:user_edit', args=[target.pk]), {
            'organization_type': 'student', 'is_org_manager': 'on', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertFalse(target.is_org_manager)

    def test_profile_form_cannot_change_category_or_privileges(self):
        user = student('me')
        self.client.force_login(user)
        self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Moi', 'last_name': 'Même', 'email': 'me@example.com', 'city': 'Tunis',
            'organization_type': 'association', 'is_superuser': 'on', 'is_staff': 'on', 'is_org_manager': 'on',
        })
        user.refresh_from_db()
        self.assertEqual(user.organization_type, 'student')
        self.assertFalse(user.is_superuser or user.is_staff or user.is_org_manager)
        self.assertEqual(user.city, 'Tunis')

    def test_student_cannot_edit_another_users_profile(self):
        a, b = student('a'), student('b')
        self.client.force_login(a)
        self.client.post(reverse('accounts:profile_edit'), {'first_name': 'Pirate', 'last_name': 'X', 'email': 'a@example.com'})
        b.refresh_from_db()
        self.assertNotEqual(b.first_name, 'Pirate')
        self.assertEqual(self.client.get(reverse('accounts:user_edit', args=[b.pk])).status_code, 403)


class AdministrationAccessTests(TestCase):
    ADMIN_URLS = [
        'analytics:admin_stats', 'analytics:audit_log', 'accounts:user_list', 'accounts:role_list',
        'organizations:admin_list', 'notifications:announce',
    ]

    def test_ordinary_accounts_cannot_open_the_control_center(self):
        org = make_org()
        for user in (student(), employee(org=org), association(org=make_org('A', Organization.Kind.ASSOCIATION), manager=True)):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('analytics:admin_dashboard')).status_code, 403, user.username)
            for name in self.ADMIN_URLS:
                self.assertEqual(self.client.get(reverse(name)).status_code, 403, f'{user.username} {name}')

    def test_anonymous_users_are_redirected_to_login(self):
        for name in self.ADMIN_URLS + ['analytics:dashboard']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)

    def test_only_superusers_assign_roles_and_permissions(self):
        group = Group.objects.create(name='Modérateurs')
        permission = Permission.objects.get(codename='moderate_actionsubmission')
        manager = make_user('mgr', is_staff=True)
        self.client.force_login(manager)
        self.assertEqual(self.client.post(reverse('accounts:role_members', args=[group.pk]), {'members': [manager.pk]}).status_code, 403)
        self.assertEqual(self.client.post(reverse('accounts:role_create'), {'name': 'Pirates', 'permissions': [permission.pk]}).status_code, 403)
        self.assertFalse(Group.objects.filter(name='Pirates').exists())
        self.assertFalse(manager.groups.filter(pk=group.pk).exists())

    def test_moderation_requires_the_moderation_permission(self):
        user = make_user('mod')
        owner = make_user('author')
        submission = make_submission(owner, make_action_type())
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('actions_admin:moderation_list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('actions_admin:moderation_detail', args=[submission.pk])).status_code, 403)
        group = Group.objects.create(name='Modération')
        group.permissions.add(Permission.objects.get(codename='moderate_actionsubmission'))
        user.groups.add(group)
        user = User.objects.get(pk=user.pk)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('actions_admin:moderation_list')).status_code, 200)

    def test_author_cannot_approve_own_submission_even_with_permission(self):
        user = make_user('mod')
        group = Group.objects.create(name='Modération')
        group.permissions.add(Permission.objects.get(codename='moderate_actionsubmission'))
        user.groups.add(group)
        submission = make_submission(user, make_action_type())
        self.client.force_login(user)
        self.client.post(reverse('actions_admin:moderation_detail', args=[submission.pk]), {'decision': 'approve'})
        submission.refresh_from_db()
        self.assertEqual(submission.status, ActionSubmission.Status.PENDING)


class OrganizationOwnershipTests(TestCase):
    def setUp(self):
        self.org_a = make_org('Asso A', Organization.Kind.ASSOCIATION)
        self.org_b = make_org('Asso B', Organization.Kind.ASSOCIATION)
        self.manager_a = association('mgr_a', self.org_a, True)
        self.manager_b = association('mgr_b', self.org_b, True)

    def test_manager_edits_only_their_own_organization(self):
        self.client.force_login(self.manager_a)
        response = self.client.post(reverse('organizations:settings'), {'name': 'Asso A+', 'mission': 'Planter'})
        self.assertEqual(response.status_code, 302)
        self.org_a.refresh_from_db()
        self.org_b.refresh_from_db()
        self.assertEqual(self.org_a.name, 'Asso A+')
        self.assertEqual(self.org_b.name, 'Asso B')

    def test_manager_cannot_modify_another_associations_event(self):
        event = make_event(self.manager_b, status=Event.Status.DRAFT, organization=self.org_b)
        self.client.force_login(self.manager_a)
        self.assertEqual(self.client.get(reverse('community:update', args=[event.slug])).status_code, 403)
        self.assertEqual(self.client.post(reverse('community:submit', args=[event.slug])).status_code, 403)
        self.assertEqual(self.client.get(event.get_absolute_url()).status_code, 404)  # foreign draft is invisible
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.DRAFT)

    def test_colleague_manager_can_edit_own_org_draft(self):
        colleague = association('colleague', self.org_a, True)
        event = make_event(self.manager_a, status=Event.Status.DRAFT, organization=self.org_a)
        self.client.force_login(colleague)
        self.assertEqual(self.client.get(reverse('community:update', args=[event.slug])).status_code, 200)

    def test_participants_page_lists_only_own_registrations(self):
        mine = make_event(self.manager_a, 'Mon atelier', organization=self.org_a)
        other = make_event(self.manager_b, 'Atelier voisin', organization=self.org_b)
        EventParticipation.objects.create(event=mine, user=student('inscrit_a'))
        EventParticipation.objects.create(event=other, user=student('inscrit_b'))
        self.client.force_login(self.manager_a)
        page = self.client.get(reverse('organizations:participants')).content.decode()
        self.assertIn('inscrit_a', page)
        self.assertNotIn('inscrit_b', page)

    def test_manager_pages_require_manager_status(self):
        plain_member = association('plain', self.org_a, False)
        no_org = association('lonely')
        for user in (plain_member, no_org, student('s'), employee('e', make_org('Co'))):
            self.client.force_login(user)
            for name in ('campaigns', 'events', 'proposals', 'participants', 'impact', 'history', 'settings'):
                self.assertEqual(self.client.get(reverse(f'organizations:{name}')).status_code, 403, f'{user.username} {name}')

    def test_association_founds_an_organization_and_becomes_manager(self):
        lonely = association('founder')
        self.client.force_login(lonely)
        response = self.client.post(reverse('organizations:create'), {'name': 'Nouvelle Asso', 'mission': 'Agir'})
        self.assertEqual(response.status_code, 302)
        lonely.refresh_from_db()
        self.assertTrue(lonely.is_org_manager)
        self.assertEqual(lonely.affiliation.name, 'Nouvelle Asso')
        self.assertEqual(lonely.affiliation.kind, Organization.Kind.ASSOCIATION)
        self.assertFalse(lonely.is_superuser)

    def test_student_cannot_found_an_organization(self):
        self.client.force_login(student())
        self.assertEqual(self.client.get(reverse('organizations:create')).status_code, 403)

    def test_event_creation_is_reserved_to_organisers(self):
        self.client.force_login(student())
        self.assertEqual(self.client.get(reverse('community:create')).status_code, 403)
        self.client.force_login(employee('emp', make_org('Co')))
        self.assertEqual(self.client.get(reverse('community:create')).status_code, 403)
        self.client.force_login(self.manager_a)
        self.assertEqual(self.client.get(reverse('community:create')).status_code, 200)

    def test_created_event_belongs_to_the_managers_organization(self):
        self.client.force_login(self.manager_a)
        start = timezone.localtime() + timedelta(days=10)
        response = self.client.post(reverse('community:create'), {
            'title': 'Plantation', 'kind': 'campaign', 'category': 'recycling', 'description': 'On plante.',
            'format': 'on_site', 'location': 'Parc', 'start_at': start.strftime('%Y-%m-%dT%H:%M'),
            'end_at': (start + timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M'), 'target_audience': 'all',
            'registration_deadline': (start - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(response.status_code, 302, getattr(response, 'context', None) and response.context['form'].errors)
        event = Event.objects.get(title='Plantation')
        self.assertEqual(event.organization, self.org_a)
        self.assertEqual(event.status, Event.Status.DRAFT)

    def test_registration_deadline_must_precede_the_start(self):
        self.client.force_login(self.manager_a)
        start = timezone.localtime() + timedelta(days=10)
        response = self.client.post(reverse('community:create'), {
            'title': 'Trop tard', 'kind': 'event', 'category': 'water', 'description': 'x', 'format': 'on_site',
            'location': 'Ici', 'start_at': start.strftime('%Y-%m-%dT%H:%M'),
            'end_at': (start + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'), 'target_audience': 'all',
            'registration_deadline': (start + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(title='Trop tard').exists())

    def test_registration_closed_after_deadline_and_audience_is_enforced(self):
        from community import services
        from core.exceptions import BusinessRuleError
        closed = make_event(self.manager_a, 'Clos', organization=self.org_a,
                            registration_deadline=timezone.now() - timedelta(hours=1))
        with self.assertRaises(BusinessRuleError):
            services.join_event(student('late'), closed)
        employees_only = make_event(self.manager_a, 'Pro', organization=self.org_a, target_audience=Audience.EMPLOYEES)
        with self.assertRaises(BusinessRuleError):
            services.join_event(student('wrong_audience'), employees_only)
        services.join_event(employee('right_audience'), employees_only)
        self.assertEqual(employees_only.participations.count(), 1)


class RestrictedChallengeTests(TestCase):
    def test_association_proposals_stay_pending_until_an_administrator_approves(self):
        org = make_org('Asso', Organization.Kind.ASSOCIATION)
        manager = association('mgr', org, True)
        self.client.force_login(manager)
        response = self.client.post(reverse('challenges:create'), {
            'title': 'Zéro déchet communautaire', 'category': 'recycling', 'difficulty': 'easy',
            'description': 'Réduire les déchets.', 'instructions': 'Trier',
            'start_date': timezone.localdate().isoformat(),
            'end_date': (timezone.localdate() + timedelta(days=14)).isoformat(),
            'duration_days': 14, 'reward_points': 40, 'required_actions': 3,
        })
        self.assertEqual(response.status_code, 302)
        challenge = Challenge.objects.get(title='Zéro déchet communautaire')
        self.assertEqual(challenge.organization, org)
        self.assertEqual(challenge.status, Challenge.Status.DRAFT)
        self.client.post(reverse('challenges:submit', args=[challenge.slug]))
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.PENDING)
        # the proposing organization cannot publish it
        self.assertEqual(self.client.get(reverse('challenges_admin:review_detail', args=[challenge.slug])).status_code, 403)
        self.client.post(reverse('challenges_admin:review_detail', args=[challenge.slug]), {'decision': 'approve', 'reward_points': 40})
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.PENDING)
        # an administrator can
        self.client.force_login(make_superuser())
        self.client.post(reverse('challenges_admin:review_detail', args=[challenge.slug]), {'decision': 'approve', 'reward_points': 40})
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.ACTIVE)


class WorkplacePrivacyTests(TestCase):
    def setUp(self):
        self.acme = make_org('Acme')
        self.globex = make_org('Globex')
        self.alice = employee('alice', self.acme)
        self.bob = employee('bob', self.globex)
        self.acme_team = make_team(self.alice, 'Acme Verte', organization=self.acme)
        self.globex_team = make_team(self.bob, 'Globex Verte', organization=self.globex)

    def test_workplace_team_is_hidden_from_other_organizations(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(self.acme_team.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(self.globex_team.get_absolute_url()).status_code, 404)
        listing = self.client.get(reverse('teams:list')).content.decode()
        self.assertIn('Acme Verte', listing)
        self.assertNotIn('Globex Verte', listing)

    def test_cannot_join_a_team_of_another_organization(self):
        from core.exceptions import BusinessRuleError
        from teams import services
        outsider = student('outsider')
        with self.assertRaises(BusinessRuleError):
            services.join_team(outsider, self.acme_team)
        colleague = employee('colleague', self.acme)
        services.join_team(colleague, self.acme_team)
        self.assertEqual(self.acme_team.memberships.count(), 2)

    def test_leaderboards_are_scoped_and_private(self):
        from analytics import services
        public_owner = student('pub')
        make_team(public_owner, 'Équipe Publique')
        names_public = {t.name for t in services.team_leaderboard(public_only=True)}
        self.assertEqual(names_public, {'Équipe Publique'})
        names_alice = {t.name for t in services.team_leaderboard(viewer=self.alice)}
        self.assertEqual(names_alice, {'Équipe Publique', 'Acme Verte'})
        names_org = {t.name for t in services.team_leaderboard(organization=self.acme)}
        self.assertEqual(names_org, {'Acme Verte'})
        self.client.force_login(self.alice)
        page = self.client.get(reverse('analytics:leaderboard'), {'scope': 'org'}).content.decode()
        self.assertIn('Acme Verte', page)
        self.assertNotIn('Globex Verte', page)

    def test_employee_profiles_are_private_to_their_organization(self):
        colleague = employee('colleague', self.acme)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse('accounts:public_profile', args=['alice'])).status_code, 404)
        self.client.force_login(colleague)
        self.assertEqual(self.client.get(reverse('accounts:public_profile', args=['alice'])).status_code, 200)

    def test_employees_are_excluded_from_the_individual_leaderboard(self):
        from analytics import services
        give_points(self.alice, 50, 'ref-self-alice-50')
        pupil = student('pupil')
        give_points(pupil, 10, 'ref-pupil-10')
        self.assertEqual([u.username for u in services.user_leaderboard()], ['pupil'])

    def test_corporate_dashboard_shows_only_aggregate_company_data(self):
        colleague = employee('colleague', self.acme)
        give_points(colleague, 70, 'ref-colleague-70')
        give_points(self.bob, 999, 'ref-self-bob-999')
        data = dashboards.employee_dashboard(self.alice)
        self.assertEqual(data['summary']['points'], 70)  # other company's 999 points are not included
        self.assertEqual(data['summary']['member_total'], 2)
        self.client.force_login(self.alice)
        page = self.client.get(reverse('analytics:dashboard')).content.decode()
        self.assertNotIn('colleague', page)  # no individual-level data about colleagues


class AdminStatisticsTests(TestCase):
    def test_statistics_reflect_database_records(self):
        from analytics import services
        org = make_org('Asso', Organization.Kind.ASSOCIATION)
        student('s1'), student('s2'), employee('e1'), association('a1', org, True)
        stats = dashboards.admin_counters()
        self.assertEqual((stats['students'], stats['employees'], stats['associations']), (2, 1, 1))
        self.assertEqual(stats['total_organizations'], 1)
        overview = services.admin_overview()
        self.assertEqual(overview['total_users'], 4)
        self.assertEqual(overview['pending_submissions'], 0)
        author = User.objects.get(username='s1')
        make_submission(author, make_action_type())
        make_submission(author, make_action_type('Autre'), days_ago=2)
        self.assertEqual(services.admin_overview()['pending_submissions'], 2)

    def test_suspicious_submissions_are_derived_from_data(self):
        author = student('burst')
        no_proof = make_action_type('Avec preuve', requires_evidence=True)
        make_submission(author, no_proof)
        flagged = list(dashboards.suspicious_submissions())
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0].user, author)

    def test_user_growth_series_is_cumulative(self):
        student('s1'), student('s2')
        series = dashboards.cumulative_users(4)
        self.assertEqual(len(series), 4)
        self.assertEqual(series[-1]['value'], 2)
        self.assertEqual(series[0]['value'], 0)


class AnnouncementTests(TestCase):
    def test_announcement_reaches_only_the_chosen_audience(self):
        admin = make_superuser()
        org = make_org()
        e1, e2 = employee('e1', org), employee('e2')
        s1 = student('s1')
        self.client.force_login(admin)
        response = self.client.post(reverse('notifications:announce'), {
            'title': 'Maintenance', 'message': 'Ce soir.', 'audience': 'employee',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.filter(title='Maintenance').count(), 2)
        self.assertFalse(Notification.objects.filter(title='Maintenance', recipient=s1).exists())
        self.client.post(reverse('notifications:announce'), {
            'title': 'Pour Acme', 'message': 'Réunion.', 'audience': 'organization', 'organization': org.pk,
        })
        self.assertEqual(list(Notification.objects.filter(title='Pour Acme').values_list('recipient', flat=True)), [e1.pk])

    def test_organization_audience_requires_an_organization(self):
        self.client.force_login(make_superuser())
        response = self.client.post(reverse('notifications:announce'), {
            'title': 'x', 'message': 'y', 'audience': 'organization',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

    def test_audit_log_records_administrative_decisions(self):
        from analytics.models import ActivityLog
        admin = make_superuser()
        target = student('target')
        self.client.force_login(admin)
        self.client.post(reverse('accounts:user_edit', args=[target.pk]), {'organization_type': 'employee', 'is_active': 'on'})
        self.assertTrue(ActivityLog.objects.filter(verb=ActivityLog.Verb.ACCOUNT_UPDATED, actor=admin).exists())
        page = self.client.get(reverse('analytics:audit_log')).content.decode()
        self.assertIn('Compte modifié', page)

    def test_organization_crud_is_admin_only_and_works(self):
        self.client.force_login(make_superuser())
        self.client.post(reverse('organizations:admin_create'), {'name': 'Nouvelle Entreprise', 'kind': 'company', 'is_active': 'on'})
        org = Organization.objects.get(name='Nouvelle Entreprise')
        self.client.post(reverse('organizations:admin_update', args=[org.pk]), {'name': 'Renommée', 'kind': 'company', 'is_active': 'on'})
        org.refresh_from_db()
        self.assertEqual(org.name, 'Renommée')
        self.client.post(reverse('organizations:admin_delete', args=[org.pk]))
        self.assertFalse(Organization.objects.filter(pk=org.pk).exists())
