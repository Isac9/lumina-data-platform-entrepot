-- CONTRÔLE QUALITÉ : aucun paiement ni échéance ne doit avoir un montant <= 0.

select 'remboursement' as type_ligne, id_remboursement as id, montant
from {{ ref('fact_remboursements') }}
where montant <= 0

union all

select 'echeance', id_echeance, montant_du
from {{ ref('fact_echeances') }}
where montant_du <= 0
