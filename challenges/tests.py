from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from actions.services import approve_submission
from core.exceptions import BusinessRuleError
from core.testing import make_action_type, make_challenge, make_submission, make_superuser, make_team, make_user
from gamification.models import PointTransaction
from notifications.models import Notification

from . import services
from .models import Challenge, ChallengeParticipation


class ChallengeWorkflowTests(TestCase):
    def setUp(self):
        self.creator = make_user('creator')
        self.other = make_user('other')
        self.admin = make_superuser()

    def challenge_data(self, **extra):
        today = timezone.localdate()
        data = {
            'title': 'Une semaine sans voiture', 'category': 'transport', 'difficulty': 'medium',
            'description': 'Laisser la voiture au garage.', 'instructions': 'Étape 1\nÉtape 2',
            'start_date': today.isoformat(), 'end_date': (today + timedelta(days=7)).isoformat(),
            'duration_days': 7, 'required_actions': 3, 'reward_points': 60,
        }
        data.update(extra)
        return data

    def test_created_challenge_is_a_private_draft(self):
        self.client.force_login(self.creator)
        self.client.post(reverse('challenges:create'), self.challenge_data())
        challenge = Challenge.objects.get()
        self.assertEqual(challenge.status, Challenge.Status.DRAFT)
        self.assertEqual(challenge.creator, self.creator)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(challenge.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('challenges:list')), challenge.title)

    def test_form_validates_dates(self):
        self.client.force_login(self.creator)
        today = timezone.localdate()
        response = self.client.post(reverse('challenges:create'), self.challenge_data(
            end_date=(today - timedelta(days=3)).isoformat()))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Challenge.objects.exists())

    def test_only_creator_edits_own_draft(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.DRAFT)
        url = reverse('challenges:update', args=[challenge.slug])
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, self.challenge_data(title='Piraté')).status_code, 403)
        self.client.force_login(self.creator)
        self.client.post(url, self.challenge_data(title='Titre corrigé'))
        challenge.refresh_from_db()
        self.assertEqual(challenge.title, 'Titre corrigé')

    def test_submitted_draft_is_locked_for_creator(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.DRAFT)
        self.client.force_login(self.creator)
        self.client.post(reverse('challenges:submit', args=[challenge.slug]))
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.PENDING)
        self.assertEqual(self.client.get(reverse('challenges:update', args=[challenge.slug])).status_code, 403)
        self.assertTrue(Notification.objects.filter(recipient=self.admin, title='Défi à valider').exists())

    def test_only_the_creator_can_submit_a_draft_and_nothing_is_published(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.DRAFT)
        self.client.force_login(make_user('intruder'))
        self.assertEqual(self.client.post(reverse('challenges:submit', args=[challenge.slug])).status_code, 404)
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.DRAFT)
        self.client.force_login(self.creator)
        response = self.client.post(reverse('challenges:submit', args=[challenge.slug]))
        self.assertRedirects(response, challenge.get_absolute_url(), fetch_redirect_response=False)
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.PENDING)
        self.assertIsNone(challenge.published_at)

    def test_regular_user_cannot_publish(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.PENDING)
        self.client.force_login(self.creator)
        self.assertEqual(self.client.get(reverse('challenges_admin:review_list')).status_code, 403)
        response = self.client.post(reverse('challenges_admin:review_detail', args=[challenge.slug]),
                                    {'decision': 'approve', 'reward_points': 1000})
        self.assertEqual(response.status_code, 403)
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.PENDING)
        with self.assertRaises(BusinessRuleError):
            services.approve_challenge(self.creator, challenge, 50)

    def test_reviewer_publishes_with_validated_points(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.PENDING, reward_points=900)
        self.client.force_login(self.admin)
        self.client.post(reverse('challenges_admin:review_detail', args=[challenge.slug]),
                         {'decision': 'approve', 'reward_points': 120, 'notes': 'Bravo'})
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.ACTIVE)
        self.assertEqual(challenge.reward_points, 120)
        self.assertEqual(challenge.reviewed_by, self.admin)
        self.assertTrue(Notification.objects.filter(recipient=self.other, title='Nouveau défi disponible').exists())

    def test_reward_points_are_capped(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.PENDING)
        self.client.force_login(self.admin)
        self.client.post(reverse('challenges_admin:review_detail', args=[challenge.slug]),
                         {'decision': 'approve', 'reward_points': 5000})
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.PENDING)

    def test_custom_role_with_review_permission_can_publish(self):
        group = Group.objects.create(name='Organisateur de défis')
        group.permissions.add(Permission.objects.get(codename='review_challenge'))
        reviewer = make_user('reviewer')
        reviewer.groups.add(group)
        challenge = make_challenge(self.creator, status=Challenge.Status.PENDING)
        self.client.force_login(reviewer)
        self.assertEqual(self.client.get(reverse('challenges_admin:review_list')).status_code, 200)
        self.client.post(reverse('challenges_admin:review_detail', args=[challenge.slug]),
                         {'decision': 'approve', 'reward_points': 40})
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.ACTIVE)

    def test_reject_requires_notes_and_returns_to_draft(self):
        challenge = make_challenge(self.creator, status=Challenge.Status.PENDING)
        with self.assertRaises(BusinessRuleError):
            services.reject_challenge(self.admin, challenge, '   ')
        services.reject_challenge(self.admin, challenge, 'Précisez les consignes.')
        challenge.refresh_from_db()
        self.assertEqual(challenge.status, Challenge.Status.DRAFT)
        self.assertEqual(challenge.review_notes, 'Précisez les consignes.')

    def test_delete_rules(self):
        draft = make_challenge(self.creator, title='Brouillon', status=Challenge.Status.DRAFT)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('challenges:delete', args=[draft.slug])).status_code, 403)
        self.client.force_login(self.creator)
        self.client.post(reverse('challenges:delete', args=[draft.slug]))
        self.assertFalse(Challenge.objects.filter(pk=draft.pk).exists())
        active = make_challenge(self.creator, title='Actif')
        services.join_challenge(self.other, active)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse('challenges:delete', args=[active.slug])).status_code, 403)


