-- Situation de chaque prêt à la date du jour :
-- combien a été payé, combien reste à payer, combien est en retard.

with paiements as (
    select
        id_pret,
        sum(montant)       as total_rembourse,
        count(*)           as nb_paiements,
        max(date_paiement) as date_dernier_paiement
    from {{ ref('stg_pf__remboursements') }}
    group by id_pret
),

echeancier as (
    select
        id_pret,
        sum(montant_du)                                              as total_du,
        sum(montant_du) filter (where date_echeance <= current_date) as du_a_date,
        count(*) filter (where date_echeance <= current_date)        as nb_echeances_echues,
        max(date_echeance)                                           as date_derniere_echeance
    from {{ ref('stg_pf__echeances') }}
    group by id_pret
)

select
    p.*,
    coalesce(pa.total_rembourse, 0)                                     as total_rembourse,
    coalesce(pa.nb_paiements, 0)                                        as nb_paiements,
    pa.date_dernier_paiement,
    e.total_du,
    coalesce(e.du_a_date, 0)                                            as du_a_date,
    e.nb_echeances_echues,
    e.date_derniere_echeance,
    greatest(e.total_du - coalesce(pa.total_rembourse, 0), 0)            as encours,
    greatest(coalesce(e.du_a_date, 0) - coalesce(pa.total_rembourse, 0), 0) as montant_impaye
from {{ ref('stg_pf__prets') }} p
left join paiements pa using (id_pret)
left join echeancier e using (id_pret)
