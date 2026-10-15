select
    id_echeance,
    id_pret,
    numero        as numero_echeance,
    date_echeance,
    montant_du
from {{ source('raw', 'pf_echeances') }}
