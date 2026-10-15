# Architecture et choix techniques

## 1. Principes

1. **ELT plutôt qu'ETL** : on charge d'abord les données brutes, puis on transforme *dans* PostgreSQL avec dbt. Le SQL est versionné, testé et documenté, et l'on peut toujours revenir à la donnée brute.
2. **Une couche = un rôle** : `raw` (copie), `staging` (nettoyage), `intermediate` (logique métier), `marts` (consommation).
3. **Idempotence** : relancer le pipeline donne le même résultat, sans doublons.
4. **Sécurité au plus près de la donnée** : les droits sont posés dans PostgreSQL (RLS), pas seulement dans l'outil de BI.

## 2. Choix techniques

| Besoin | Choix | Pourquoi | Alternative envisagée |
|---|---|---|---|
| Entrepôt | PostgreSQL 16 | Exigé par le poste, robuste, gratuit, partitionnement natif | ClickHouse (plus rapide en analytique, mais une compétence de plus à maintenir) |
| Orchestration | Apache Airflow 2.10 | Standard du marché, retries, historique, alertes | Dagster, cron |
| Transformations | dbt-core 1.9 | SQL versionné, tests, documentation et lignage automatiques | Procédures stockées |
| Extraction API | Python + requests | Gère la pagination ; simple à faire évoluer | Airbyte (lourd pour 3 sources) |
| Conteneurs | Docker Compose | Reproductible sur tout poste | Kubernetes (surdimensionné) |

## 3. Gestion des différences entre pays

| | CI | SN | BF |
|---|---|---|---|
| Séparateur CSV | `;` | `,` | `;` |
| Format de date | `JJ/MM/AAAA` | `AAAA-MM-JJ` | `JJ/MM/AAAA` |
| Montants | `125000` | `125000` | `125 000` |
| Compte de ventes | 706100 | 7061 | 70610 |

- Les séparateurs sont gérés à l'extraction (`SEPARATEURS_ERP`).
- Les dates et montants sont gérés dans dbt (macros `convertir_date_erp` et `convertir_montant_erp`).
- Les comptes sont gérés par le référentiel `correspondance_comptes`, qui ramène chaque compte local au **plan de comptes Groupe**. Un test `not_null` sur `compte_groupe` bloque tout compte local inconnu.

## 4. Sécurité

| Rôle | Voit |
|---|---|
| `direction_groupe` | toutes les entités |
| `lecteur_ci` / `lecteur_sn` / `lecteur_bf` | uniquement les lignes de son pays |

La règle (policy) est posée automatiquement par dbt après chaque reconstruction de table (macro `appliquer_rls`).

## 5. Exploitation

- **Planification** : tous les jours à 5h00, avec une nouvelle tentative automatique en cas d'échec.
- **Sauvegarde** : `pg_dump` au format custom, une fois par jour, conservé 7 jours.
- **Contrôles qualité** : bloquants pour l'intégrité (clés, relations) ; en avertissement pour le rapprochement ERP (une anomalie est signalée sans bloquer le reporting).
