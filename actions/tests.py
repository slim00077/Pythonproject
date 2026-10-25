import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Sum
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from challenges.services import join_challenge
from core.exceptions import BusinessRuleError
from core.testing import (make_action_type, make_challenge, make_submission, make_superuser, make_team, make_user,
                          png_upload)
from gamification.models import PointTransaction
from gamification.services import award_points
from notifications.models import Notification

from . import services
from .models import ActionSubmission, ModerationLog

MEDIA_ROOT = tempfile.mkdtemp(prefix='ecoteams-tests-')


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class SubmissionTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = make_user('author')
        self.other = make_user('other')
        self.bike = make_action_type(points=15, unit='km', co2_factor_kg=Decimal('0.2'), factor_source='Test')

    def data(self, **extra):
        data = {'action_type': self.bike.pk, 'performed_on': timezone.localdate().isoformat(),
                'description': 'Trajet domicile-travail à vélo.', 'quantity': '10'}
        data.update(extra)
        return data

    def test_submission_is_pending_and_awards_no_points(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('actions:create'), self.data())
        submission = ActionSubmission.objects.get()
        self.assertRedirects(response, submission.get_absolute_url())
        self.assertEqual(submission.status, ActionSubmission.Status.PENDING)
        self.assertEqual(submission.points_awarded, 0)
        self.assertFalse(PointTransaction.objects.exists())

    def test_validation_rules(self):
        self.client.force_login(self.user)
        future = (timezone.localdate() + timedelta(days=1)).isoformat()
        too_old = (timezone.localdate() - timedelta(days=90)).isoformat()
        for payload in (self.data(performed_on=future), self.data(performed_on=too_old), self.data(description='')):
            self.assertEqual(self.client.post(reverse('actions:create'), payload).status_code, 200)
        quantity_needed = make_action_type(name='Covoiturage', points=5, requires_quantity=True)
        self.client.post(reverse('actions:create'), self.data(action_type=quantity_needed.pk, quantity=''))
        evidence_needed = make_action_type(name='Réparation', points=20, requires_evidence=True)
        self.client.post(reverse('actions:create'), self.data(action_type=evidence_needed.pk))
        self.assertFalse(ActionSubmission.objects.exists())

    def test_duplicate_same_day_submission_is_rejected(self):
        self.client.force_login(self.user)
        self.client.post(reverse('actions:create'), self.data())
        response = self.client.post(reverse('actions:create'), self.data())
        self.assertContains(response, 'Vous avez déjà déclaré cette action pour cette date.')
        self.assertEqual(ActionSubmission.objects.count(), 1)

    def test_inactive_action_types_cannot_be_used(self):
        self.bike.is_active = False
        self.bike.save()
        self.client.force_login(self.user)
        self.client.post(reverse('actions:create'), self.data())
        self.assertFalse(ActionSubmission.objects.exists())

    def test_challenge_must_be_joined_and_match_category(self):
        challenge = make_challenge(make_superuser(), category='transport')
        water = make_challenge(challenge.creator, title='Eau', category='water')
        self.client.force_login(self.user)
        self.client.post(reverse('actions:create'), self.data(challenge=challenge.pk))
        self.assertFalse(ActionSubmission.objects.exists())  # not a participant
        join_challenge(self.user, challenge)
        join_challenge(self.user, water)
        self.client.post(reverse('actions:create'), self.data(challenge=water.pk))
        self.assertFalse(ActionSubmission.objects.exists())  # category mismatch
        self.client.post(reverse('actions:create'), self.data(challenge=challenge.pk))
        self.assertEqual(ActionSubmission.objects.get().challenge, challenge)

    def test_evidence_upload_and_private_access(self):
        evidence_needed = make_action_type(name='Réparation', points=20, requires_evidence=True)
        self.client.force_login(self.user)
        self.client.post(reverse('actions:create'), self.data(action_type=evidence_needed.pk, evidence=png_upload()))
        submission = ActionSubmission.objects.get()
        self.assertTrue(submission.evidence.name.startswith('evidence/'))
        url = reverse('actions:evidence', args=[submission.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(f'/media/{submission.evidence.name}').status_code, 404)
        self.client.force_login(make_superuser())
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_invalid_uploads_are_rejected(self):
        self.client.force_login(self.user)
        fake = SimpleUploadedFile('script.png', b'not really an image', content_type='image/png')
        self.client.post(reverse('actions:create'), self.data(evidence=fake))
        bad_extension = SimpleUploadedFile('photo.svg', png_upload().read(), content_type='image/svg+xml')
        self.client.post(reverse('actions:create'), self.data(evidence=bad_extension))
        self.assertFalse(ActionSubmission.objects.exists())

    @override_settings(ECOTEAMS_MAX_UPLOAD_MB=0)
    def test_oversized_upload_is_rejected(self):
        self.client.force_login(self.user)
        self.client.post(reverse('actions:create'), self.data(evidence=png_upload()))
        self.assertFalse(ActionSubmission.objects.exists())

    def test_owner_edits_and_deletes_pending_submission_only(self):
        submission = make_submission(self.user, self.bike)
        update_url = reverse('actions:update', args=[submission.pk])
        delete_url = reverse('actions:delete', args=[submission.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('actions:detail', args=[submission.pk])).status_code, 404)
        self.assertEqual(self.client.post(update_url, self.data(description='piraté')).status_code, 404)
        self.assertEqual(self.client.post(delete_url).status_code, 404)
        self.client.force_login(self.user)
        self.client.post(update_url, self.data(performed_on=submission.performed_on.isoformat(), description='Corrigée'))
        submission.refresh_from_db()
        self.assertEqual(submission.description, 'Corrigée')
        self.client.post(delete_url)
        self.assertFalse(ActionSubmission.objects.filter(pk=submission.pk).exists())

    def test_approved_submission_is_protected(self):
        submission = make_submission(self.user, self.bike, quantity=Decimal('5'))
        services.approve_submission(make_superuser(), submission)
        self.client.force_login(self.user)
        self.client.post(reverse('actions:update', args=[submission.pk]), self.data(description='Modifiée'))
        self.client.post(reverse('actions:delete', args=[submission.pk]))
        submission.refresh_from_db()
        self.assertEqual(submission.status, ActionSubmission.Status.APPROVED)
        self.assertNotEqual(submission.description, 'Modifiée')


class ModerationTests(TestCase):
    def setUp(self):
        self.moderator = make_superuser('moderator')
        self.user = make_user('author')
        self.team = make_team(self.user)
        self.bike = make_action_type(points=15, unit='km', co2_factor_kg=Decimal('0.2'), factor_source='Test')
        self.submission = make_submission(self.user, self.bike, quantity=Decimal('10'))

    def test_regular_user_cannot_moderate(self):
        intruder = make_user('intruder')
        self.client.force_login(intruder)
        self.assertEqual(self.client.get(reverse('actions_admin:moderation_list')).status_code, 403)
        response = self.client.post(reverse('actions_admin:moderation_detail', args=[self.submission.pk]),
                                    {'decision': 'approve'})
        self.assertEqual(response.status_code, 403)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.PENDING)
        self.assertFalse(PointTransaction.objects.exists())
        with self.assertRaises(BusinessRuleError):
            services.approve_submission(intruder, self.submission)

    def test_approval_awards_fixed_points_to_user_and_team(self):
        self.client.force_login(self.moderator)
        self.client.post(reverse('actions_admin:moderation_detail', args=[self.submission.pk]),
                         {'decision': 'approve', 'notes': 'OK'})
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.APPROVED)
        self.assertEqual(self.submission.points_awarded, 15)
        self.assertEqual(self.submission.co2_saved_kg, Decimal('2.000'))
        self.assertEqual(self.submission.team, self.team)
        entry = PointTransaction.objects.get()
        self.assertEqual((entry.user, entry.team, entry.amount, entry.reference),
                         (self.user, self.team, 15, f'action:{self.submission.pk}'))
        self.assertEqual(ModerationLog.objects.get().decision, ModerationLog.Decision.APPROVED)
        self.assertTrue(Notification.objects.filter(recipient=self.user, title='Action validée').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user, kind='points').exists())

    def test_points_are_never_awarded_twice(self):
        services.approve_submission(self.moderator, self.submission)
        with self.assertRaises(BusinessRuleError):
            services.approve_submission(self.moderator, self.submission)
        self.client.force_login(self.moderator)
        self.client.post(reverse('actions_admin:moderation_detail', args=[self.submission.pk]), {'decision': 'approve'})
        self.assertIsNone(award_points(user=self.user, amount=15, reason='action_approved',
                                       reference=f'action:{self.submission.pk}', description='retry'))
        self.assertEqual(PointTransaction.objects.count(), 1)

    def test_moderator_cannot_moderate_own_submission(self):
        own = make_submission(self.moderator, self.bike, days_ago=2)
        with self.assertRaises(BusinessRuleError):
            services.approve_submission(self.moderator, own)

    def test_rejection_requires_reason_and_awards_nothing(self):
        with self.assertRaises(BusinessRuleError):
            services.reject_submission(self.moderator, self.submission, '')
        services.reject_submission(self.moderator, self.submission, 'Preuve insuffisante')
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.REJECTED)
        self.assertEqual(self.submission.moderation_notes, 'Preuve insuffisante')
        self.assertFalse(PointTransaction.objects.exists())

    def test_revocation_is_audited_with_a_reversing_entry(self):
        services.approve_submission(self.moderator, self.submission)
        services.revoke_approval(self.moderator, self.submission, 'Doublon détecté')
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.REJECTED)
        self.assertEqual(PointTransaction.objects.count(), 2)
        self.assertEqual(PointTransaction.objects.aggregate(total=Sum('amount'))['total'], 0)
        self.assertEqual(PointTransaction.objects.get(amount=-15).team, self.team)
        self.assertEqual(ModerationLog.objects.filter(decision=ModerationLog.Decision.REVOKED).count(), 1)
        with self.assertRaises(BusinessRuleError):
            services.revoke_approval(self.moderator, self.submission, 'encore')

    def test_custom_moderator_role_can_moderate(self):
        group = Group.objects.create(name='Modérateur')
        group.permissions.add(Permission.objects.get(codename='moderate_actionsubmission'))
        moderator = make_user('custom-mod')
        moderator.groups.add(group)
        self.client.force_login(moderator)
        self.assertEqual(self.client.get(reverse('actions_admin:moderation_list')).status_code, 200)
        self.client.post(reverse('actions_admin:moderation_detail', args=[self.submission.pk]), {'decision': 'approve'})
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ActionSubmission.Status.APPROVED)
        self.assertEqual(self.client.get(reverse('accounts:role_list')).status_code, 403)

    def test_catalogue_management_is_restricted(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('actions_admin:type_list')).status_code, 403)
        response = self.client.post(reverse('actions_admin:type_update', args=[self.bike.pk]),
                                    {'name': 'Vélo', 'category': 'transport', 'description': 'x', 'points': 500})
        self.assertEqual(response.status_code, 403)
        self.bike.refresh_from_db()
        self.assertEqual(self.bike.points, 15)

    def test_co2_factor_requires_documented_source(self):
        self.client.force_login(self.moderator)
        response = self.client.post(reverse('actions_admin:type_create'), {
            'name': 'Nouvelle action', 'category': 'energy', 'description': 'x', 'points': 5,
            'co2_factor_kg': '0.5', 'unit': 'kWh', 'factor_source': '', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documentez la source du facteur CO₂.')
