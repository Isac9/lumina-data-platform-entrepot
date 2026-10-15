select
    code_produit,
    libelle,
    prix_xof,
    case
        when code_produit like 'KIT-%' then 'Kit solaire'
        when code_produit = 'POMPE'    then 'Équipement agricole'
        else 'Cuisson'
    end as gamme
from {{ ref('stg_pf__produits') }}
