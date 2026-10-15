-- Une ligne par paiement reçu, avec le résultat du rapprochement ERP.
{{ config(
    post_hook="{{ appliquer_rls() }}",
    indexes=[{'columns': ['id_pret']}, {'columns': ['code_entite', 'date_paiement']}]
) }}

select
    r.id_remboursement,
    r.id_pret,
    p.id_client,
    c.id_agent,
    p.code_entite,
    p.code_produit,
    r.date_paiement,
    r.montant,
    r.canal,
    r.famille_canal,
    rap.num_piece          as num_piece_erp,
    rap.montant_erp,
    rap.compte_groupe,
    rap.statut_rapprochement
from {{ ref('stg_pf__remboursements') }} r
join {{ ref('stg_pf__prets') }} p using (id_pret)
left join {{ ref('stg_crm__clients') }} c on c.id_client = p.id_client
left join {{ ref('int_encaissements__rapprochement') }} rap using (id_remboursement)
