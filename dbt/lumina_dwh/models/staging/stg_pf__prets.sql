select
    id_pret,
    id_client,
    upper(trim(code_entite)) as code_entite,
    code_produit,
    date_decaissement,
    prix_vente,
    apport_initial,
    montant_finance,
    duree_mois,
    mensualite,
    statut                   as statut_source
from {{ source('raw', 'pf_prets') }}
