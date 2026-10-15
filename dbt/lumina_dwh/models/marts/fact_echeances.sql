-- Une ligne par échéance (mensualité prévue).
{{ config(
    post_hook="{{ appliquer_rls() }}",
    indexes=[{'columns': ['id_pret']}, {'columns': ['code_entite', 'date_echeance']}]
) }}

select
    e.id_echeance,
    e.id_pret,
    p.id_client,
    p.code_entite,
    p.code_produit,
    e.numero_echeance,
    e.date_echeance,
    e.montant_du,
    e.date_echeance <= current_date as est_echue
from {{ ref('stg_pf__echeances') }} e
join {{ ref('stg_pf__prets') }} p using (id_pret)
