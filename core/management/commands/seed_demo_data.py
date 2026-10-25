"""Populate EcoTeams with clearly labelled demonstration data.

The command is idempotent: objects are looked up by natural keys and every
point is awarded through the central scoring service, whose unique ledger
references make a second run harmless. ``--reset`` removes the demo data.
"""
import os
import random
import secrets
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Role, User
from actions.models import ActionSubmission, EcoActionType, ModerationLog
from actions.services import approve_submission, reject_submission
from analytics.models import ActivityLog
from challenges.models import Challenge, ChallengeParticipation
from challenges.services import approve_challenge, complete_challenge, join_challenge, participation_progress
from community.models import Event, EventParticipation
from community.services import join_event, publish_event
from core.choices import Audience, EcoCategory
from core.exceptions import BusinessRuleError
from gamification.models import Badge, PointTransaction
from goals.models import Goal
from goals.services import refresh_auto_goals
from notifications.models import Notification
from teams.models import Membership, Team

DEMO_PREFIX = 'demo_'
DEMO_FACTOR_SOURCE = (
    'Valeur indicative de démonstration — à remplacer par une valeur sourcée '
    '(ex. Base Empreinte® de l’ADEME ou facteur national) avant tout usage réel.'
)

ACTION_TYPES = [
    # name, category, points, unit, co2 factor, evidence, quantity, description, instructions
    ('Trajet à vélo ou à pied', EcoCategory.TRANSPORT, 15, 'km', '0.190', False, True,
     'Remplacer un trajet en voiture par le vélo, la trottinette ou la marche.',
     'Indiquez la distance parcourue et le trajet effectué.'),
    ('Transports en commun plutôt que la voiture', EcoCategory.TRANSPORT, 10, 'km', '0.120', False, True,
     'Prendre le bus, le métro, le train ou le tramway au lieu de la voiture individuelle.',
     'Précisez la ligne ou le trajet.'),
    ('Covoiturage', EcoCategory.TRANSPORT, 8, 'km', '0.090', False, True,
     'Partager un trajet en voiture avec au moins une autre personne.', ''),
    ('Tri sélectif des déchets', EcoCategory.RECYCLING, 10, 'kg', None, False, False,
     'Trier correctement les emballages, le verre et le papier du foyer ou du bureau.',
     'Décrivez les flux triés. Une photo des bacs est appréciée.'),
    ('Réparer au lieu de jeter', EcoCategory.CONSUMPTION, 20, '', None, True, False,
     'Faire réparer ou réparer soi-même un objet plutôt que d’en racheter un neuf.',
     'Photo de l’objet réparé obligatoire.'),
    ('Gourde et contenants réutilisables', EcoCategory.CONSUMPTION, 5, '', None, False, False,
     'Éviter les bouteilles et emballages jetables grâce à des contenants réutilisables.', ''),
    ('Éteindre les appareils en veille', EcoCategory.ENERGY, 8, 'kWh', '0.450', False, False,
     'Couper multiprises et appareils en veille (maison, salle de cours, bureau).',
     'Estimez l’énergie économisée si possible.'),
    ('Lessive à basse température', EcoCategory.ENERGY, 6, '', None, False, False,
     'Laver son linge à 30 °C ou moins, à pleine charge.', ''),
    ('Douche de moins de 5 minutes', EcoCategory.WATER, 6, '', None, False, False,
     'Limiter la durée de la douche pour économiser l’eau et l’énergie de chauffage.', ''),
    ('Récupération d’eau de pluie', EcoCategory.WATER, 12, 'L', None, True, True,
     'Récupérer l’eau de pluie pour l’arrosage ou le nettoyage.', 'Photo du dispositif obligatoire.'),
    ('Repas végétarien', EcoCategory.FOOD, 8, 'repas', '1.500', False, True,
     'Choisir un repas végétarien à la place d’un repas avec viande.', ''),
    ('Lutte contre le gaspillage alimentaire', EcoCategory.FOOD, 10, '', None, False, False,
     'Cuisiner les restes, donner les invendus, planifier ses courses.', ''),
]

