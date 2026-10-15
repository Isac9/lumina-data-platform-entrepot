select
    id_client,
    upper(trim(code_entite))              as code_entite,
    initcap(trim(nom))                    as nom,
    initcap(trim(prenom))                 as prenom,
    regexp_replace(telephone, '\s', '', 'g') as telephone,
    trim(ville)                           as ville,
    date_inscription::date                as date_inscription,
    id_agent,
    segment,
    _charge_le
from {{ source('raw', 'crm_clients') }}
