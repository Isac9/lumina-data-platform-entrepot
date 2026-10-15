select
    f.code_entite,
    f.num_facture,
    f.id_pret::integer                          as id_pret,
    {{ convertir_date_erp('f.date_facture') }}  as date_facture,
    f.code_compte                               as code_compte_local,
    c.compte_groupe,
    {{ convertir_montant_erp('f.montant_ht') }}  as montant_ht,
    {{ convertir_montant_erp('f.tva') }}         as montant_tva,
    {{ convertir_montant_erp('f.montant_ttc') }} as montant_ttc,
    f._fichier_source
from {{ source('raw', 'erp_factures') }} f
left join {{ ref('correspondance_comptes') }} c
    on c.code_entite = f.code_entite
   and c.code_compte_local = f.code_compte
