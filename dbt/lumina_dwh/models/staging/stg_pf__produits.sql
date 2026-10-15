select
    code_produit,
    libelle,
    prix_xof
from {{ source('raw', 'pf_produits') }}
