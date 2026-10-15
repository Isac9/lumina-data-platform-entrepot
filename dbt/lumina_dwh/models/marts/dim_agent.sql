{{ config(post_hook="{{ appliquer_rls() }}") }}

select
    id_agent,
    code_entite,
    prenom || ' ' || nom as nom_complet,
    zone,
    date_embauche
from {{ ref('stg_crm__agents') }}