BADGES = [
    ('Premier geste vert', 'Valider sa toute première action écologique.', 'sprout', 'lime', Badge.Rule.ACTIONS_TOTAL, '', 1),
    ('Éco-débutant', 'Atteindre 50 points au registre.', 'leaf', 'emerald', Badge.Rule.POINTS_TOTAL, '', 50),
    ('Héros du recyclage', 'Valider 5 actions de recyclage.', 'recycle', 'emerald', Badge.Rule.CATEGORY_ACTIONS, EcoCategory.RECYCLING, 5),
    ('Cycliste urbain', 'Valider 5 actions de mobilité durable.', 'bike', 'cyan', Badge.Rule.CATEGORY_ACTIONS, EcoCategory.TRANSPORT, 5),
    ('Économe en énergie', 'Valider 5 actions d’économie d’énergie.', 'zap', 'lime', Badge.Rule.CATEGORY_ACTIONS, EcoCategory.ENERGY, 5),
    ('Série de 7 jours', 'Valider une action 7 jours consécutifs.', 'flame', 'gold', Badge.Rule.STREAK_DAYS, '', 7),
    ('Défi relevé', 'Réussir un premier défi écologique.', 'target', 'cyan', Badge.Rule.CHALLENGES_COMPLETED, '', 1),
    ('Objectif atteint', 'Atteindre un objectif personnel.', 'star', 'lime', Badge.Rule.GOALS_COMPLETED, '', 1),
    ('Citoyen engagé', 'S’inscrire à 2 événements de la communauté.', 'users', 'cyan', Badge.Rule.EVENTS_JOINED, '', 2),
    ('Champion d’équipe', 'Appartenir à l’équipe classée 1re.', 'crown', 'gold', Badge.Rule.TEAM_RANK, '', 1),
    ('Leader de l’action climat', 'Atteindre 500 points au registre.', 'trophy', 'gold', Badge.Rule.POINTS_TOTAL, '', 500),
]

USERS = [
    # username, first, last, organization type, organization, city, favourite category
    ('demo_amina', 'Amina', 'Ben Salah', 'student', 'Université (démo)', 'Tunis', EcoCategory.TRANSPORT),
    ('demo_youssef', 'Youssef', 'Trabelsi', 'student', 'Université (démo)', 'Ariana', EcoCategory.FOOD),
    ('demo_nour', 'Nour', 'Belhadj', 'student', 'Université (démo)', 'Tunis', EcoCategory.WATER),
    ('demo_lina', 'Lina', 'Haddad', 'employee', 'Entreprise (démo)', 'Sousse', EcoCategory.RECYCLING),
    ('demo_karim', 'Karim', 'Jaziri', 'employee', 'Entreprise (démo)', 'Sousse', EcoCategory.CONSUMPTION),
    ('demo_sarra', 'Sarra', 'Mansour', 'association', 'Association (démo)', 'Sfax', EcoCategory.ENERGY),
    ('demo_mehdi', 'Mehdi', 'Gharbi', 'student', 'Université (démo)', 'Sfax', EcoCategory.ENERGY),
    ('demo_ines', 'Inès', 'Chaabane', 'employee', 'Entreprise (démo)', 'Bizerte', EcoCategory.WATER),
    ('demo_omar', 'Omar', 'Ferchichi', 'association', 'Association (démo)', 'Nabeul', EcoCategory.WATER),
    ('demo_moderateur', 'Salma', 'Ayari', 'other', 'Équipe EcoTeams (démo)', 'Tunis', ''),
]

TEAMS = [
    # name, captain, members, focus, motto, description, goal
    ('Les Pédaleurs Verts', 'demo_amina', ['demo_youssef', 'demo_nour'], EcoCategory.TRANSPORT,
     'Chaque coup de pédale compte.', 'Équipe de démonstration d’étudiants qui privilégient le vélo et les transports en commun.', 600),
    ('Zéro Déchet Squad', 'demo_lina', ['demo_karim'], EcoCategory.RECYCLING,
     'Moins jeter, mieux trier.', 'Équipe de démonstration de salariés engagés dans le tri, la réparation et le réemploi.', 500),
    ('Watt Watchers', 'demo_sarra', ['demo_mehdi', 'demo_ines'], EcoCategory.ENERGY,
     'Le meilleur kWh est celui qu’on ne consomme pas.', 'Équipe associative de démonstration qui traque le gaspillage d’énergie.', None),
    ('Gouttes d’Avenir', 'demo_omar', [], EcoCategory.WATER,
     'Préserver chaque goutte.', 'Équipe de démonstration dédiée aux économies d’eau.', None),
    ('Consom’Acteurs', 'demo_moderateur', [], EcoCategory.CONSUMPTION,
     'Consommer moins, consommer mieux.', 'Équipe de démonstration qui promeut le réemploi et la consommation responsable.', 400),
]

