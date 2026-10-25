from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from core.testing import PASSWORD, make_superuser, make_user


class RegistrationTests(TestCase):
    def registration_data(self, **extra):
        data = {
            'first_name': 'Amel', 'last_name': 'Ben Ali', 'username': 'amel', 'email': 'Amel@Example.com',
            'organization_type': 'student', 'password1': PASSWORD, 'password2': PASSWORD,
        }
        data.update(extra)
        return data

    def test_registration_creates_user_with_default_role_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data())
        self.assertRedirects(response, reverse('analytics:dashboard'))
        user = User.objects.get(username='amel')
        self.assertEqual(user.email, 'amel@example.com')
        self.assertTrue(user.groups.filter(name=settings.ECOTEAMS_DEFAULT_ROLE).exists())
        self.assertNotEqual(user.password, PASSWORD)  # hashed
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_cannot_grant_privileges(self):
        admin_group = Group.objects.create(name='Super groupe')
        self.client.post(reverse('accounts:register'), self.registration_data(
            is_superuser='on', is_staff='on', groups=[admin_group.pk], user_permissions=[1],
        ))
        user = User.objects.get(username='amel')
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.groups.filter(pk=admin_group.pk).exists())
        self.assertFalse(user.user_permissions.exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        make_user('existing', email='amel@example.com')
        response = self.client.post(reverse('accounts:register'), self.registration_data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Un compte utilise déjà cette adresse e-mail.')
        self.assertFalse(User.objects.filter(username='amel').exists())

    def test_password_mismatch_shows_error(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data(password2='autre-chose-123'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='amel').exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = make_user('bob')
        self.admin = make_superuser()

    def test_user_is_redirected_to_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': PASSWORD})
        self.assertRedirects(response, reverse('analytics:dashboard'))

    def test_admin_is_redirected_to_admin_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'admin', 'password': PASSWORD})
        self.assertRedirects(response, reverse('analytics:admin_dashboard'))

    def test_login_with_email(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'BOB@example.com', 'password': PASSWORD})
        self.assertRedirects(response, reverse('analytics:dashboard'))

    def test_wrong_password_is_refused(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': 'faux'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('core:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_anonymous_users_are_redirected_to_login(self):
        for name in ['analytics:dashboard', 'teams:list', 'challenges:list', 'actions:list', 'goals:list',
                     'community:list', 'analytics:leaderboard', 'analytics:history', 'notifications:list',
                     'accounts:profile']:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f'{reverse("accounts:login")}?next={reverse(name)}', msg_prefix=name)


class ProfileTests(TestCase):
    def test_profile_edit_ignores_privilege_fields(self):
        user = make_user('carla')
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Carla', 'last_name': 'Test', 'email': 'carla@example.com', 'organization_type': 'employee',
            'is_superuser': 'on', 'is_staff': 'on', 'username': 'hacker',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        user.refresh_from_db()
        self.assertEqual(user.organization_type, 'student')  # the category is changed by an administrator only
        self.assertEqual(user.username, 'carla')
        self.assertFalse(user.is_superuser or user.is_staff)

    def test_password_change(self):
        user = make_user('dina')
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': PASSWORD, 'new_password1': 'Nouveau-Mot-De-Passe-42', 'new_password2': 'Nouveau-Mot-De-Passe-42',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('Nouveau-Mot-De-Passe-42'))


