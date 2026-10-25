from django.test import TestCase, override_settings
from django.urls import reverse

from core.testing import make_action_type, make_user

from .services import ask


class EcoAssistantTests(TestCase):
    def setUp(self):
        self.user = make_user('assistant-user')
        self.action = make_action_type(name='Trajet à vélo', points=15, category='transport', unit='km')

    @override_settings(GEMINI_API_KEY='')
    def test_fallback_recommends_only_an_existing_catalogue_action(self):
        answer, recommendations = ask(self.user, 'Comment utiliser le vélo ?')
        self.assertIn('catalogue', answer)
        self.assertEqual([action.pk for action in recommendations], [self.action.pk])
        self.assertEqual(recommendations[0].points, 15)

    def test_chat_requires_login(self):
        response = self.client.get(reverse('ecoassistant:chat'))
        self.assertEqual(response.status_code, 302)

    @override_settings(GEMINI_API_KEY='')
    def test_chat_is_available_without_an_api_key(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('ecoassistant:chat'), {'question': 'Comment économiser ?'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'service IA est momentanément désactivé')

