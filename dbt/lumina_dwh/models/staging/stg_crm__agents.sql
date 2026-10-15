select
    id_agent,
    upper(trim(code_entite))   as code_entite,
    initcap(trim(nom))         as nom,
    initcap(trim(prenom))      as prenom,
    trim(zone)                 as zone,
    date_embauche::date        as date_embauche,
    _charge_le
from {{ source('raw', 'crm_agents') }}