class RoleManagementTests(TestCase):
    def setUp(self):
        self.user = make_user('eve')
        self.admin = make_superuser()
        self.moderate = Permission.objects.get(codename='moderate_actionsubmission')

    def test_role_pages_are_superuser_only(self):
        staff = make_user('staffer', is_staff=True)
        powerful = make_user('powerful')
        group = Group.objects.create(name='Tout-puissant')
        group.permissions.set(Permission.objects.all())
        powerful.groups.add(group)
        urls = [reverse('accounts:role_list'), reverse('accounts:role_create'), reverse('accounts:user_list'),
                reverse('accounts:role_update', args=[group.pk]), reverse('accounts:role_members', args=[group.pk]),
                reverse('accounts:user_edit', args=[self.user.pk])]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302, url)  # anonymous → login
            for account in (self.user, staff, powerful):
                self.client.force_login(account)
                self.assertEqual(self.client.get(url).status_code, 403, f'{account} {url}')
                self.client.logout()
        self.client.force_login(self.admin)
        for url in urls:
            self.assertIn(self.client.get(url).status_code, (200, 302), url)

    def test_regular_user_cannot_create_role_or_assign_permissions(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:role_create'), {'name': 'Pirate', 'permissions': [self.moderate.pk]})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Group.objects.filter(name='Pirate').exists())

    def test_regular_user_cannot_change_role_members(self):
        group = Group.objects.create(name='Modérateur')
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:role_members', args=[group.pk]), {'members': [self.user.pk]})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.user.groups.filter(pk=group.pk).exists())

    def test_superuser_creates_role_with_permissions_without_joining_it(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:role_create'), {
            'name': 'Modérateur', 'description': 'Modère les actions', 'permissions': [self.moderate.pk],
        })
        self.assertRedirects(response, reverse('accounts:role_list'))
        group = Group.objects.get(name='Modérateur')
        self.assertEqual(list(group.permissions.all()), [self.moderate])
        self.assertEqual(group.role.description, 'Modère les actions')
        self.assertFalse(group.user_set.filter(pk=self.admin.pk).exists())

    def test_reserved_role_names_are_refused(self):
        self.client.force_login(self.admin)
        for name in ('Administrateur', 'admin', settings.ECOTEAMS_DEFAULT_ROLE):
            response = self.client.post(reverse('accounts:role_create'), {'name': name})
            self.assertEqual(response.status_code, 200)
        self.assertFalse(Group.objects.filter(name__iexact='administrateur').exists())

    def test_assigning_role_members_grants_permission(self):
        group = Group.objects.create(name='Modérateur')
        group.permissions.add(self.moderate)
        self.client.force_login(self.admin)
        self.client.post(reverse('accounts:role_members', args=[group.pk]), {'members': [self.user.pk]})
        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.has_perm('actions.moderate_actionsubmission'))
        self.assertTrue(user.notifications.filter(title='Vos rôles ont évolué').exists())

    def test_default_role_cannot_be_deleted_but_custom_role_can(self):
        default = Group.objects.get(name=settings.ECOTEAMS_DEFAULT_ROLE)
        custom = Group.objects.create(name='Organisateur')
        Role.objects.create(group=custom)
        self.client.force_login(self.admin)
        self.client.post(reverse('accounts:role_delete', args=[default.pk]))
        self.assertTrue(Group.objects.filter(pk=default.pk).exists())
        self.client.post(reverse('accounts:role_delete', args=[custom.pk]))
        self.assertFalse(Group.objects.filter(pk=custom.pk).exists())

    def test_default_role_permissions_are_locked(self):
        default = Group.objects.get(name=settings.ECOTEAMS_DEFAULT_ROLE)
        self.client.force_login(self.admin)
        self.client.post(reverse('accounts:role_update', args=[default.pk]), {
            'name': 'Renommé', 'description': 'Nouvelle description', 'permissions': [self.moderate.pk],
        })
        default.refresh_from_db()
        self.assertEqual(default.name, settings.ECOTEAMS_DEFAULT_ROLE)
        self.assertFalse(default.permissions.exists())
        self.assertEqual(default.role.description, 'Nouvelle description')

    def test_superuser_manages_user_access_but_not_other_admins(self):
        group = Group.objects.create(name='Modérateur')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:user_edit', args=[self.user.pk]), {'groups': [group.pk], 'organization_type': 'student'})
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.groups.filter(pk=group.pk).exists())
        self.assertTrue(self.user.groups.filter(name=settings.ECOTEAMS_DEFAULT_ROLE).exists())
        other_admin = make_superuser('admin2')
        self.client.post(reverse('accounts:user_edit', args=[other_admin.pk]), {'groups': []})
        other_admin.refresh_from_db()
        self.assertTrue(other_admin.is_active and other_admin.is_superuser)
