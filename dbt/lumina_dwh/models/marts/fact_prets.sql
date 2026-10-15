-- Une ligne par prêt, avec sa situation à la date du jour.
{{ config(
    post_hook="{{ appliquer_rls() }}",
    indexes=[{'columns': ['id_pret'], 'unique': True}, {'columns': ['code_entite']}]
) }}

select
    s.id_pret,
    s.id_client,
    c.id_agent,
    s.code_entite,
    s.code_produit,
    s.date_decaissement,
    s.duree_mois,
    s.prix_vente,
    s.apport_initial,
    s.montant_finance,
    s.mensualite,
    s.total_du,
    s.du_a_date,
    s.total_rembourse,
    s.encours,
    s.montant_impaye,
    s.nb_echeances_echues,
    s.nb_paiements,
    s.date_dernier_paiement,
    s.date_derniere_echeance,
    case
        when s.encours = 0                 then 'SOLDE'
        when s.montant_impaye = 0          then 'A_JOUR'
        else 'EN_RETARD'
    end                                    as statut_pret,
    current_date                           as date_arrete
from {{ ref('int_prets__situation') }} s
left join {{ ref('stg_crm__clients') }} c using (id_client)
