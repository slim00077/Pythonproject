# Évaluation d'EcoPulse

## Jeu d'évaluation (`scenarios.json`)

7 scénarios environnementaux synthétiques (journée dégagée, canicule, tempête, air pollué, vent modéré, vague de froid,
données de qualité d'air manquantes). Chacun définit :

- les valeurs injectées (au format Open-Meteo) ;
- le résultat **attendu des règles** (`expected_outdoor`, niveaux par indicateur) — vérifiable automatiquement ;
- les **critères attendus de l'IA** : `valid_schema` (résumé + au moins une proposition), `no_official_alert_wording`
  (aucun « alerte »/« vigilance »), `no_outdoor_content` (aucune reco/mission extérieure si conditions déconseillées),
  `outdoor_allowed`, `mentions_unavailable_data` (signale les données manquantes).

## Exécution

```
python -m ecopulse.eval.run_eval
```

Le script écrit `results.json` avec **uniquement ce qui a réellement été mesuré**. Sans `GEMINI_API_KEY`/`GEMINI_MODEL`, seule la
partie règles est exécutée (`"ai_run": false`) : aucun résultat IA n'est alors enregistré ni inventé.

Les critères automatiques mesurent la structure et la sécurité. La **qualité rédactionnelle** (clarté, pertinence du défi,
ton) doit être relue par un humain : grille proposée, note de 0 à 2 par critère — (1) explique correctement les niveaux
fournis, (2) action adaptée aux conditions, (3) défi réaliste et sûr, (4) formulation prudente, non assimilable à une alerte.

## Mesures réalisées (machine de développement, 25/10/2026)

| Mesure | Résultat | Remarque |
|---|---|---|
| Règles, 7 scénarios | 7/7 conformes à l'attendu | ~0,06–0,1 ms par évaluation |
| Open-Meteo prévisions, 5 appels séquentiels | 0,30–0,75 s | série mesurée en premier |
| Open-Meteo qualité de l'air, 5 appels | 0,23–0,31 s | |
| Géocodage Open-Meteo (« Sfax ») | 0,29 s | |
| Récupération complète à froid (prévisions + air) | 4,7 s et 11,8 s (2 essais), 1,6–3,8 s (séquentiel, 3 essais) | **forte variabilité réseau**, constatée lors d'une 2ᵉ série |
| Page tableau de bord, 1ʳᵉ charge (données réelles) | 16,9 s (réseau lent ce jour-là) | |
| Page tableau de bord, chargement suivant (cache) | 0,017 s | |
| Analyse IA | **non mesurée** | aucune clé Gemini disponible lors du développement |

Décision d'architecture : la latence des fournisseurs est variable mais bornée (timeout 8 s) et neutralisée par le cache
(15 min, copie obsolète 6 h). L'appel IA, le plus long, est déjà asynchrone côté navigateur (requête `fetch` + état de
chargement) ; une file de tâches (Celery) n'est pas justifiée par ces mesures et n'existe pas dans l'architecture du projet.
À réévaluer après mesure de la latence IA réelle.