# username -> list of (action type index, days ago, quantity, challenge key or None)
SUBMISSIONS = {
    'demo_amina': [(0, d, 6 + d % 4, 'velo') for d in range(1, 9)] + [(1, 10, 12, None), (1, 12, 9, None)],
    'demo_youssef': [(0, 3, 5, 'velo'), (0, 4, 7, 'velo'), (0, 6, 4, 'velo'), (10, 5, 1, None), (11, 9, None, None)],
    'demo_nour': [(1, 2, 15, None), (1, 5, 11, None), (8, 3, None, 'douche'), (8, 4, None, 'douche'), (10, 7, 2, None)],
    'demo_lina': [(3, d, 3, 'tri') for d in (1, 2, 4, 6, 8, 11)] + [(4, 7, None, None), (5, 3, None, None)],
    'demo_karim': [(3, 2, 2, 'tri'), (3, 5, 4, 'tri'), (6, 6, 3, None), (5, 9, None, None)],
    'demo_sarra': [(6, d, 2 + d % 3, 'energie') for d in (1, 2, 3, 5, 7)] + [(7, 4, None, None), (7, 9, None, None)],
    'demo_mehdi': [(6, 2, 1.5, 'energie'), (6, 4, 2, 'energie'), (2, 6, 18, None)],
    'demo_ines': [(8, 1, None, 'douche'), (8, 2, None, 'douche'), (8, 3, None, 'douche'), (6, 5, 1, None)],
    'demo_omar': [(8, d, None, 'douche') for d in (1, 2, 3, 4, 5, 6)] + [(9, 8, 120, None)],
}
PENDING = [
    ('demo_amina', 1, 0, 8, 'Trajet en bus jusqu’au campus ce matin (démo, en attente).'),
    ('demo_karim', 3, 0, 3, 'Tri des emballages de la cafétéria (démo, en attente).'),
    ('demo_mehdi', 6, 1, 2, 'Extinction des écrans de la salle informatique (démo, en attente).'),
    ('demo_ines', 11, 1, None, 'Préparation d’un repas avec les restes de la veille (démo, en attente).'),
]
REJECTED = [('demo_youssef', 4, 2, None, 'Réparation déclarée sans photo (démo).', 'La photo justificative est obligatoire pour cette action.')]

DESCRIPTIONS = {
    0: 'Trajet domicile – campus à vélo au lieu de la voiture (démo).',
    1: 'Trajet en métro léger plutôt qu’en voiture (démo).',
    2: 'Covoiturage avec deux collègues pour aller au travail (démo).',
    3: 'Tri des emballages et du verre de la semaine (démo).',
    4: 'Réparation d’une lampe de bureau au repair café (démo).',
    5: 'Gourde et boîte réutilisable pour le déjeuner (démo).',
    6: 'Extinction des multiprises et des appareils en veille (démo).',
    7: 'Lessive à 30 °C à pleine charge (démo).',
    8: 'Douche chronométrée de 4 minutes (démo).',
    9: 'Récupération d’eau de pluie pour arroser le potager (démo).',
    10: 'Déjeuner végétarien au restaurant universitaire (démo).',
    11: 'Soupe préparée avec les légumes restants (démo).',
}