class ParticipationTests(TestCase):
    def setUp(self):
        self.moderator = make_superuser()
        self.user = make_user('runner')
        self.team = make_team(self.user)
        self.challenge = make_challenge(self.moderator, required_actions=2, reward_points=50)
        self.action_type = make_action_type(points=10)

    def test_join_and_duplicate_participation(self):
        self.client.force_login(self.user)
        self.client.post(reverse('challenges:join', args=[self.challenge.slug]))
        participation = ChallengeParticipation.objects.get(challenge=self.challenge, user=self.user)
        self.assertEqual(participation.team, self.team)
        with self.assertRaises(BusinessRuleError):
            services.join_challenge(self.user, self.challenge)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ChallengeParticipation.objects.create(challenge=self.challenge, user=self.user)

    def test_cannot_join_draft_or_ended_challenge(self):
        draft = make_challenge(self.moderator, title='Brouillon', status=Challenge.Status.DRAFT)
        with self.assertRaises(BusinessRuleError):
            services.join_challenge(self.user, draft)
        today = timezone.localdate()
        ended = make_challenge(self.moderator, title='Fini', start_date=today - timedelta(days=20),
                               end_date=today - timedelta(days=1))
        with self.assertRaises(BusinessRuleError):
            services.join_challenge(self.user, ended)

    def test_completion_requires_approved_linked_actions_and_rewards_once(self):
        services.join_challenge(self.user, self.challenge)
        with self.assertRaises(BusinessRuleError):
            services.complete_challenge(self.user, self.challenge)
        first = make_submission(self.user, self.action_type, days_ago=1, challenge=self.challenge)
        second = make_submission(self.user, self.action_type, days_ago=2, challenge=self.challenge)
        approve_submission(self.moderator, first)
        with self.assertRaises(BusinessRuleError):
            services.complete_challenge(self.user, self.challenge)
        approve_submission(self.moderator, second)
        self.client.force_login(self.user)
        self.client.post(reverse('challenges:complete', args=[self.challenge.slug]))
        participation = ChallengeParticipation.objects.get(challenge=self.challenge, user=self.user)
        self.assertEqual(participation.status, ChallengeParticipation.Status.COMPLETED)
        reward = PointTransaction.objects.get(reason=PointTransaction.Reason.CHALLENGE_COMPLETED)
        self.assertEqual((reward.amount, reward.team, reward.challenge), (50, self.team, self.challenge))
        self.client.post(reverse('challenges:complete', args=[self.challenge.slug]))
        with self.assertRaises(BusinessRuleError):
            services.complete_challenge(self.user, self.challenge)
        self.assertEqual(PointTransaction.objects.filter(reason=PointTransaction.Reason.CHALLENGE_COMPLETED).count(), 1)

    def test_pending_actions_do_not_count(self):
        services.join_challenge(self.user, self.challenge)
        make_submission(self.user, self.action_type, days_ago=1, challenge=self.challenge)
        make_submission(self.user, self.action_type, days_ago=2, challenge=self.challenge)
        with self.assertRaises(BusinessRuleError):
            services.complete_challenge(self.user, self.challenge)

    def test_leave_and_rejoin(self):
        services.join_challenge(self.user, self.challenge)
        services.leave_challenge(self.user, self.challenge)
        participation = ChallengeParticipation.objects.get(user=self.user)
        self.assertEqual(participation.status, ChallengeParticipation.Status.ABANDONED)
        services.join_challenge(self.user, self.challenge)
        participation.refresh_from_db()
        self.assertEqual(participation.status, ChallengeParticipation.Status.IN_PROGRESS)
        self.assertEqual(ChallengeParticipation.objects.filter(user=self.user).count(), 1)

    def test_detail_page_shows_progress(self):
        services.join_challenge(self.user, self.challenge)
        self.client.force_login(self.user)
        response = self.client.get(self.challenge.get_absolute_url())
        self.assertContains(response, '0 / 2 actions validées')
