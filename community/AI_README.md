# Fonctionnalités d’IA de la communauté

Ce document décrit les recommandations, l’assistant de rédaction, l’estimation d’impact et la prévision de participation actuellement intégrés à `community`. Les calculs locaux ne nécessitent ni clé API ni service externe.

## 1. Recommandations d’événements et de campagnes

La page `/community/` affiche jusqu’à trois événements publiés, encore accessibles et non déjà rejoints. Le classement est calculé localement par `community/ai/recommender.py`, sans dépendance d’apprentissage automatique.

Le score additionne des affinités de catégorie (actions écologiques validées, défis suivis, thème favori, domaine de l’équipe, de l’organisation et badges thématiques), un bonus si l’événement est organisé par l’organisation de la personne ou se trouve dans sa ville, et un bonus de popularité. Les points et le nombre de badges modulent légèrement le poids de la popularité. Les événements hors public cible, complets ou dont la date limite d’inscription est dépassée sont exclus.

Une explication courte accompagne chaque résultat. Les actions utilisées sont uniquement les déclarations validées ; les données du profil restent dans l’application et ne sont jamais transmises à un modèle distant par le recommandeur.

## 2. Assistant de rédaction

Le bouton « Générer avec l’IA » apparaît aux organisateurs autorisés sur le formulaire de création ou de modification d’un brouillon. Il utilise le titre, la catégorie, la date et le lieu fournis pour proposer une description, un programme et des hashtags. Le contenu est injecté dans le champ description existant, que l’organisateur peut corriger ; il n’est jamais enregistré automatiquement.

L’endpoint AJAX est réservé aux utilisateurs connectés et aux organisateurs, utilise la protection CSRF de Django et limite chaque compte à cinq demandes par minute. Les entrées sont validées côté serveur. Seuls les champs nécessaires à la rédaction sont envoyés au provider distant ; aucune donnée de compte, d’équipe, de participation ou de points ne lui est transmise.

### Configuration

Par défaut, le provider `template` fonctionne hors ligne et sans clé. Pour un endpoint compatible avec l’API Chat Completions d’OpenAI, configurez les variables d’environnement suivantes dans votre fichier `.env` local (ne le commitez pas) :

```dotenv
AI_PROVIDER=openai_compatible
AI_API_KEY=remplacez-par-votre-cle
AI_MODEL=gpt-4o-mini
AI_TIMEOUT=10
AI_API_BASE_URL=https://api.openai.com/v1
```

`AI_API_BASE_URL` permet de configurer l’URL de base d’un service compatible. Sans clé, avec `AI_PROVIDER=template` ou si l’appel distant échoue, expire ou retourne un contenu invalide, le service journalise l’échec et utilise les modèles locaux. Aucune migration n’est nécessaire pour ces deux fonctionnalités.

### Limites et tests

Les recommandations sont heuristiques et leurs poids sont des choix explicables, pas une prédiction de participation. La rédaction par templates fournit une proposition générique ; un provider distant peut produire des résultats inexacts, qui doivent être relus avant enregistrement. Le timeout et la validation de réponse limitent les risques liés à l’appel externe.

La limitation d’appels s’appuie sur le cache Django ; avec le cache mémoire local par défaut, les compteurs ne sont pas partagés entre plusieurs processus serveur. Configurez un cache partagé si l’application est déployée sur plusieurs workers.

Lancer les tests ciblés avec :

```powershell
env\Scripts\python.exe manage.py test community
```

## 3. Estimation de l’impact d’une campagne

`community/ai/impact.py` estime le CO₂ et les points potentiels selon la catégorie de la campagne, le nombre de participants prévus et la durée. Le calcul est :

```text
facteur par participant-jour × participants prévus × durée en jours
```

Le nombre prévu est l’objectif de participation s’il existe, sinon la capacité, sinon le nombre d’inscriptions actuelles. La durée est calculée à partir des dates de début et de fin, avec une précision de quatre décimales en jours. Le résultat CO₂ est arrondi à 0,001 kg et les points potentiels à l’entier le plus proche. Une estimation n’est pas affichée si le nombre de participants est nul, si la durée est nulle ou si aucun facteur actif n’existe.

Les facteurs sont modifiables dans l’administration Django (`Facteurs d’impact des campagnes`). La migration `0003_campaignimpactfactor_event_actual_co2_saved_kg` crée une ligne par catégorie. Les valeurs initiales sont des hypothèses pédagogiques illustratives, non des facteurs mesurés :

| Catégorie | kg CO₂ / participant-jour | points / participant-jour |
|---|---:|---:|
| Transport | 0,2500 | 12 |
| Recyclage | 0,1500 | 10 |
| Énergie | 0,2000 | 10 |
| Eau | 0,1000 | 8 |
| Consommation responsable | 0,1200 | 8 |
| Alimentation et anti-gaspillage | 0,2000 | 12 |

Après la fin d’une campagne, son organisateur peut saisir le CO₂ réellement économisé sur la fiche. Le résultat est comparé à l’estimation ; il n’est pas calculé automatiquement à partir des inscriptions et ne déclenche pas l’attribution de points. Remplacez les valeurs illustratives par des facteurs provenant d’une méthodologie locale vérifiée avant de communiquer un bilan environnemental.

## 4. Prévision de participation

Les organisateurs voient la prévision sur la fiche d’un événement publié et à venir. La colonne `EventParticipation.attended` distingue présent (`True`), absent (`False`) et inconnu (`NULL`). Après l’événement, l’organisateur peut saisir les présences depuis « Gérer les présences » ; les valeurs inconnues ne sont jamais comptées comme absences.

La prévision n’est pas affichée tant qu’aucune présence passée vérifiée n’est disponible. Ensuite, elle calcule un taux global lissé, puis des taux par catégorie et par délai d’inscription (tardif : au plus un jour, moyen : de un à sept jours, anticipé : plus de sept jours). Les petits groupes sont ramenés vers le taux global avec un a priori de cinq observations. Pour chaque inscrit, le taux de présence prédit combine 60 % du taux de sa catégorie, 30 % du taux de son délai d’inscription et 10 % du taux global. La prévision affiche la somme des probabilités individuelles comme nombre attendu de participants.

Une alerte apparaît quand le taux moyen d’absence estimé atteint 30 %. L’organisateur peut envoyer, via `notifications.services`, un rappel aux seuls inscrits dont le risque individuel d’absence atteint ce seuil et qui n’ont pas déjà reçu un rappel. L’envoi respecte les préférences de notification existantes et marque le rappel comme envoyé.

## 5. Suggestions locales de catégorie et de tags

Sur le formulaire d’événement, cliquez sur « Suggérer une catégorie et des tags ». Le service local analyse le titre et la description avec un petit lexique français, puis propose une catégorie et des hashtags liés aux mots reconnus. Choisissez explicitement « Appliquer la catégorie » ou « Ajouter les tags » : les tags sont ajoutés à la description, qui reste modifiable et indexée par la recherche existante. Aucune migration, dépendance ou API externe n’est nécessaire.

Cette suggestion est déterministe et limitée à son vocabulaire ; un texte sans mots-clés connus ne produira pas de suggestion. Les propositions sont facultatives et doivent être relues par l’organisateur.
