-- CONTRÔLE QUALITÉ : chaque paiement doit être présent dans l'ERP avec le même montant.
-- En "warn" (avertissement) : on signale les anomalies sans bloquer le pipeline.
{{ config(severity='warn') }}

select *
from {{ ref('int_encaissements__rapprochement') }}
where statut_rapprochement <> 'RAPPROCHE'
