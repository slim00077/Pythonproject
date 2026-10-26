# Intégration, livraison et déploiement (CI/CD)

```text
 feature/*  ──PR──►  develop  ──PR──►  main
                │                       │
        CI : tests SQLite + PostgreSQL  CI (mêmes tests) ─► CD : image Docker → GHCR
        + image Docker + config prod                          └► déploiement Render ─► URL publique
```

| Brique | Fichier | Rôle |
|---|---|---|
| Image Docker | `Dockerfile`, `docker/entrypoint.sh`, `.dockerignore` | gunicorn + WhiteNoise, utilisateur non-root, health check |
| Environnement local complet | `docker-compose.yml` | application + PostgreSQL en une commande |
| Intégration continue | `.github/workflows/ci.yml` | tests sur SQLite **et** PostgreSQL, couverture, `check --deploy`, build + test de fumée de l'image |
| Livraison continue | `.github/workflows/cd.yml` | rejoue la CI, publie l'image sur GHCR, déclenche Render, vérifie l'URL publique |
| Infrastructure | `render.yaml` | service web Docker + base PostgreSQL décrits en code |
| Sonde de santé | `/healthz/` | 200 si la base répond (Docker, CI, Render) |

## 1. Tester l'image en local (5 min)

Prérequis : Docker Desktop **démarré**.

```powershell
docker compose up --build
```

Ouvrez http://localhost:8000 (port occupé ? `$env:WEB_PORT=8081; docker compose up --build`).
Comptes créés automatiquement : `admin` / `Admin-Local-2026!` et les comptes `demo_*` (mot de passe `Demo12345!pass`).
Pour le coach IA : créez un fichier `.env` à côté de `docker-compose.yml` avec `GEMINI_API_KEY=...`.
Arrêt et remise à zéro : `docker compose down -v`.

## 2. Intégration continue (automatique)

Elle démarre toute seule à chaque pull request vers `develop` ou `main`, et à chaque push sur ces branches.
Onglet **Actions** du dépôt GitHub → workflow **CI**. Quatre contrôles :

1. **Tests (sqlite)** et **Tests (postgresql)** : `check`, migrations à jour, syntaxe JS, tous les tests, couverture ≥ 90 % sur goals/gamification.
2. **Configuration de production** : `check --deploy` avec `DEBUG=False`.
3. **Image Docker** : construction puis démarrage du conteneur et requêtes réelles (`/healthz/`, accueil, connexion, fichiers statiques).

**À activer une fois (propriétaire du dépôt)** : Settings → Branches → *Add branch protection rule* pour `develop` et `main` :
cocher *Require a pull request before merging* et *Require status checks to pass* (choisir les contrôles ci-dessus).
Ainsi, plus personne ne peut fusionner du code qui casse les tests.

## 3. Registre d'images (GHCR) — automatique

À chaque fusion dans `main`, la CD publie `ghcr.io/<propriétaire>/<dépôt>:latest` et `:<sha>`.
Après la **première** publication : GitHub → profil ou organisation → *Packages* → l'image → *Package settings* →
*Change visibility* → **Public** (pour que n'importe qui puisse faire `docker pull`).

```powershell
docker pull ghcr.io/slim00077/pythonproject:latest
docker run -p 8000:8000 -e DJANGO_SECRET_KEY=une-cle-longue-et-aleatoire -e DJANGO_SECURE_COOKIES=False ghcr.io/slim00077/pythonproject:latest
```

## 4. Hébergement : créer le site sur Render (une seule fois, 10 min)

1. Créez un compte sur https://render.com (connexion avec GitHub).
2. **New → Blueprint**, choisissez le dépôt, branche `main`. Render lit `render.yaml` et prépare : un service web Docker `ecoteams`
   et une base PostgreSQL `ecoteams-db` (plans gratuits).
3. Render demande les valeurs secrètes (`sync: false`) : 
   - `DJANGO_SUPERUSER_PASSWORD` : mot de passe de l'administrateur (choisissez-le, ne le publiez pas) ;
   - `DEMO_USER_PASSWORD` : mot de passe des comptes `demo_*` ;
   - `GEMINI_API_KEY` : votre clé (laisser vide désactive proprement le coach IA).
4. Lancez le premier déploiement (**Apply**). Au premier démarrage : migrations, données de démonstration, compte `admin`.
5. L'adresse publique est `https://ecoteams-xxxx.onrender.com` (visible en haut du service). Notez-la : c'est votre **URL live**.

## 5. Brancher la livraison continue (une seule fois, 5 min)

1. Render → service `ecoteams` → **Settings → Deploy Hook** → copiez l'URL.
2. GitHub → dépôt → **Settings → Secrets and variables → Actions** :
   - onglet *Secrets* → **New repository secret** : nom `RENDER_DEPLOY_HOOK_URL`, valeur = l'URL du hook ;
   - onglet *Variables* → **New repository variable** : nom `LIVE_URL`, valeur = l'URL publique (sans `/` final).
3. GitHub → **Settings → Environments → New environment** : `production` (facultatif : *Required reviewers* pour exiger une validation
   humaine avant chaque mise en production).

## 6. Mettre en production

1. Pull request `develop` → `main`, la CI passe au vert, fusion.
2. La CD se lance (onglet **Actions → CD**) : CI → publication de l'image → déclenchement Render → attente de `/healthz/` → test de fumée.
3. Ouvrez l'URL live : c'est la nouvelle version. Pour revenir en arrière : Render → *Deploys* → *Rollback*.

## 7. Limites du plan gratuit (à connaître pour la soutenance)

- **Mise en veille** : après ~15 min sans visite, le service s'endort ; la première requête met ~50 s. Ouvrez l'URL 2 minutes avant la démonstration.
- **Base gratuite** : la base PostgreSQL gratuite de Render expire après 30 jours ; recréez-la (ou passez en plan payant) si le projet vit plus longtemps.
- **Fichiers envoyés** (logos, photos justificatives) : stockage éphémère, perdu à chaque déploiement. Pour la production réelle : stockage objet (S3...).
- **Coach IA** : fonctionne tant que `GEMINI_API_KEY` est définie ; sinon un message clair s'affiche.

## 8. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| CI rouge sur « Tests (postgresql) » seulement | requête incompatible PostgreSQL (ex. `select_for_update` avec jointure) | corriger la requête ; c'est précisément ce que ce contrôle protège |
| `CSRF verification failed` sur le site live | domaine non reconnu | Render fournit `RENDER_EXTERNAL_HOSTNAME` ; pour un domaine personnalisé, ajouter `DJANGO_ALLOWED_HOSTS` et `DJANGO_CSRF_TRUSTED_ORIGINS` |
| CD échoue à « Vérifier la configuration » | secret ou variable manquants | étape 5 |
| CD échoue à « Attendre que la nouvelle version réponde » | démarrage lent ou erreur au boot | Render → *Logs* |
| `docker compose up` : port déjà utilisé | un autre service écoute sur 8000 | `$env:WEB_PORT=8081` |
| Image : `exec ./entrypoint.sh: no such file` | fins de ligne Windows dans un script | `.gitattributes` force LF ; refaire `git add --renormalize .` |
