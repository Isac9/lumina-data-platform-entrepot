-- CONTRÔLE QUALITÉ : le total remboursé dans fact_prets doit être égal
-- à la somme des paiements dans fact_remboursements, pour chaque entité.

with prets as (
    select code_entite, sum(total_rembourse) as total
    from {{ ref('fact_prets') }}
    group by code_entite
),
paiements as (
    select code_entite, sum(montant) as total
    from {{ ref('fact_remboursements') }}
    group by code_entite
)
select p.code_entite, p.total as total_prets, r.total as total_paiements
from prets p
full outer join paiements r using (code_entite)
where coalesce(p.total, 0) <> coalesce(r.total, 0)
