# Feuille de route du dispositif data

| Phase | Horizon | Livrables | Statut |
|---|---|---|---|
| **1. Socle** | Mois 1-2 | Entrepôt PostgreSQL, pipelines ELT des 3 sources, modèle en étoile, RLS, sauvegardes, tests qualité | Fait (ce projet) |
| **2. Pilotage** | Mois 2-4 | Indicateurs de crédit (PAR 30/60/90/120, recouvrement, provisions), tableaux de bord Superset par entité et consolidés Groupe, reporting institutionnel | Projet 2 |
| **3. Aide à la décision** | Mois 4-6 | Scoring de risque, prévision des encaissements, détection d'anomalies | Projet 3 |
| **4. Gouvernance** | En continu | Dictionnaire des indicateurs, catalogue de données, matrice des droits, tableau de bord qualité | Projet 3 |
| **5. Industrialisation** | Mois 6+ | Chargements incrémentaux, CI/CD (GitHub Actions + `dbt build`), alertes Slack ou email, environnements dev et prod séparés, secrets dans un coffre | À venir |

## Améliorations identifiées

- Passer `raw.pf_remboursements` en **chargement incrémental** (filtre sur la date de mise à jour) quand les volumes augmenteront.
- Historiser les changements des clients (agent, ville) avec des **snapshots dbt** (SCD type 2).
- Ajouter **la source des opérations de terrain** (installations, SAV).
- Remplacer les mots de passe en clair par des **secrets** (fichier `.env` non versionné, puis un coffre-fort).
