{{ config(
    post_hook="{{ appliquer_rls() }}",
    indexes=[{'columns': ['code_entite']}]
) }}

select
    c.id_client,
    c.code_entite,
    c.prenom || ' ' || c.nom                                  as nom_complet,
    c.telephone,
    c.ville,
    c.segment,
    c.date_inscription,
    (current_date - c.date_inscription) / 30                  as anciennete_mois,
    c.id_agent,
    a.prenom || ' ' || a.nom                                  as nom_agent
from {{ ref('stg_crm__clients') }} c
left join {{ ref('stg_crm__agents') }} a using (id_agent)
