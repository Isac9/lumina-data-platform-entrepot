select
    e.code_entite,
    e.num_piece,
    e.ref_paiement::integer                   as id_remboursement,
    {{ convertir_date_erp('e.date_piece') }}  as date_piece,
    e.code_compte                             as code_compte_local,
    c.compte_groupe,
    {{ convertir_montant_erp('e.montant') }}  as montant,
    e._fichier_source
from {{ source('raw', 'erp_encaissements') }} e
left join {{ ref('correspondance_comptes') }} c
    on c.code_entite = e.code_entite
   and c.code_compte_local = e.code_compte
