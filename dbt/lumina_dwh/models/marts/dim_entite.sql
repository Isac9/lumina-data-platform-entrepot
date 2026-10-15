select
    code_entite,
    nom_entite,
    pays,
    ville_siege,
    devise,
    date_creation
from {{ ref('entites') }}
