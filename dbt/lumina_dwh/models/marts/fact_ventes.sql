-- Ventes comptabilisées dans l'ERP, ramenées au plan de comptes GROUPE
-- (permet la consolidation entre pays).
{{ config(post_hook="{{ appliquer_rls() }}") }}

select
    f.num_facture,
    f.code_entite,
    f.id_pret,
    p.code_produit,
    f.date_facture,
    f.code_compte_local,
    f.compte_groupe,
    f.montant_ht,
    f.montant_tva,
    f.montant_ttc
from {{ ref('stg_erp__factures') }} f
left join {{ ref('stg_pf__prets') }} p using (id_pret)
