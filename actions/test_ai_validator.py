from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from core.exceptions import BusinessRuleError
from core.testing import make_action_type, make_submission, make_user, png_upload

from .ai_validator import validate_submission
from .models import ActionSubmission


class AIEcoValidatorTests(TestCase):
    def setUp(self):
        self.user = make_user('ai-author')
        self.action = make_action_type(name='Recyclage test', points=10)
        self.submission = make_submission(self.user, self.action, evidence=png_upload())

    def test_missing_photo_is_safe_and_does_not_change_status(self):
        self.submission.evidence.delete(save=False)
        self.submission.evidence = ''
        self.submission.save(update_fields=['evidence'])
        with self.assertRaises(BusinessRuleError):
            validate_submission(self.submission)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.PENDING)

    @override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='test-model')
    @patch('google.genai.Client')
    def test_report_is_advisory_and_normalised(self, client_class):
        client = client_class.return_value
        client.models.generate_content.return_value = Mock(text='''{
            "detected_elements": ["bac de tri"],
            "photo_readable": true,
            "consistency_analysis": "Le bac est visible.",
            "confidence_score": 87,
            "recommendation": "supports_claim",
            "evidence_limitations": "La photo ne prouve pas la date."
        }''')
        report = validate_submission(self.submission)
        self.assertEqual(report['confidence_score'], 87)
        self.assertEqual(report['recommendation'], 'supports_claim')
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.PENDING)
        self.assertEqual(self.submission.points_awarded, 0)