class Command(BaseCommand):
    help = 'Crée des données de démonstration clairement identifiées (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--password', help='Mot de passe des comptes de démonstration (sinon DEMO_USER_PASSWORD).')
        parser.add_argument('--reset', action='store_true', help='Supprime les données de démonstration puis les recrée.')
        parser.add_argument('--force', action='store_true', help='Autorise l’exécution lorsque DJANGO_DEBUG=False.')

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['force']:
            raise CommandError('Données de démonstration refusées hors mode développement (utilisez --force si nécessaire).')
        self.rng = random.Random(2026)
        self.today = timezone.localdate()
        password = options['password'] or os.environ.get('DEMO_USER_PASSWORD', '')
        generated = not password
        if generated:
            password = secrets.token_urlsafe(9)
        if options['reset']:
            self.reset()
        with transaction.atomic():
            self.action_types = self.seed_action_types()
            self.seed_badges()
            self.users, created_users = self.seed_users(password)
            self.moderator = self.users['demo_moderateur']
            self.seed_moderator_role()
            self.seed_teams()
            self.challenges = self.seed_challenges()
            self.seed_submissions()
            self.complete_ready_challenges()
            self.seed_goals()
            self.seed_events()
            self.tidy_notifications()
        self.stdout.write(self.style.SUCCESS('Données de démonstration prêtes.'))
        self.stdout.write(f'  Comptes : {", ".join(self.users)}')
        if created_users:
            label = 'généré automatiquement' if generated else 'fourni'
            self.stdout.write(f'  Mot de passe ({label}) des nouveaux comptes : {password}')
        else:
            self.stdout.write('  Les comptes existaient déjà : leur mot de passe n’a pas été modifié.')
        self.stdout.write('  « demo_moderateur » possède le rôle Modérateur. Créez l’administrateur avec createsuperuser.')

    # --- helpers -------------------------------------------------------------

    def at(self, days_ago, hour=18):
        day = self.today - timedelta(days=days_ago)
        return timezone.make_aware(datetime.combine(day, time(hour, self.rng.randint(0, 59))))

    def reset(self):
        demo_users = User.objects.filter(username__startswith=DEMO_PREFIX)
        Team.objects.filter(captain__in=demo_users).delete()
        Challenge.objects.filter(creator__in=demo_users).delete()
        Event.objects.filter(organizer__in=demo_users).delete()
        deleted, _ = demo_users.delete()
        Group.objects.filter(name='Modérateur', role__is_system=False).delete()
        self.stdout.write(self.style.WARNING(f'Données de démonstration supprimées ({deleted} objets).'))

    # --- catalogue -----------------------------------------------------------

    def seed_action_types(self):
        types = []
        for name, category, points, unit, factor, evidence, quantity, description, instructions in ACTION_TYPES:
            action_type, _ = EcoActionType.objects.get_or_create(name=name, defaults={
                'category': category, 'points': points, 'unit': unit,
                'co2_factor_kg': Decimal(factor) if factor else None,
                'factor_source': DEMO_FACTOR_SOURCE if factor else '',
                'requires_evidence': evidence, 'requires_quantity': quantity,
                'description': description, 'instructions': instructions,
            })
            types.append(action_type)
        return types

    def seed_badges(self):
        for name, description, icon, tone, rule, category, threshold in BADGES:
            Badge.objects.get_or_create(name=name, defaults={
                'description': description, 'icon': icon, 'tone': tone, 'rule': rule,
                'category': category, 'threshold': threshold,
            })

    # --- people and teams ----------------------------------------------------

    def seed_users(self, password):
        users, created_any = {}, False
        for username, first, last, org_type, org, city, favourite in USERS:
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username, email=f'{username}@demo.ecoteams.local', password=password,
                    first_name=first, last_name=last, organization_type=org_type, organization=org, city=city,
                    favorite_category=favourite, bio='Compte de démonstration EcoTeams — données fictives.',
                )
                User.objects.filter(pk=user.pk).update(date_joined=timezone.now() - timedelta(days=self.rng.randint(20, 50)))
                created_any = True
            users[username] = user
        return users, created_any

    def seed_moderator_role(self):
        group, _ = Group.objects.get_or_create(name='Modérateur')
        Role.objects.get_or_create(group=group, defaults={
            'description': 'Rôle de démonstration : modère les actions, valide défis et événements, consulte les rapports.',
        })
        codenames = [('actions', 'moderate_actionsubmission'), ('challenges', 'review_challenge'),
                     ('community', 'review_event'), ('analytics', 'view_reports')]
        for app_label, codename in codenames:
            group.permissions.add(Permission.objects.get(content_type__app_label=app_label, codename=codename))
        self.moderator.groups.add(group)

    def seed_teams(self):
        for name, captain, members, focus, motto, description, goal in TEAMS:
            team = Team.objects.filter(name=name).first()
            if team is None:
                team = Team.objects.create(
                    name=name, captain=self.users[captain], focus_area=focus, motto=motto,
                    description=description, goal_points=goal, max_members=6,
                )
                Team.objects.filter(pk=team.pk).update(created_at=self.at(30, 10))
                ActivityLog.objects.create(actor=self.users[captain], team=team, verb=ActivityLog.Verb.TEAM_CREATED,
                                           description=f'{self.users[captain].display_name} a créé l’équipe « {name} ».',
                                           link=team.get_absolute_url(), created_at=self.at(30, 10))
            Membership.objects.get_or_create(user=self.users[captain], defaults={
                'team': team, 'role': Membership.Role.CAPTAIN, 'joined_at': self.at(30, 10)})
            for offset, username in enumerate(members):
                _, created = Membership.objects.get_or_create(user=self.users[username], defaults={
                    'team': team, 'joined_at': self.at(28 - offset, 12)})
                if created:
                    ActivityLog.objects.create(actor=self.users[username], team=team, verb=ActivityLog.Verb.TEAM_JOINED,
                                               description=f'{self.users[username].display_name} a rejoint l’équipe « {name} ».',
                                               link=team.get_absolute_url(), created_at=self.at(28 - offset, 12))

    # --- challenges ------------------------------------------------------------

    def _challenge(self, key, title, category, difficulty, start, end, required, points, creator, description, steps,
                   status):
        challenge = Challenge.objects.filter(title=title).first()
        if challenge is not None:
            return challenge
        challenge = Challenge.objects.create(
            title=title, category=category, difficulty=difficulty, description=description, instructions=steps,
            start_date=self.today + timedelta(days=start), end_date=self.today + timedelta(days=end),
            duration_days=min(30, end - start + 1), required_actions=required, reward_points=points,
            creator=self.users[creator], status=Challenge.Status.DRAFT,
        )
        if status == Challenge.Status.ACTIVE:
            challenge.status = Challenge.Status.PENDING
            challenge.save(update_fields=['status'])
            approve_challenge(self.moderator, challenge, points, 'Défi de démonstration validé.')
            challenge.refresh_from_db()
        elif status != Challenge.Status.DRAFT:
            Challenge.objects.filter(pk=challenge.pk).update(status=status, reviewed_by=self.moderator)
            challenge.refresh_from_db()
        return challenge

    def seed_challenges(self):
        c = {}
        c['velo'] = self._challenge(
            'velo', 'Mois du vélo', EcoCategory.TRANSPORT, Challenge.Difficulty.MEDIUM, -20, 10, 3, 80, 'demo_moderateur',
            'Pendant un mois, remplacez au moins trois trajets en voiture par le vélo ou la marche.',
            'Vérifiez votre vélo et votre éclairage\nRepérez un itinéraire sécurisé\nDéclarez chaque trajet en le liant au défi',
            Challenge.Status.ACTIVE)
        c['tri'] = self._challenge(
            'tri', 'Tri sélectif au quotidien', EcoCategory.RECYCLING, Challenge.Difficulty.EASY, -15, 15, 4, 100, 'demo_lina',
            'Installez un tri efficace chez vous ou au bureau et tenez-le pendant deux semaines.',
            'Identifiez les consignes de tri de votre commune\nÉquipez-vous de bacs séparés\nDéclarez vos actions de tri',
            Challenge.Status.ACTIVE)
        c['energie'] = self._challenge(
            'energie', 'Chasse au gaspillage énergétique', EcoCategory.ENERGY, Challenge.Difficulty.MEDIUM, -10, 20, 3, 90,
            'demo_sarra', 'Traquez les veilles inutiles et réduisez la consommation électrique de votre lieu de vie.',
            'Listez les appareils en veille\nInstallez des multiprises à interrupteur\nCoupez-les chaque soir et déclarez-le',
            Challenge.Status.ACTIVE)
        c['douche'] = self._challenge(
            'douche', 'Douches express', EcoCategory.WATER, Challenge.Difficulty.EASY, -7, 23, 5, 70, 'demo_omar',
            'Limitez vos douches à moins de cinq minutes pendant un mois.',
            'Utilisez un minuteur\nCoupez l’eau pendant le savonnage\nDéclarez vos douches courtes',
            Challenge.Status.ACTIVE)
        c['gaspillage'] = self._challenge(
            'gaspillage', 'Zéro gaspillage alimentaire', EcoCategory.FOOD, Challenge.Difficulty.HARD, 2, 32, 6, 120,
            'demo_youssef', 'Un mois sans jeter de nourriture : planification, restes cuisinés, dons.',
            'Planifiez vos repas\nCuisinez les restes\nDonnez ce que vous ne consommerez pas', Challenge.Status.PENDING)
        c['local'] = self._challenge(
            'local', 'Consommer local', EcoCategory.CONSUMPTION, Challenge.Difficulty.EASY, 5, 35, 3, 60, 'demo_karim',
            'Privilégier les produits locaux et de saison pendant un mois.',
            'Repérez les marchés de producteurs\nAchetez de saison', Challenge.Status.DRAFT)
        c['printemps'] = self._challenge(
            'printemps', 'Printemps propre', EcoCategory.RECYCLING, Challenge.Difficulty.MEDIUM, -90, -60, 2, 50,
            'demo_moderateur', 'Défi terminé de démonstration : opération de collecte de déchets.',
            'Rejoignez une collecte\nTriez les déchets ramassés', Challenge.Status.COMPLETED)
        c['covoiturage'] = self._challenge(
            'covoiturage', 'Semaine du covoiturage', EcoCategory.TRANSPORT, Challenge.Difficulty.EASY, -5, 25, 3, 55,
            'demo_youssef', 'Partagez vos trajets en voiture au moins trois fois sur la période.',
            'Trouvez un partenaire de trajet\nOrganisez les horaires\nDéclarez chaque trajet partagé',
            Challenge.Status.ACTIVE)
        c['reemploi'] = self._challenge(
            'reemploi', 'Objets qui durent', EcoCategory.CONSUMPTION, Challenge.Difficulty.MEDIUM, 0, 30, 2, 65,
            'demo_moderateur', 'Réparez ou donnez une seconde vie à au moins deux objets au lieu de les jeter.',
            'Identifiez un objet abîmé\nRéparez-le ou faites-le réparer\nDéclarez chaque réparation',
            Challenge.Status.PENDING)
        c['potager'] = self._challenge(
            'potager', 'Potager partagé', EcoCategory.FOOD, Challenge.Difficulty.HARD, -40, -10, 4, 110,
            'demo_sarra', 'Défi terminé de démonstration : entretien collectif d’un potager urbain.',
            'Préparez les parcelles\nPlantez et arrosez\nRécoltez et partagez', Challenge.Status.COMPLETED)
        for challenge in c.values():
            if challenge.status == Challenge.Status.ACTIVE:
                Challenge.objects.filter(pk=challenge.pk).update(published_at=self.at(abs((challenge.start_date - self.today).days), 9))
        participants = {
            'velo': ['demo_amina', 'demo_youssef', 'demo_nour', 'demo_mehdi'],
            'tri': ['demo_lina', 'demo_karim', 'demo_youssef'],
            'energie': ['demo_sarra', 'demo_mehdi', 'demo_ines'],
            'douche': ['demo_omar', 'demo_ines', 'demo_nour'],
            'covoiturage': ['demo_youssef', 'demo_karim'],
        }
        for key, usernames in participants.items():
            for username in usernames:
                if not ChallengeParticipation.objects.filter(challenge=c[key], user=self.users[username]).exists():
                    join_challenge(self.users[username], c[key])
                    ChallengeParticipation.objects.filter(challenge=c[key], user=self.users[username]).update(
                        joined_at=self.at(min(19, abs((c[key].start_date - self.today).days)), 8))
        return c

    # --- submissions -----------------------------------------------------------

    def _submission(self, username, type_index, days_ago, quantity, description, challenge=None):
        user = self.users[username]
        action_type = self.action_types[type_index]
        day = self.today - timedelta(days=days_ago)
        existing = ActionSubmission.objects.filter(user=user, action_type=action_type, performed_on=day).first()
        if existing:
            return existing, False
        submission = ActionSubmission.objects.create(
            user=user, action_type=action_type, performed_on=day, description=description,
            quantity=Decimal(str(quantity)) if quantity else None, challenge=challenge,
        )
        ActivityLog.objects.create(actor=user, verb=ActivityLog.Verb.ACTION_SUBMITTED,
                                   team=user.memberships.first().team if user.memberships.exists() else None,
                                   description=f'{user.display_name} a déclaré l’action « {action_type.name} ».',
                                   link=submission.get_absolute_url(), created_at=self.at(days_ago, 17))
        return submission, True

    def _backdate_approval(self, submission, days_ago):
        moment = self.at(max(0, days_ago - 1), 10)
        ActionSubmission.objects.filter(pk=submission.pk).update(reviewed_at=moment)
        PointTransaction.objects.filter(reference=f'action:{submission.pk}').update(created_at=moment)
        ModerationLog.objects.filter(submission=submission).update(created_at=moment)
        ActivityLog.objects.filter(verb=ActivityLog.Verb.ACTION_APPROVED, link=submission.get_absolute_url()).update(created_at=moment)
        Notification.objects.filter(link=submission.get_absolute_url()).update(created_at=moment)

    def seed_submissions(self):
        plan = sorted(
            ((username, *entry) for username, entries in SUBMISSIONS.items() for entry in entries),
            key=lambda row: -row[2],
        )
        for username, type_index, days_ago, quantity, challenge_key in plan:
            challenge = self.challenges.get(challenge_key) if challenge_key else None
            submission, created = self._submission(username, type_index, days_ago, quantity,
                                                   DESCRIPTIONS[type_index], challenge)
            if created and submission.status == ActionSubmission.Status.PENDING:
                approve_submission(self.moderator, submission, 'Validé (démonstration).')
                self._backdate_approval(submission, days_ago)
        for username, type_index, days_ago, quantity, description in PENDING:
            self._submission(username, type_index, days_ago, quantity, description)
        for username, type_index, days_ago, quantity, description, reason in REJECTED:
            submission, created = self._submission(username, type_index, days_ago, quantity, description)
            if created:
                reject_submission(self.moderator, submission, reason)

    def complete_ready_challenges(self):
        participations = ChallengeParticipation.objects.filter(
            status=ChallengeParticipation.Status.IN_PROGRESS, user__username__startswith=DEMO_PREFIX,
        ).select_related('challenge', 'user')
        for participation in participations:
            if participation_progress(participation)['ready']:
                complete_challenge(participation.user, participation.challenge)
                moment = self.at(1, 20)
                ChallengeParticipation.objects.filter(pk=participation.pk).update(completed_at=moment)
                PointTransaction.objects.filter(
                    reference=f'challenge:{participation.challenge_id}:user:{participation.user_id}'
                ).update(created_at=moment)

    # --- goals and events ----------------------------------------------------------

    def seed_goals(self):
        goals = [
            # username, title, category, mode, target, start offset, end offset, unit
            ('demo_amina', '15 trajets à vélo ce mois-ci', EcoCategory.TRANSPORT, Goal.TrackingMode.ACTIONS, 15, -20, 10, 'actions'),
            ('demo_amina', 'Atteindre 200 points', '', Goal.TrackingMode.POINTS, 200, -25, 20, 'points'),
            ('demo_lina', 'Trier chaque semaine', EcoCategory.RECYCLING, Goal.TrackingMode.ACTIONS, 6, -20, 10, 'actions'),
            ('demo_sarra', 'Réduire les veilles à zéro', EcoCategory.ENERGY, Goal.TrackingMode.ACTIONS, 8, -15, 15, 'actions'),
            ('demo_omar', 'Économiser 1 000 litres d’eau', EcoCategory.WATER, Goal.TrackingMode.MANUAL, 1000, -10, 20, 'litres'),
            ('demo_youssef', 'Cuisiner 5 repas anti-gaspi', EcoCategory.FOOD, Goal.TrackingMode.MANUAL, 5, -5, 25, 'repas'),
            ('demo_nour', 'Prendre les transports en commun 10 fois', EcoCategory.TRANSPORT, Goal.TrackingMode.ACTIONS, 10, -12, 18, 'actions'),
            ('demo_karim', 'Trier 5 fois ce mois-ci', EcoCategory.RECYCLING, Goal.TrackingMode.ACTIONS, 5, -18, 12, 'actions'),
            ('demo_mehdi', 'Atteindre 150 points', '', Goal.TrackingMode.POINTS, 150, -20, 15, 'points'),
            ('demo_ines', 'Douches courtes 8 fois', EcoCategory.WATER, Goal.TrackingMode.ACTIONS, 8, -14, 14, 'actions'),
            ('demo_youssef', 'Covoiturer 3 fois', EcoCategory.TRANSPORT, Goal.TrackingMode.ACTIONS, 3, -8, 22, 'actions'),
            ('demo_karim', 'Réparer 2 objets au lieu de jeter', EcoCategory.CONSUMPTION, Goal.TrackingMode.MANUAL, 2, -5, 25, 'objets'),
            ('demo_sarra', 'Atteindre 300 points', '', Goal.TrackingMode.POINTS, 300, -22, 18, 'points'),
            ('demo_moderateur', 'Donner une seconde vie à 2 objets', EcoCategory.CONSUMPTION, Goal.TrackingMode.MANUAL, 2, -10, 20, 'objets'),
            ('demo_omar', 'Prendre les transports en commun 6 fois', EcoCategory.TRANSPORT, Goal.TrackingMode.ACTIONS, 6, -9, 16, 'actions'),
        ]
        for username, title, category, mode, target, start, end, unit in goals:
            user = self.users[username]
            goal, created = Goal.objects.get_or_create(user=user, title=title, defaults={
                'category': category, 'tracking_mode': mode, 'target_value': target, 'unit': unit,
                'start_date': self.today + timedelta(days=start), 'deadline': self.today + timedelta(days=end),
                'current_progress': 420 if 'litres' in title else (2 if mode == Goal.TrackingMode.MANUAL else 0),
                'description': 'Objectif de démonstration.',
            })
            if created:
                ActivityLog.objects.create(actor=user, verb=ActivityLog.Verb.GOAL_CREATED,
                                           description=f'{user.display_name} s’est fixé l’objectif « {title} ».',
                                           link=goal.get_absolute_url(), created_at=self.at(abs(start), 9))
            refresh_auto_goals(user)

    def _event(self, title, kind, category, fmt, location, url, start_days, start_hour, duration_hours, organizer,
               audience, capacity, goal, status, description):
        event = Event.objects.filter(title=title).first()
        if event is not None:
            return event
        start = self.at(-start_days, start_hour).replace(minute=0)
        event = Event.objects.create(
            title=title, kind=kind, category=category, format=fmt, location=location, online_url=url,
            start_at=start, end_at=start + timedelta(hours=duration_hours), organizer=self.users[organizer],
            target_audience=audience, capacity=capacity, participation_goal=goal, description=description,
            status=Event.Status.PENDING if status == Event.Status.PUBLISHED else status,
        )
        if status == Event.Status.PUBLISHED:
            publish_event(self.moderator, event, 'Publié (démonstration).')
            event.refresh_from_db()
        return event

    def seed_events(self):
        e = [
            self._event('Grand nettoyage de la plage', Event.Kind.EVENT, EcoCategory.RECYCLING, Event.Format.ON_SITE,
                        'Plage de La Marsa (lieu fictif de démonstration)', '', 5, 9, 4, 'demo_lina', Audience.ALL, 40, 30,
                        Event.Status.PUBLISHED, 'Ramassage collectif des déchets, tri sur place et pesée des collectes.'),
            self._event('Conférence : sobriété énergétique au bureau', Event.Kind.EVENT, EcoCategory.ENERGY,
                        Event.Format.ONLINE, '', 'https://example.org/ecoteams-demo', 1, 18, 2, 'demo_sarra',
                        Audience.EMPLOYEES, 100, None, Event.Status.PUBLISHED,
                        'Bonnes pratiques simples pour réduire la consommation électrique des espaces de travail.'),
            self._event('Atelier compost urbain', Event.Kind.EVENT, EcoCategory.FOOD, Event.Format.HYBRID,
                        'Maison des associations (démo)', 'https://example.org/ecoteams-compost', 12, 14, 3, 'demo_omar',
                        Audience.ASSOCIATIONS, 25, None, Event.Status.PUBLISHED,
                        'Apprendre à composter en appartement et à valoriser ses biodéchets.'),
            self._event('Campagne Mobilité douce', Event.Kind.CAMPAIGN, EcoCategory.TRANSPORT, Event.Format.ONLINE, '',
                        'https://example.org/ecoteams-mobilite', -10, 8, 24 * 30, 'demo_moderateur', Audience.STUDENTS,
                        None, 30, Event.Status.PUBLISHED,
                        'Un mois pour tester le vélo, la marche et les transports en commun au quotidien.'),
            self._event('Repair café solidaire', Event.Kind.EVENT, EcoCategory.CONSUMPTION, Event.Format.ON_SITE,
                        'Local associatif (démo)', '', 20, 15, 3, 'demo_karim', Audience.ALL, 20, None,
                        Event.Status.PENDING, 'Réparer ensemble petits appareils, vêtements et vélos.'),
        ]
        joins = {
            0: ['demo_amina', 'demo_lina', 'demo_karim', 'demo_omar', 'demo_nour'],
            1: ['demo_sarra', 'demo_mehdi', 'demo_ines', 'demo_lina', 'demo_amina'],
            2: ['demo_omar', 'demo_youssef'],
            3: ['demo_amina', 'demo_youssef', 'demo_nour', 'demo_mehdi'],
        }
        for index, usernames in joins.items():
            for username in usernames:
                if not EventParticipation.objects.filter(event=e[index], user=self.users[username]).exists():
                    try:
                        join_event(self.users[username], e[index])
                    except BusinessRuleError:
                        pass

    def tidy_notifications(self):
        for user in self.users.values():
            keep = list(Notification.objects.filter(recipient=user).order_by('-created_at').values_list('pk', flat=True)[:5])
            Notification.objects.filter(recipient=user, is_read=False).exclude(pk__in=keep).update(
                is_read=True, read_at=timezone.now())
