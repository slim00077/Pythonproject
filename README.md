# EcoTeams — Agir ensemble. Faire la différence.

**EcoTeams** est une application web Django qui transforme les gestes écologiques individuels en une
**compétition collective, mesurable et motivante entre équipes**. Les participants créent ou rejoignent
une équipe, relèvent des défis, déclarent leurs actions écologiques (validées par une modération),
gagnent des points, débloquent des badges, suivent leurs objectifs et comparent les équipes dans un
classement dynamique.

Thème : **EcoTrack / GreenTech** — Objectifs de développement durable visés : **ODD 13** (action
climatique), **ODD 12** (consommation et production responsables), **ODD 11** (villes et communautés
durables) et **ODD 17** (partenariats).

> Projet universitaire — module « Framework Python pour le Web ». Version 1.0 **sans intelligence
> artificielle** : l’architecture (services métier séparés des vues) permet d’ajouter des
> fonctionnalités d’IA dans une version ultérieure.

---

## Sommaire

1. [Fonctionnalités principales](#1-fonctionnalités-principales)
2. [Architecture de l’application](#2-architecture-de-lapplication)
3. [Répartition entre les cinq membres](#3-répartition-entre-les-cinq-membres)
4. [Stack technique](#4-stack-technique)
5. [Installation pas à pas (Windows)](#5-installation-pas-à-pas-windows)
6. [Configuration de la base de données (XAMPP / MySQL)](#6-configuration-de-la-base-de-données-xampp--mysql)
7. [Lancer et utiliser l’application](#7-lancer-et-utiliser-lapplication)
8. [Rôles, permissions et sécurité](#8-rôles-permissions-et-sécurité)
9. [Règles de score et de gamification](#9-règles-de-score-et-de-gamification)
10. [Tests](#10-tests)
11. [Dépannage](#11-dépannage)
12. [Collaboration Git à cinq](#12-collaboration-git-à-cinq)
13. [Évolutions prévues](#13-évolutions-prévues)

---

## 1. Fonctionnalités principales

| Domaine | Ce que l’on peut faire |
|---|---|
| Comptes | Inscription (rôle « Utilisateur » attribué automatiquement), connexion par identifiant **ou** e-mail, déconnexion sécurisée (POST + CSRF), profil public, édition du profil, changement de mot de passe |
| Équipes | CRUD complet, recherche et filtres, adhésion / départ, capitaine, retrait de membres, transfert du rôle de capitaine, une seule équipe par participant |
| Défis | Brouillon → soumission → validation → publication, participation, progression, réussite récompensée une seule fois, clôture / archivage |
| Actions écologiques | Catalogue configurable (points fixes, facteurs CO₂ documentés), déclaration avec photo justificative privée, modération (validation / refus motivé / annulation tracée), historique de modération |
| Objectifs et gamification | Objectifs personnels (suivi manuel ou automatique), registre de points immuable, badges à règles configurables, séries de jours consécutifs |
| Communauté | Événements et campagnes (présentiel, en ligne, hybride), publication après validation, inscriptions avec capacité, rappels automatiques |
| Analyses | Tableau de bord personnel, tableau de bord d’équipe, classement dynamique filtrable, historique, tableau de bord administrateur, rapports avec export CSV |
| Notifications | Centre de notifications, menu déroulant, marquer comme lu / tout lire / supprimer, préférences par type |
| Administration | Gestion des rôles et permissions (superutilisateur uniquement), gestion des utilisateurs, files de modération, catalogue, badges, corrections de points |

Toutes les données affichées (statistiques, classement, CO₂) sont **calculées à partir de la base de
données**. Les valeurs de CO₂ sont toujours présentées comme des **estimations** issues des facteurs
configurés par l’administration.

---

## 2. Architecture de l’application

Le projet suit les conventions du dépôt du cours
([DoussRim/AU-26-27-5TWIN4](https://github.com/DoussRim/AU-26-27-5TWIN4)) : paquet de projet `config/`,
modèle utilisateur personnalisé hérité d’`AbstractUser` déclaré dans `AUTH_USER_MODEL`, vues
fonctionnelles, un `urls.py` par application relié par `include()`, formulaires dans `forms.py`
(dont un `UserCreationForm` personnalisé), modèles intermédiaires (`through`) pour les relations
plusieurs-à-plusieurs, et `ModelAdmin` riches (inlines, filtres, recherche). La seule différence
assumée : la logique métier est placée dans des fichiers `services.py`, et non dans les vues.

```text
ecoteams/
├── manage.py
├── config/              Paramètres, URL racines, WSGI/ASGI
├── core/                Socle commun : page d’accueil, choix partagés, décorateurs de permissions,
│                        validateurs d’upload, icônes SVG, balises de gabarit, commande seed_demo_data
├── accounts/            Utilisateur personnalisé, rôles (groupes Django), authentification, gestion admin
├── teams/               Membre 1 — équipes et adhésions
├── challenges/          Membre 2 — défis écologiques et participations
├── actions/             Membre 3 — catalogue, déclarations, modération
├── goals/               Membre 4 — objectifs personnels
├── gamification/        Membre 4 — registre de points, badges, séries (service central de score)
├── community/           Membre 5 — événements et campagnes
├── notifications/       Membre 5 — notifications et préférences
├── analytics/           Membre 5 — tableaux de bord, classement, historique, rapports, journal d’activité
├── templates/           Gabarits (base, mises en page, composants partagés, un dossier par application)
├── static/              css/ecoteams.css, js/app.js, js/charts.js, img/
├── media/               Fichiers envoyés (logos, photos justificatives) — ignoré par Git
├── requirements.txt / pyproject.toml / .python-version
└── .env.example
```

Chaque application métier contient : `models.py`, `services.py` (règles métier, transactions),
`forms.py`, `views.py`, `urls.py` (et `admin_urls.py` pour le back-office), `admin.py`, `tests.py`.

**Flux principal :** une action déclarée (`actions`) est validée par un modérateur →
`actions.services.approve_submission()` → `gamification.services.award_points()` écrit une ligne
unique dans le registre → mise à jour des objectifs automatiques (`goals`), des badges, des
notifications (`notifications`) et du journal d’activité (`analytics`) → le classement (`analytics`)
est recalculé à partir du registre.

### Principales routes

| Public | Utilisateur connecté | Administration |
|---|---|---|
| `/` accueil | `/dashboard/` tableau de bord | `/admin-dashboard/` vue d’ensemble |
| `/accounts/register/` | `/teams/`, `/teams/create/`, `/teams/<slug>/` | `/admin/roles/` rôles et permissions |
| `/accounts/login/` | `/challenges/`, `/challenges/mine/` | `/admin/users/` utilisateurs |
| | `/actions/`, `/actions/catalog/`, `/actions/submit/` | `/admin/actions/` modération, `/admin/actions/types/` catalogue |
| | `/goals/`, `/achievements/` | `/admin/challenges/` validation des défis |
| | `/community/`, `/leaderboard/`, `/history/` | `/admin/events/` validation des événements |
| | `/notifications/`, `/profile/` | `/admin/badges/`, `/admin/points/`, `/admin/reports/` |

L’administration Django intégrée reste disponible à **`/django-admin/`** (elle a été déplacée pour
libérer les adresses `/admin/...` du back-office EcoTeams).

---

## 3. Répartition entre les cinq membres

| Membre | Module (applications) | Modèles | Fonctionnalités | Fichiers principaux |
|---|---|---|---|---|
| **1** | Équipes (`teams`) | `Team`, `Membership` | CRUD équipes, recherche et filtres, adhésion et départ, droits du capitaine, retrait de membres, transfert de capitaine, tableau de bord d’équipe | `teams/*`, `templates/teams/*` |
| **2** | Défis (`challenges`) | `Challenge`, `ChallengeParticipation` | CRUD défis, circuit brouillon → validation → publication, participation, progression, échéances, réussite récompensée | `challenges/*`, `templates/challenges/*` |
| **3** | Actions écologiques (`actions`) | `EcoActionType`, `ActionSubmission`, `ModerationLog` | Catalogue, déclaration avec preuve, modération, annulation auditée, estimations CO₂ configurables | `actions/*`, `templates/actions/*` |
| **4** | Objectifs et gamification (`goals`, `gamification`) | `Goal`, `PointTransaction`, `Badge`, `UserBadge` | CRUD objectifs, registre de points, règles de badges, séries, corrections de points | `goals/*`, `gamification/*`, templates associés |
| **5** | Communauté et analyses (`community`, `notifications`, `analytics`) | `Event`, `EventParticipation`, `Notification`, `NotificationPreference`, `ActivityLog` | CRUD événements, inscriptions, notifications, tableaux de bord, classement, historique, rapports | `community/*`, `notifications/*`, `analytics/*` |

**Responsabilités partagées (intégration)** — à relire ensemble avant chaque fusion :
`config/` (paramètres, URL), `core/` (décorateurs de permissions, choix communs, gabarits de base, CSS/JS),
`accounts/` (authentification, rôles), `gamification/services.py` (seul point d’écriture des points)
et la commande `seed_demo_data`. Proposition : le membre 4 est garant du service de score, le membre 5
des gabarits partagés et du CSS, et chaque membre maintient les tests de son module.

---

## 4. Stack technique

- **Python 3.11** (testé aussi avec 3.15) et **Django 5.2** (gabarits, ORM, formulaires, authentification, permissions)
- **MySQL/MariaDB via XAMPP** (base principale) — PostgreSQL et SQLite restent disponibles en repli
- HTML, CSS et **JavaScript natif** sans étape de build ; graphiques SVG maison (`static/js/charts.js`) ; icônes SVG intégrées
- Pillow (vérification des images), mysqlclient (MySQL/MariaDB), psycopg 3 (PostgreSQL), python-dotenv (fichier `.env`)
- Aucun CDN n’est nécessaire : seules les polices Google Fonts sont chargées de façon facultative et non bloquante (repli sur les polices système hors ligne)

---

## 5. Installation pas à pas (Windows)

### Prérequis

- Python **3.11** (`py -3.11 --version`). Si nécessaire : `py install 3.11` (gestionnaire d’installation Python) ou l’installateur de python.org
- Git
- **XAMPP** (https://www.apachefriends.org/) pour le service MySQL/MariaDB et phpMyAdmin — facultatif pour un premier essai avec SQLite
- Sur Windows, l’installation de `mysqlclient` nécessite une roue précompilée (wheel) ; `pip install -r requirements.txt` en récupère une automatiquement pour les versions de Python courantes. En cas d’échec, voir §11.

### 5.1 Environnement virtuel et dépendances

**PowerShell**

```powershell
cd C:\chemin\vers\ecoteams
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell refuse d’activer l’environnement : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**CMD**

```bat
cd C:\chemin\vers\ecoteams
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Variante uv** (outil utilisé dans le dépôt du cours ; `pyproject.toml` et `.python-version` sont fournis,
mais ce chemin n’a pas été testé pendant le développement — la méthode `pip` ci-dessus l’a été) :

```powershell
uv sync                    # crée .venv avec Python 3.11 (fichier .python-version) et installe les dépendances
uv run python manage.py runserver
```

### 5.2 Fichier `.env`

```powershell
Copy-Item .env.example .env     # CMD : copy .env.example .env
```

Ouvrez `.env` et renseignez au minimum `DJANGO_SECRET_KEY`. Pour générer une clé :

```powershell
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

- **Avec XAMPP / MySQL (recommandé)** : laissez `DB_ENGINE=mysql-xampp` et complétez `DB_NAME`, `DB_USER`,
  `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (voir §6).
- **Avec PostgreSQL** : mettez `DB_ENGINE=postgresql` et complétez les variables `POSTGRES_*`.
- **Premier essai sans service de base de données** : mettez `DB_ENGINE=sqlite`. Un fichier `db.sqlite3` sera créé. Sans fichier `.env`, l’application utilise SQLite et une clé de développement (uniquement en mode `DJANGO_DEBUG=True`).

### 5.3 Base de données, administrateur, données de démonstration

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
```

- `createsuperuser` crée **l’administrateur** (aucun mot de passe d’administrateur n’est écrit dans le code).
- `seed_demo_data` crée des données **clairement identifiées comme fictives** : 10 comptes `demo_*`, 5 équipes, 10 défis, 12 types d’actions, 58 déclarations (validées, en attente, refusée), 15 objectifs, 11 badges, événements et notifications. Les points passent par le service officiel de score.
  - Mot de passe des comptes de démonstration : variable `DEMO_USER_PASSWORD` du `.env`, ou option `--password "MonMotDePasse"`. Sans l’une ni l’autre, un mot de passe aléatoire est généré et affiché.
  - La commande est **idempotente** : la relancer ne duplique ni les données ni les points (vérifié sur MariaDB pendant le développement). `--reset` supprime puis recrée les données de démonstration.
  - Elle refuse de s’exécuter si `DJANGO_DEBUG=False` (sauf `--force`).
  - Le compte `demo_moderateur` possède un rôle personnalisé **Modérateur** (modération, validation des défis et événements, rapports) — il illustre les rôles sans être administrateur.

---

## 6. Configuration de la base de données (XAMPP / MySQL)

### 6.1 Démarrer XAMPP et créer la base

1. Ouvrez le **XAMPP Control Panel** (menu Démarrer, ou `C:\xampp\xampp-control.exe`) et cliquez sur **Start**
   en face de **MySQL** (et d’**Apache**, nécessaire pour phpMyAdmin). Le voyant passe au vert.
2. Ouvrez phpMyAdmin à l’adresse **http://localhost/phpmyadmin/**.
3. Onglet **SQL**, exécutez :

   ```sql
   CREATE DATABASE ecoteams_db
   CHARACTER SET utf8mb4
   COLLATE utf8mb4_unicode_ci;

   CREATE USER 'ecoteams_user'@'localhost'
   IDENTIFIED BY 'CHANGEZ_MOI_PAR_UN_MOT_DE_PASSE_LOCAL';
   CREATE USER 'ecoteams_user'@'127.0.0.1'
   IDENTIFIED BY 'CHANGEZ_MOI_PAR_UN_MOT_DE_PASSE_LOCAL';

   GRANT ALL PRIVILEGES ON ecoteams_db.* TO 'ecoteams_user'@'localhost';
   GRANT ALL PRIVILEGES ON ecoteams_db.* TO 'ecoteams_user'@'127.0.0.1';

   FLUSH PRIVILEGES;
   ```

   Remplacez `CHANGEZ_MOI_PAR_UN_MOT_DE_PASSE_LOCAL` par le mot de passe de votre choix : il doit être
   **identique** à `DB_PASSWORD` dans votre `.env`. Ces commandes sont à exécuter par la personne qui
   administre la base (chaque membre de l’équipe, sur sa propre machine XAMPP).

   Les deux `CREATE USER` (`localhost` et `127.0.0.1`) évitent une erreur d’accès selon que Django se
   connecte par le socket local ou par TCP — utilisez `DB_HOST=127.0.0.1` dans `.env` pour rester cohérent.

4. Pour que `python manage.py test` puisse créer sa base de test, donnez aussi les droits sur
   `test_ecoteams_db` (Django la crée et la détruit à chaque exécution des tests) :

   ```sql
   GRANT ALL PRIVILEGES ON `test_ecoteams_db`.* TO 'ecoteams_user'@'localhost';
   GRANT ALL PRIVILEGES ON `test_ecoteams_db`.* TO 'ecoteams_user'@'127.0.0.1';
   FLUSH PRIVILEGES;
   ```

### 6.2 Fichier `.env`

```ini
DB_ENGINE=mysql-xampp
DB_NAME=ecoteams_db
DB_USER=ecoteams_user
DB_PASSWORD=CHANGEZ_MOI_PAR_UN_MOT_DE_PASSE_LOCAL
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 6.3 Pourquoi `DB_ENGINE=mysql-xampp` et pas simplement `mysql`

XAMPP installe **MariaDB 10.4**, mais Django 5.2 exige au minimum **MariaDB 10.5** pour son backend MySQL
standard (`django.db.backends.mysql`) et refuse la connexion avec l’erreur
`NotSupportedError: MariaDB 10.5 or later is required`. Vérifié pendant le développement de ce projet.

`DB_ENGINE=mysql-xampp` utilise un petit backend local, [`core/db_backends/mysql_xampp`](core/db_backends/mysql_xampp/base.py),
qui hérite entièrement du backend MySQL de Django et ne modifie que **deux points de version** :
le seuil minimal (ramené à 10.4) et la disponibilité de `INSERT ... RETURNING` (réellement absente avant
MariaDB 10.5, remise à la condition utilisée par Django avant la version 5.0). Tout le reste — SQL émis,
types de colonnes, transactions, contraintes, verrous — est strictement le backend MySQL standard.

Si vous mettez à niveau MariaDB (10.11 LTS par exemple) ou utilisez MySQL Server, repassez simplement
`DB_ENGINE` sur `mysql` : le backend standard de Django suffit alors.

### 6.4 Pourquoi `TIME_ZONE` est aligné sur la connexion

XAMPP ne charge pas les tables de fuseaux horaires de MySQL (`mysql.time_zone*` restent vides). Sans elles,
la fonction `CONVERT_TZ()` que Django utilise pour regrouper par jour/semaine renvoie `NULL`, et les
graphiques des tableaux de bord (points par jour, par semaine) remonteraient vides. `config/settings.py`
indique à Django le fuseau réel de la connexion (`TIME_ZONE`, `Africa/Tunis` par défaut) via
`DATABASES['default']['TIME_ZONE']` : Django n’émet alors plus aucun `CONVERT_TZ()` pour les dates, et les
agrégats fonctionnent sans installer les tables de fuseaux sur le serveur. Si vous chargez ces tables
(`mysql_tzinfo_to_sql`) et préférez stocker en UTC, mettez `DB_TIME_ZONE=UTC` dans `.env`.

### 6.5 Migrations et vérification

```powershell
python manage.py migrate
python manage.py check
python manage.py seed_demo_data
```

`manage.py check` doit afficher *System check identified no issues*. Un message `(models.W036) MariaDB
does not support unique constraints with conditions` indiquerait une régression : les deux contraintes
conditionnelles d’origine (« un capitaine par équipe », « une déclaration par jour ») ont été remplacées
par des colonnes dédiées (`Membership.captain_of`, `ActionSubmission.dedupe_key`) justement pour que ces
règles restent garanties par un index unique sur MySQL comme sur PostgreSQL — ce message ne doit donc plus
apparaître.

### 6.6 Alternative PostgreSQL

```sql
CREATE USER ecoteams WITH PASSWORD 'choisissez-un-mot-de-passe';
CREATE DATABASE ecoteams OWNER ecoteams ENCODING 'UTF8';
ALTER USER ecoteams CREATEDB;   -- nécessaire pour que « manage.py test » crée sa base de test
```

```ini
DB_ENGINE=postgresql
POSTGRES_DB=ecoteams
POSTGRES_USER=ecoteams
POSTGRES_PASSWORD=choisissez-un-mot-de-passe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Puis `python manage.py migrate`, `createsuperuser` et `seed_demo_data` comme ci-dessus.

---

## 7. Lancer et utiliser l’application

```powershell
python manage.py runserver
```

| Adresse | Contenu |
|---|---|
| http://127.0.0.1:8000/ | Page d’accueil publique |
| http://127.0.0.1:8000/accounts/login/ | Connexion (utilisateur → `/dashboard/`, administrateur → `/admin-dashboard/`) |
| http://127.0.0.1:8000/admin-dashboard/ | Back-office EcoTeams |
| http://127.0.0.1:8000/admin/roles/ | Rôles et permissions (superutilisateur uniquement) |
| http://127.0.0.1:8000/django-admin/ | Administration Django intégrée |

**Scénario de démonstration conseillé**

1. Connectez-vous avec `demo_amina` : tableau de bord, équipe « Les Pédaleurs Verts », classement, badges.
2. Déclarez une action (`/actions/submit/`) en la liant au défi « Mois du vélo ».
3. Connectez-vous avec `demo_moderateur` (ou l’administrateur) : `/admin/actions/` → validez l’action. Les points apparaissent dans le registre, le classement bouge, une notification est envoyée.
4. En administrateur : `/admin/roles/` → créez un rôle « Organisateur de défis » avec la permission clé « Peut valider, publier et clôturer les défis », puis attribuez-le à un utilisateur.
5. Inscrivez un nouvel utilisateur via `/accounts/register/` : il reçoit automatiquement le rôle « Utilisateur ».

**Rappels d’événements** — les participants sont notifiés des événements qui commencent dans les 48 h :
à l’ouverture de leur tableau de bord, ou via la commande (planifiable avec le Planificateur de tâches Windows) :

```powershell
python manage.py send_event_reminders
```

---

## 8. Rôles, permissions et sécurité

### Niveaux d’accès

| Niveau | Obtention | Accès |
|---|---|---|
| **Utilisateur** | Automatique à l’inscription (groupe `Utilisateur`) | Fonctionnalités participant ; ses propres données uniquement |
| **Rôle personnalisé** | Créé et attribué par un superutilisateur sur `/admin/roles/` | Les écrans liés aux permissions choisies (ex. modération) |
| **Administrateur** | `python manage.py createsuperuser` | Tout, y compris rôles, utilisateurs et `/django-admin/` |

Permissions « clé » qui ouvrent des écrans du back-office : `actions.moderate_actionsubmission`,
`actions.change_ecoactiontype`, `challenges.review_challenge`, `community.review_event`,
`gamification.change_badge`, `gamification.adjust_points`, `analytics.view_reports`
(liste centralisée dans `core/permissions.py`).

### Mesures de sécurité

- Gestion des rôles et des utilisateurs réservée aux **superutilisateurs actifs** (décorateur `superuser_required`, réponse 403 sinon) ; créer un rôle n’ajoute jamais son créateur à ce rôle ; les noms « Administrateur », « admin » et le rôle par défaut sont réservés ; le rôle par défaut est verrouillé (ni renommable, ni supprimable, sans permissions).
- Aucun formulaire utilisateur n’expose `is_staff`, `is_superuser`, groupes, permissions ou mot de passe (testé en envoyant ces champs).
- Toutes les vérifications sont faites **côté serveur** ; les liens masqués ne sont qu’un confort.
- **Anti-IDOR** : les objets privés sont chargés avec un filtre sur leur propriétaire (`get_object_or_404(Goal, pk=pk, user=request.user)`), ce qui renvoie 404 pour les autres utilisateurs ; brouillons de défis et d’événements invisibles pour les tiers.
- Photos justificatives servies uniquement par une vue protégée (auteur ou modérateur) ; le dossier `media/evidence/` n’est jamais exposé publiquement.
- Uploads : extensions autorisées (jpg, jpeg, png, webp), taille maximale (`ECOTEAMS_MAX_UPLOAD_MB`), vérification Pillow, noms de fichiers aléatoires.
- CSRF sur tous les formulaires, déconnexion en POST, mots de passe hachés et validés par Django, secrets dans `.env` (jamais dans Git), cookies `HttpOnly`, `X-Frame-Options: DENY`, liens de notification limités aux chemins internes.
- Registre de points en **ajout seul** (modification et suppression impossibles via l’ORM ou l’admin), références uniques contre les doubles attributions, transactions et verrous `select_for_update` lors de la modération.

---

## 9. Règles de score et de gamification

1. Les points d’une action ne sont attribués **qu’après validation** par la modération, selon la valeur fixe du catalogue.
2. La réussite d’un défi n’est récompensée que si le nombre requis d’actions **validées et liées au défi** est atteint.
3. Une même action ou une même réussite ne peut jamais rapporter deux fois (référence unique `action:<id>` / `challenge:<id>:user:<id>`).
4. Les utilisateurs ne peuvent pas modifier leurs points. Les corrections sont des **écritures nouvelles**, motivées, tracées (`/admin/points/`) et ne peuvent rendre un solde négatif.
5. Les points d’équipe sont la somme des écritures du registre portant l’équipe **au moment du gain** (changer d’équipe ne transfère pas les points passés).
6. Badges : premier geste, total de points, actions par catégorie, série de jours, défis réussis, objectifs atteints, inscriptions aux événements, rang de l’équipe — évalués après chaque changement de score.
7. Paliers d’équipe (100, 250, 500, 1 000… points) notifiés aux membres.
8. Une déclaration validée ne peut plus être modifiée ni supprimée par son auteur ; seule une annulation motivée par un modérateur est possible (écriture négative tracée).
9. Une même action ne peut être déclarée qu’une fois par jour et seulement pour les 30 derniers jours.

**CO₂** : estimation = quantité × facteur configuré. Les facteurs fournis dans les données de démonstration
sont des **valeurs indicatives** à remplacer par des valeurs sourcées (ex. Base Empreinte® de l’ADEME)
avant tout usage réel ; le formulaire du catalogue exige une source documentée pour chaque facteur.

---

## 10. Tests

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

La suite comprend **140 tests** répartis par application (`<app>/tests.py`) : authentification et
redirections, inscription sans auto-promotion, rôles réservés au superutilisateur, IDOR, CRUD et règles
des cinq modules, validation et refus, absence de double attribution de points, immuabilité du
registre, badges et séries, classement calculé depuis le registre, statistiques, notifications privées,
rendu de toutes les pages pour chaque niveau d’accès (à partir des données de démonstration) et
idempotence de `seed_demo_data`.

Résultats obtenus pendant le développement : **140 tests réussis** sur **MariaDB 10.4 (XAMPP)**, ainsi
que sur SQLite, avec Python 3.15.1 et Django 5.2.18. PostgreSQL reste à vérifier sur votre machine.

Lancer les tests d’un seul module : `python manage.py test teams` (ou `challenges`, `actions`, …).

---

## EcoPulse — intelligence environnementale en direct

Page `/ecopulse/` (lien « EcoPulse » dans chaque menu latéral). Application `ecopulse/` **sans modèle ni migration**.

- **Données** : prévisions et qualité de l'air d'[Open-Meteo](https://open-meteo.com/) (CC BY 4.0, usage non commercial),
  timeout 8 s, cache 15 min, copie obsolète 6 h en secours, quota global de 200 appels/heure.
- **Règles** (`ecopulse/rules.py`) : validation des valeurs, bandes de classification documentées et configurables
  (`ECOPULSE_THRESHOLDS`). Ce sont des repères indicatifs, **pas des alertes officielles**.
- **Lieu** : formulaire (ville géocodée ou coordonnées), gardé en session ; par défaut la ville de l'organisation, sinon Tunis.
- **IA** (`ecopulse/ai.py`, SDK officiel `google-genai`, Google Gemini) : explique les valeurs validées et propose des défis.
  Variables `GEMINI_API_KEY` et `GEMINI_MODEL` (voir « Configurer l'IA » ci-dessous) ; sans elles, tout le reste fonctionne.
  6 analyses/heure/utilisateur, résultats mis en cache 30 min.
- **Défis proposés** : enregistrés via le workflow existant (brouillon, ou « en attente de validation »), 0 point proposé ;
  un valideur publie et fixe les points. Rien n'est publié ni récompensé automatiquement.
- **EcoProof AI** (page « Défis », `ecopulse/ecoproof.py`) : assistant **consultatif** qui aide à préparer une déclaration
  d'action (catégorie, informations manquantes, preuves à ajouter, points pour le modérateur). Il réutilise le client Gemini
  d'EcoPulse (`ECOPROOF_AI_MAX_PER_HOUR`=10). Sans IA : vérifications de complétude déterministes uniquement. L'IA ne valide
  rien : la déclaration est envoyée par un POST classique (`ActionSubmission` en attente, 0 point) et seule la modération
  existante attribue des points. Les photos sont validées côté serveur (contenu réel JPEG/PNG/WebP, 5 Mo) puis ré-encodées
  sans métadonnées avant envoi à Gemini.

### Configurer l'IA (développeurs)

1. `pip install -r requirements.txt` (ou `pip install google-genai`).
2. Créez une clé sur <https://aistudio.google.com/apikey> et choisissez un modèle disponible pour votre compte
   (<https://ai.google.dev/gemini-api/docs/models>). Le code n'impose aucun modèle par défaut.
3. Dans `.env` (jamais versionné) : `GEMINI_API_KEY=...` et `GEMINI_MODEL=...`, puis redémarrez le serveur.
4. (Facultatif) `GEMINI_THINKING_LEVEL=low` (défaut) accélère les réponses ; mettez une valeur vide si votre modèle ne gère pas ce réglage.
5. Vérifiez : `python manage.py check_gemini` (une requête minimale ; affiche la durée réelle).

Les utilisateurs ne voient jamais de détail technique : si l'IA n'est pas configurée ou échoue, ils lisent « Le service
d'analyse intelligente est temporairement indisponible. Vous pouvez continuer manuellement. ». La cause réelle est dans les
journaux du serveur (logger `ecoteams.ecopulse`) : variable absente, clé refusée (401/403 ou « API key not valid »), modèle
introuvable (404, vérifiez `GEMINI_MODEL`), quota atteint (429), délai dépassé (`ECOPULSE_AI_TIMEOUT`), réponse bloquée ou mal formée.
Le « créateur de défis EcoQuest » n'existe pas dans le projet : les missions proposées par EcoPulse en tiennent lieu.
- **Évaluation** : `ecopulse/eval/` (voir son README). Tests : `python manage.py test ecopulse`.

## 11. Dépannage

| Problème | Solution |
|---|---|
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou utilisez CMD (`.venv\Scripts\activate.bat`) |
| `py -3.11` introuvable | Installez Python 3.11 (`py install 3.11` ou python.org) puis recréez `.venv` |
| `ModuleNotFoundError: No module named 'django'` | L’environnement virtuel n’est pas activé, ou `pip install -r requirements.txt` n’a pas été exécuté |
| `ModuleNotFoundError: No module named 'MySQLdb'` | `pip install mysqlclient` (dans le venv activé) ; sous Windows, s’il n’existe pas de roue précompilée pour votre version de Python, utilisez Python 3.11 ou 3.12 |
| `django.db.utils.NotSupportedError: MariaDB 10.5 or later is required` | Utilisez `DB_ENGINE=mysql-xampp` (voir §6.3), ou mettez à niveau MariaDB |
| `(2002) Can't connect to MySQL server` / connexion refusée sur le port 3306 | Le service MySQL de XAMPP n’est pas démarré (XAMPP Control Panel → **Start** sur MySQL) ; vérifiez aussi qu’aucun autre service n’occupe déjà le port 3306 |
| `(1045) Access denied for user 'ecoteams_user'@...` | Le mot de passe dans `.env` (`DB_PASSWORD`) ne correspond pas à celui créé en SQL, ou l’utilisateur n’a pas été créé pour l’hôte utilisé (`localhost` **et** `127.0.0.1`, voir §6.1) |
| `(1049) Unknown database 'ecoteams_db'` | La base n’a pas été créée ; relancez le `CREATE DATABASE` du §6.1 |
| Port 3306 déjà utilisé (un autre MySQL tourne) | Changez `DB_PORT` dans `.env` et dans la configuration MySQL de XAMPP (`my.ini`, section `[mysqld]` → `port=...`), ou arrêtez l’autre service |
| Les graphiques « points par jour/semaine » du tableau de bord restent vides sur MySQL | Vérifiez que `DATABASES['default']['TIME_ZONE']` est bien défini dans `config/settings.py` (voir §6.4) — ne le supprimez pas |
| `(models.W036) MariaDB does not support unique constraints with conditions` au `check`/`migrate` | Régression : les contraintes conditionnelles ont été remplacées par `captain_of` / `dedupe_key` (§6.5) ; vérifiez que vous utilisez bien la version actuelle de `teams/models.py` et `actions/models.py` |
| `connection to server at "localhost" … failed` (PostgreSQL) | PostgreSQL n’est pas démarré ou les variables `POSTGRES_*` sont incorrectes ; pour un essai rapide, `DB_ENGINE=sqlite` |
| `permission denied to create database` pendant les tests (PostgreSQL) | `ALTER USER ecoteams CREATEDB;` |
| `DJANGO_SECRET_KEY doit être défini…` | Renseignez `DJANGO_SECRET_KEY` dans `.env` lorsque `DJANGO_DEBUG=False` |
| `no such table` / `relation does not exist` | `python manage.py migrate` |
| Images envoyées non affichées en production | Les fichiers média ne sont servis par Django qu’en mode développement ; configurez votre serveur web |
| `seed_demo_data` refuse de s’exécuter | Passez en `DJANGO_DEBUG=True` ou ajoutez `--force` (à éviter en production) |
| Erreur 403 sur une page d’administration | Normal pour un compte sans la permission requise ; connectez-vous avec l’administrateur |
| Mot de passe des comptes démo oublié | `python manage.py seed_demo_data --reset --password "NouveauMotDePasse"` |

---

## 12. Collaboration Git à cinq

### Branches

| Branche | Responsable | Périmètre |
|---|---|---|
| `main` | toute l’équipe (protégée) | Version stable, uniquement via pull request |
| `develop` | toute l’équipe | Intégration continue des modules |
| `feature/teams` | Membre 1 | `teams/`, `templates/teams/` |
| `feature/challenges` | Membre 2 | `challenges/`, `templates/challenges/` |
| `feature/actions` | Membre 3 | `actions/`, `templates/actions/` |
| `feature/goals-gamification` | Membre 4 | `goals/`, `gamification/`, templates associés |
| `feature/community-analytics` | Membre 5 | `community/`, `notifications/`, `analytics/`, templates associés |

Les noms `feature/*-ai-*` du cahier des charges initial sont remplacés par ces noms, l’IA étant hors périmètre de cette version.

### Commandes courantes

```powershell
# Première mise en place (une seule personne)
git init
git add .
git commit -m "Initialisation du projet EcoTeams"
git branch -M main
git remote add origin https://github.com/<organisation>/ecoteams.git
git push -u origin main
git switch -c develop
git push -u origin develop

# Chaque membre : récupérer le projet et créer sa branche
git clone https://github.com/<organisation>/ecoteams.git
cd ecoteams
git switch develop
git switch -c feature/teams

# Travailler et enregistrer
git status
git add teams/ templates/teams/
git commit -m "teams: ajout du transfert de capitaine"
git push -u origin feature/teams

# Mettre sa branche à jour avec develop
git fetch origin
git merge origin/develop        # ou : git rebase origin/develop (si la branche n’est pas partagée)
```

**Ouvrir une pull request** : sur GitHub, « Compare & pull request » de `feature/teams` vers `develop`,
décrivez le changement, demandez la relecture d’au moins un autre membre, vérifiez que
`python manage.py test` passe, puis fusionnez. `develop` est fusionnée dans `main` avant chaque rendu.

### Résoudre un conflit sans risque

1. `git fetch origin` puis `git merge origin/develop` sur votre branche.
2. Ouvrez les fichiers signalés, gardez les deux versions utiles entre `<<<<<<<` et `>>>>>>>`, supprimez les marqueurs.
3. **Migrations** : si deux membres ont créé une migration du même numéro dans une application partagée, ne modifiez pas la migration d’autrui ; lancez `python manage.py makemigrations --merge`.
4. `python manage.py check` et `python manage.py test`, puis `git add .` et `git commit`.
5. En cas de doute : `git merge --abort` et demandez de l’aide — ne forcez jamais (`push --force`) sur `develop` ou `main`.

### Bonnes pratiques

- Ne modifiez les fichiers partagés (`config/`, `core/`, `accounts/`, `gamification/services.py`, `templates/base.html`, `static/css/ecoteams.css`) que via une pull request relue par l’équipe.
- Ne commitez jamais `.env`, `db.sqlite3`, `media/` ou `.venv/` (déjà dans `.gitignore`).
- Messages de commit préfixés par le module : `actions: …`, `community: …`.
- Ajoutez un test pour chaque règle métier modifiée.

---

## 13. Évolutions prévues

- **IA (version future)** : les services métier existants offrent des points d’accroche naturels (recommandation d’équipe à partir des profils, génération de brouillons de défis soumis à validation, aide à la déclaration, coach personnel, analyse d’impact d’équipe). Toute fonctionnalité d’IA devra rester consultative : elle ne pourra ni publier, ni valider, ni attribuer de points sans passer par les services et permissions existants.
- Notifications par e-mail, export PDF des rapports, plusieurs équipes par participant, API REST.
