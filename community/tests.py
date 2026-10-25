from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.exceptions import BusinessRuleError
from core.testing import make_event, make_superuser, make_team, make_user
from gamification.models import Badge, UserBadge
from notifications.models import Notification

from . import services
from .models import Event, EventParticipation


class EventWorkflowTests(TestCase):
    def setUp(self):
        self.organizer = make_user('organizer', organization_type='association')
        self.user = make_user('guest')
        self.admin = make_superuser()

    def event_data(self, **extra):
        start = timezone.localtime() + timedelta(days=3)
        data = {'title': 'Nettoyage du parc', 'kind': 'event', 'category': 'recycling', 'description': 'Venez nombreux',
                'format': 'on_site', 'location': 'Parc central', 'online_url': '',
                'start_at': start.strftime('%Y-%m-%dT%H:%M'),
                'end_at': (start + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
                'target_audience': 'all', 'capacity': 10, 'participation_goal': ''}
        data.update(extra)
        return data

    def test_created_event_is_private_draft(self):
        self.client.force_login(self.organizer)
        self.client.post(reverse('community:create'), self.event_data())
        event = Event.objects.get()
        self.assertEqual((event.status, event.organizer), (Event.Status.DRAFT, self.organizer))
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(event.get_absolute_url()).status_code, 404)

    def test_location_required_for_on_site_events(self):
        self.client.force_login(self.organizer)
        response = self.client.post(reverse('community:create'), self.event_data(location=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.exists())

    def test_only_reviewers_publish(self):
        event = make_event(self.organizer, status=Event.Status.PENDING)
        self.client.force_login(self.organizer)
        response = self.client.post(reverse('community_admin:review_detail', args=[event.slug]), {'decision': 'publish'})
        self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.PENDING)
        self.client.force_login(self.admin)
        self.client.post(reverse('community_admin:review_detail', args=[event.slug]), {'decision': 'publish'})
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.PUBLISHED)
        self.assertTrue(Notification.objects.filter(recipient=self.user, kind='event').exists())

    def test_submit_and_edit_rules(self):
        event = make_event(self.organizer, status=Event.Status.DRAFT)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('community:update', args=[event.slug]), self.event_data()).status_code, 403)
        self.assertEqual(self.client.post(reverse('community:submit', args=[event.slug])).status_code, 403)
        self.client.force_login(self.organizer)
        self.client.post(reverse('community:update', args=[event.slug]), self.event_data(title='Titre modifié'))
        self.client.post(reverse('community:submit', args=[event.slug]))
        event.refresh_from_db()
        self.assertEqual((event.title, event.status), ('Titre modifié', Event.Status.PENDING))

    def test_delete_rules(self):
        draft = make_event(self.organizer, title='Brouillon', status=Event.Status.DRAFT)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('community:delete', args=[draft.slug])).status_code, 403)
        self.client.force_login(self.organizer)
        self.client.post(reverse('community:delete', args=[draft.slug]))
        self.assertFalse(Event.objects.filter(pk=draft.pk).exists())


class EventParticipationTests(TestCase):
    def setUp(self):
        self.organizer = make_user('organizer')
        self.user = make_user('guest')
        self.team = make_team(self.user)
        self.event = make_event(self.organizer, capacity=1)

    def test_join_records_team_and_notifies_organizer(self):
        self.client.force_login(self.user)
        self.client.post(reverse('community:join', args=[self.event.slug]))
        participation = EventParticipation.objects.get()
        self.assertEqual(participation.team, self.team)
        self.assertTrue(Notification.objects.filter(recipient=self.organizer, title='Nouvelle inscription').exists())

    def test_capacity_and_duplicates(self):
        services.join_event(self.user, self.event)
        with self.assertRaises(BusinessRuleError):
            services.join_event(self.user, self.event)
        with self.assertRaises(BusinessRuleError):
            services.join_event(make_user('late'), self.event)
        self.assertEqual(EventParticipation.objects.count(), 1)

    def test_drafts_cannot_be_joined(self):
        draft = make_event(self.organizer, title='Brouillon', status=Event.Status.DRAFT)
        with self.assertRaises(BusinessRuleError):
            services.join_event(self.user, draft)

    def test_cancel_participation_only_before_start(self):
        services.join_event(self.user, self.event)
        services.leave_event(self.user, self.event)
        self.assertFalse(EventParticipation.objects.exists())
        started = make_event(self.organizer, title='En cours', start_in_hours=-1)
        services.join_event(self.user, started)
        with self.assertRaises(BusinessRuleError):
            services.leave_event(self.user, started)

    def test_reminders_are_sent_once(self):
        soon = make_event(self.organizer, title='Demain', start_in_hours=20)
        services.join_event(self.user, soon)
        self.assertEqual(services.send_due_reminders(), 1)
        self.assertEqual(services.send_due_reminders(), 0)
        self.assertTrue(Notification.objects.filter(recipient=self.user, title='Bientôt : Demain').exists())

    def test_event_badge(self):
        badge = Badge.objects.create(name='Engagé', description='x', rule=Badge.Rule.EVENTS_JOINED, threshold=2)
        services.join_event(self.user, self.event)
        services.join_event(self.user, make_event(self.organizer, title='Deuxième'))
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=badge).exists())

    def test_organizer_cancels_and_participants_are_notified(self):
        services.join_event(self.user, self.event)
        self.client.force_login(self.organizer)
        self.client.post(reverse('community:cancel', args=[self.event.slug]), {'reason': 'Météo'})
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.Status.CANCELLED)
        self.assertTrue(Notification.objects.filter(recipient=self.user, title='Événement annulé').exists())
