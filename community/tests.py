from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from actions.models import ActionSubmission
from challenges.models import ChallengeParticipation
from core.exceptions import BusinessRuleError
from core.testing import (
    make_action_type, make_challenge, make_event, make_submission, make_superuser, make_team, make_user,
)
from gamification.models import Badge, PointTransaction, UserBadge
from notifications.models import Notification
from organizations.models import Organization

from . import services
from .ai.impact import compare_campaign_impact, estimate_campaign_impact
from .ai.participation import predict_event_participation
from .ai.providers import generate_event_content
from .ai.recommender import recommend_events
from .ai.tagger import suggest_event_tags
from .models import CampaignImpactFactor, Event, EventParticipation


class EventRecommendationTests(TestCase):
    def setUp(self):
        self.organizer = make_user('recommendation_organizer', organization_type='association')
        self.user = make_user('recommendation_user')

    def test_recommends_events_matching_approved_actions_with_explanation(self):
        recycling = make_action_type(category='recycling')
        for days_ago in range(1, 4):
            make_submission(
                self.user, recycling, days_ago=days_ago, status=ActionSubmission.Status.APPROVED,
            )
        matching = make_event(self.organizer, title='Atelier recyclage', category='recycling')
        make_event(self.organizer, title='Trajet à vélo', category='transport')

        recommendations = recommend_events(self.user)

        self.assertEqual(recommendations[0].event, matching)
        self.assertIn('3 action(s) de recyclage', recommendations[0].reason)

    def test_challenge_team_and_favorite_category_affect_recommendations(self):
        team = make_team(self.user, focus_area='water')
        challenge = make_challenge(self.user, category='water')
        ChallengeParticipation.objects.create(user=self.user, challenge=challenge, team=team)
        self.user.favorite_category = 'water'
        self.user.save(update_fields=['favorite_category'])
        matching = make_event(self.organizer, title='Protection de l’eau', category='water')
        make_event(self.organizer, title='Transport responsable', category='transport')

        recommendations = recommend_events(self.user)

        self.assertEqual(recommendations[0].event, matching)
        self.assertIn('défi(s) sur le thème « Eau »', recommendations[0].reason)

    def test_excludes_joined_private_past_and_wrong_audience_events(self):
        joined = make_event(self.organizer, title='Déjà rejoint')
        EventParticipation.objects.create(event=joined, user=self.user)
        make_event(self.organizer, title='Brouillon privé', status=Event.Status.DRAFT)
        make_event(self.organizer, title='Événement passé', start_in_hours=-48)
        make_event(self.organizer, title='Public salarié', target_audience='employees')
        eligible = make_event(self.organizer, title='Tout public')

        recommendations = recommend_events(self.user)

        self.assertEqual([item.event for item in recommendations], [eligible])

    def test_organization_and_city_are_used_as_relevance_signals(self):
        organization = Organization.objects.create(
            name='Association du quartier', focus_area='energy', city='Tunis',
        )
        self.user.affiliation = organization
        self.user.save(update_fields=['affiliation'])
        matching = make_event(
            self.organizer, title='Atelier de l’association', category='energy',
            location='Tunis', organization=organization,
        )
        make_event(self.organizer, title='Autre atelier énergie', category='energy', location='Sfax')

        recommendations = recommend_events(self.user)

        self.assertEqual(recommendations[0].event, matching)
        self.assertIn('organisation', recommendations[0].reason)

    def test_points_and_badges_increase_the_popularity_signal(self):
        popular = make_event(self.organizer, title='Rencontre populaire', category='recycling')
        EventParticipation.objects.create(event=popular, user=make_user('attendee'))
        make_event(self.organizer, title='Atelier sans inscrits', category='recycling')
        initial_score = next(
            item.score for item in recommend_events(self.user) if item.event == popular
        )
        PointTransaction.objects.create(
            user=self.user, amount=100, reason=PointTransaction.Reason.ACTION_APPROVED,
            description='Action validée', reference='recommendation-test-points',
        )
        badge = Badge.objects.create(
            name='Badge recommandation', description='Badge de test',
            rule=Badge.Rule.EVENTS_JOINED, threshold=1,
        )
        UserBadge.objects.create(user=self.user, badge=badge)

        updated_score = next(
            item.score for item in recommend_events(self.user) if item.event == popular
        )

        self.assertGreater(updated_score, initial_score)

    def test_user_can_open_community_list_with_recommendations(self):
        make_event(self.organizer, title='Atelier recommandé')
        self.client.force_login(self.user)

        response = self.client.get(reverse('community:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recommandé pour vous')
        self.assertContains(response, 'Atelier recommandé')


class EventTagSuggestionTests(TestCase):
    def setUp(self):
        self.organizer = make_user('tag_organizer', organization_type='association')
        self.member = make_user('tag_member')

    def test_suggests_category_and_tags_from_french_text(self):
        result = suggest_event_tags(
            'Nettoyage de la plage',
            'Collecte des déchets plastiques et protection de l’eau.',
        )

        self.assertEqual(result['category'], 'recycling')
        self.assertIn('#Recyclage', result['tags'])
        self.assertIn('#ProtectionDeLEau', result['tags'])

    def test_returns_no_category_or_tags_without_known_keywords(self):
        result = suggest_event_tags('Rencontre conviviale', 'Échange entre les participants.')

        self.assertIsNone(result['category'])
        self.assertEqual(result['tags'], [])

    def test_tag_endpoint_is_limited_to_organizers(self):
        url = reverse('community:tag_suggestions')
        self.assertEqual(self.client.post(url, {'title': 'Nettoyage'}).status_code, 302)
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(url, {'title': 'Nettoyage'}).status_code, 403)

    def test_organizer_can_request_tag_suggestions(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse('community:tag_suggestions'),
            {'title': 'Atelier vélo', 'description': 'Promouvoir la mobilité douce.'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['category'], 'transport')
        self.assertIn('#MobiliteDouce', response.json()['tags'])

    def test_organizer_sees_tag_suggestion_button_on_event_form(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse('community:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suggérer une catégorie et des tags')

    def test_tag_endpoint_enforces_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.organizer)

        response = client.post(reverse('community:tag_suggestions'), {'title': 'Atelier vélo'})

        self.assertEqual(response.status_code, 403)


@override_settings(AI_PROVIDER='template', AI_API_KEY='')
class EventAIGenerationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.organizer = make_user('ai_organizer', organization_type='association')
        self.user = make_user('ai_member')
        self.details = {
            'title': 'Nettoyage du parc',
            'category': 'recycling',
            'start_at': timezone.now() + timedelta(days=7),
            'location': 'Parc central',
        }

    def generation_data(self):
        return {
            'title': self.details['title'],
            'category': self.details['category'],
            'start_at': self.details['start_at'].strftime('%Y-%m-%dT%H:%M'),
            'location': self.details['location'],
        }

    def test_template_provider_works_without_api_key(self):
        content, provider = generate_event_content(self.details)

        self.assertEqual(provider, 'template')
        self.assertIn('Nettoyage du parc', content.description)
        self.assertTrue(content.program)
        self.assertTrue(content.hashtags)

    @override_settings(AI_PROVIDER='openai_compatible', AI_API_KEY='test-key')
    def test_remote_timeout_falls_back_to_templates(self):
        with patch('community.ai.providers.urlopen', side_effect=TimeoutError):
            content, provider = generate_event_content(self.details)

        self.assertEqual(provider, 'template')
        self.assertIn('Nettoyage du parc', content.description)

    @override_settings(
        AI_PROVIDER='openai_compatible', AI_API_KEY='test-key', AI_MODEL='test-model',
        AI_TIMEOUT=3, AI_API_BASE_URL='https://ai.example/v1',
    )
    def test_openai_compatible_provider_validates_output_and_sends_only_event_details(self):
        response_body = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'description': 'Une action collective pour le recyclage.',
                        'program': ['Accueil', 'Atelier', 'Bilan'],
                        'hashtags': ['#Recyclage', '#EcoTeams'],
                    }),
                },
            }],
        }
        response = BytesIO(json.dumps(response_body).encode('utf-8'))
        details = {**self.details, 'email': 'private@example.com'}
        with patch('community.ai.providers.urlopen', return_value=response) as mocked:
            content, provider = generate_event_content(details)

        sent_request = mocked.call_args.args[0]
        sent_payload = json.loads(sent_request.data.decode('utf-8'))
        prompt = sent_payload['messages'][1]['content']
        self.assertEqual(provider, 'llm')
        self.assertEqual(content.hashtags, ('#Recyclage', '#EcoTeams'))
        self.assertIn('Nettoyage du parc', prompt)
        self.assertNotIn('private@example.com', prompt)
        self.assertEqual(mocked.call_args.kwargs['timeout'], 3)

    def test_generation_endpoint_requires_login_and_organizer_permission(self):
        url = reverse('community:ai_generate')
        self.assertEqual(self.client.post(url, self.generation_data()).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url, self.generation_data()).status_code, 403)

    def test_organizer_receives_editable_generation_fields_as_json(self):
        self.client.force_login(self.organizer)

        response = self.client.post(reverse('community:ai_generate'), self.generation_data())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['provider'], 'template')
        self.assertIn('description', response.json())
        self.assertTrue(response.json()['program'])
        self.assertTrue(response.json()['hashtags'])

    def test_generation_endpoint_rejects_invalid_input_and_limits_calls(self):
        self.client.force_login(self.organizer)
        url = reverse('community:ai_generate')
        invalid = self.client.post(url, {'title': '', 'category': 'unknown'})
        self.assertEqual(invalid.status_code, 400)
        for _ in range(5):
            self.assertEqual(self.client.post(url, self.generation_data()).status_code, 200)

        limited = self.client.post(url, self.generation_data())

        self.assertEqual(limited.status_code, 429)
        self.assertIn('5 générations par minute', limited.json()['error'])

    def test_generation_endpoint_enforces_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.organizer)

        response = csrf_client.post(reverse('community:ai_generate'), self.generation_data())

        self.assertEqual(response.status_code, 403)


