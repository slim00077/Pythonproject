from django.test import TestCase
from django.urls import reverse

from core.testing import make_user

from .models import Notification, NotificationPreference
from .services import notify, notify_many


class NotificationTests(TestCase):
    def setUp(self):
        self.user = make_user('reader')
        self.other = make_user('other')
        notify(self.user, Notification.Kind.TEAM, 'Bienvenue', 'Message', '/teams/')
        self.notification = Notification.objects.get(recipient=self.user)

    def test_other_users_cannot_access_private_notifications(self):
        self.client.force_login(self.other)
        pk = self.notification.pk
        self.assertEqual(self.client.get(reverse('notifications:detail', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('notifications:read', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('notifications:delete', args=[pk])).status_code, 404)
        self.client.post(reverse('notifications:read_all'))
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)
        self.assertNotContains(self.client.get(reverse('notifications:list')), 'Bienvenue')

    def test_view_marks_as_read(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('notifications:detail', args=[self.notification.pk]))
        self.assertContains(response, 'Bienvenue')
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_mark_read_mark_all_and_delete(self):
        notify(self.user, Notification.Kind.BADGE, 'Badge', 'x')
        self.client.force_login(self.user)
        self.client.post(reverse('notifications:read', args=[self.notification.pk]))
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 1)
        self.client.post(reverse('notifications:read_all'))
        self.assertFalse(Notification.objects.filter(recipient=self.user, is_read=False).exists())
        self.client.post(reverse('notifications:delete', args=[self.notification.pk]))
        self.assertFalse(Notification.objects.filter(pk=self.notification.pk).exists())

    def test_preferences_mute_a_kind(self):
        self.client.force_login(self.user)
        self.client.post(reverse('notifications:preferences'), {
            field: 'on' for field in NotificationPreference.KIND_FIELDS if field != 'badge'})
        self.assertFalse(NotificationPreference.objects.get(user=self.user).badge)
        self.assertEqual(notify(self.user, Notification.Kind.BADGE, 'Muet'), 0)
        self.assertEqual(notify(self.user, Notification.Kind.TEAM, 'Audible'), 1)
        self.assertEqual(notify(self.user, Notification.Kind.SYSTEM, 'Toujours'), 1)

    def test_external_links_are_discarded(self):
        notify_many([self.user], Notification.Kind.SYSTEM, 'Lien', 'x', '//evil.example.com/phishing')
        notify_many([self.user], Notification.Kind.SYSTEM, 'Lien 2', 'x', 'https://evil.example.com')
        self.assertFalse(Notification.objects.filter(title__startswith='Lien').exclude(link='').exists())

    def test_inactive_users_are_not_notified(self):
        self.other.is_active = False
        self.other.save()
        self.assertEqual(notify(self.other, Notification.Kind.TEAM, 'x'), 0)

    def test_header_dropdown_shows_unread_count(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertEqual(response.context['unread_notifications_count'], 1)