class CampaignImpactTests(TestCase):
    def setUp(self):
        self.organizer = make_user('impact_organizer', organization_type='association')
        self.participants = [make_user(f'impact_participant_{index}') for index in range(2)]
        self.factor = CampaignImpactFactor.objects.get(category='water')
        self.factor.co2_kg_per_participant_day = Decimal('0.5000')
        self.factor.points_per_participant_day = 12
        self.factor.source = 'Facteur de test'
        self.factor.methodology = 'Valeur de test pour le calcul.'
        self.factor.save()

    def test_uses_goal_duration_and_category_factor(self):
        campaign = make_event(
            self.organizer, kind=Event.Kind.CAMPAIGN, start_in_hours=72,
            capacity=10, participation_goal=8, category='water',
        )

        estimate = estimate_campaign_impact(campaign)

        self.assertEqual(estimate.participants, 8)
        self.assertEqual(estimate.duration_days, Decimal('0.0833'))
        self.assertEqual(estimate.co2_saved_kg, Decimal('0.333'))
        self.assertEqual(estimate.potential_points, 8)

    def test_falls_back_to_registrations_when_no_goal_or_capacity(self):
        campaign = make_event(self.organizer, kind=Event.Kind.CAMPAIGN, category='water')
        for participant in self.participants:
            EventParticipation.objects.create(event=campaign, user=participant)

        estimate = estimate_campaign_impact(campaign)

        self.assertEqual(estimate.participants, 2)

    def test_returns_no_estimate_without_active_factor_or_campaign(self):
        campaign = make_event(
            self.organizer, title='Campagne sans facteur', kind=Event.Kind.CAMPAIGN,
            category='water',
        )
        event = make_event(self.organizer, title='Événement', kind=Event.Kind.EVENT)
        self.factor.is_active = False
        self.factor.save(update_fields=['is_active'])

        self.assertIsNone(estimate_campaign_impact(campaign))
        self.assertIsNone(estimate_campaign_impact(event))

    def test_records_actual_result_and_compares_it(self):
        campaign = make_event(
            self.organizer, kind=Event.Kind.CAMPAIGN, start_in_hours=-48, capacity=2, category='water',
        )
        estimate = estimate_campaign_impact(campaign)

        services.record_campaign_impact(self.organizer, campaign, Decimal('0.500'))
        campaign.refresh_from_db()
        comparison = compare_campaign_impact(campaign, estimate)

        self.assertEqual(campaign.actual_co2_saved_kg, Decimal('0.500'))
        self.assertEqual(comparison['relation'], 'above')
        self.assertGreater(comparison['difference_kg'], Decimal('0'))

    def test_only_organizer_can_record_actual_impact(self):
        campaign = make_event(
            self.organizer, kind=Event.Kind.CAMPAIGN, start_in_hours=-48, category='water',
        )

        with self.assertRaises(BusinessRuleError):
            services.record_campaign_impact(self.participants[0], campaign, Decimal('0.500'))

    def test_seeded_factors_are_marked_as_illustrative(self):
        factor = CampaignImpactFactor.objects.get(category='recycling')

        self.assertIn('illustrative', factor.source)
        self.assertIn('sans source empirique', factor.methodology)

    def test_campaign_detail_shows_estimate_and_accepts_actual_result(self):
        campaign = make_event(
            self.organizer, kind=Event.Kind.CAMPAIGN, start_in_hours=-48, capacity=2, category='water',
        )
        self.client.force_login(self.organizer)

        response = self.client.get(campaign.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Impact écologique estimé')
        self.assertContains(response, 'Enregistrer le résultat réel')
        response = self.client.post(
            reverse('community:record_impact', args=[campaign.slug]),
            {'actual_co2_saved_kg': '0.500'},
        )

        self.assertRedirects(response, campaign.get_absolute_url())
        campaign.refresh_from_db()
        self.assertEqual(campaign.actual_co2_saved_kg, Decimal('0.500'))


class EventParticipationPredictionTests(TestCase):
    def setUp(self):
        self.organizer = make_user('prediction_organizer', organization_type='association')
        self.attendee = make_user('prediction_attendee')
        self.history_index = 0

    def add_history(self, attended, category='recycling'):
        self.history_index += 1
        event = make_event(
            self.organizer, title=f'Historique {self.history_index}',
            status=Event.Status.COMPLETED, start_in_hours=-72, category=category,
        )
        EventParticipation.objects.create(
            event=event,
            user=make_user(f'prediction_history_{self.history_index}'),
            joined_at=event.start_at - timedelta(days=3),
            attended=attended,
        )

    def test_no_forecast_is_returned_without_recorded_attendance(self):
        event = make_event(self.organizer, start_in_hours=72)

        self.assertIsNone(predict_event_participation(event))

    def test_forecast_uses_category_and_registration_lead_time_history(self):
        for _ in range(5):
            self.add_history(False, category='recycling')
            self.add_history(True, category='water')
        recycling_event = make_event(
            self.organizer, title='Futur recyclage', start_in_hours=72, category='recycling',
        )
        water_event = make_event(
            self.organizer, title='Futur eau', start_in_hours=72, category='water',
        )
        EventParticipation.objects.create(event=recycling_event, user=self.attendee)
        water_attendee = make_user('water_attendee')
        EventParticipation.objects.create(event=water_event, user=water_attendee)

        recycling_forecast = predict_event_participation(recycling_event)
        water_forecast = predict_event_participation(water_event)

        self.assertEqual(recycling_forecast.registrations, 1)
        self.assertGreater(recycling_forecast.absence_rate, water_forecast.absence_rate)
        self.assertTrue(recycling_forecast.is_high_absence_risk)
        self.assertEqual(recycling_forecast.at_risk_participations[0].user, self.attendee)

    def test_forecast_is_visible_only_to_the_event_organizer(self):
        self.add_history(False)
        event = make_event(self.organizer, title='Prévision privée', start_in_hours=72)
        EventParticipation.objects.create(event=event, user=self.attendee)

        self.client.force_login(self.organizer)
        organizer_response = self.client.get(event.get_absolute_url())
        self.client.force_login(self.attendee)
        member_response = self.client.get(event.get_absolute_url())

        self.assertContains(organizer_response, 'Prévision de participation')
        self.assertNotContains(member_response, 'Prévision de participation')

    def test_organizer_can_record_attendance_after_event(self):
        event = make_event(
            self.organizer, title='Événement terminé', start_in_hours=-48,
        )
        participation = EventParticipation.objects.create(event=event, user=self.attendee)

        services.record_event_attendance(self.organizer, event, participation, True)
        participation.refresh_from_db()

        self.assertIs(participation.attended, True)

    def test_attendance_page_updates_presence(self):
        event = make_event(
            self.organizer, title='Présences à saisir', start_in_hours=-48,
        )
        participation = EventParticipation.objects.create(event=event, user=self.attendee)
        self.client.force_login(self.organizer)

        response = self.client.get(reverse('community:attendance', args=[event.slug]))

        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse('community:attendance', args=[event.slug]),
            {
                'participation_id': participation.pk,
                'page': 1,
                f'attendance-{participation.pk}-attended': 'present',
            },
        )

        self.assertEqual(response.status_code, 302)
        participation.refresh_from_db()
        self.assertIs(participation.attended, True)

    def test_risk_reminder_uses_notifications_and_is_sent_once(self):
        for _ in range(5):
            self.add_history(False)
        event = make_event(
            self.organizer, title='Rappel présence', start_in_hours=72,
        )
        participation = EventParticipation.objects.create(event=event, user=self.attendee)

        sent = services.send_absence_risk_reminders(self.organizer, event)

        self.assertEqual(sent, 1)
        self.assertTrue(Notification.objects.filter(recipient=self.attendee, title='Rappel : Rappel présence').exists())
        participation.refresh_from_db()
        self.assertTrue(participation.reminder_sent)
        with self.assertRaises(BusinessRuleError):
            services.send_absence_risk_reminders(self.organizer, event)

    def test_organizer_can_trigger_risk_reminders_from_event_page(self):
        for _ in range(5):
            self.add_history(False)
        event = make_event(
            self.organizer, title='Rappel depuis la fiche', start_in_hours=72,
        )
        EventParticipation.objects.create(event=event, user=self.attendee)
        self.client.force_login(self.organizer)

        response = self.client.post(reverse('community:remind_risk', args=[event.slug]))

        self.assertRedirects(response, event.get_absolute_url())
        self.assertTrue(Notification.objects.filter(
            recipient=self.attendee, title='Rappel : Rappel depuis la fiche',
        ).exists())


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
