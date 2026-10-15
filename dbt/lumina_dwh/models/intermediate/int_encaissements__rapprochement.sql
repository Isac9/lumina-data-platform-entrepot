-- Rapprochement : chaque paiement du logiciel de portefeuille
-- doit avoir son écriture dans l'ERP, avec le même montant.

select
    coalesce(r.id_remboursement, e.id_remboursement) as id_remboursement,
    e.num_piece,
    r.montant                                        as montant_portefeuille,
    e.montant                                        as montant_erp,
    e.compte_groupe,
    case
        when e.id_remboursement is null then 'ABSENT_ERP'
        when r.id_remboursement is null then 'ABSENT_PORTEFEUILLE'
        when r.montant <> e.montant     then 'ECART_MONTANT'
        else 'RAPPROCHE'
    end as statut_rapprochement
from {{ ref('stg_pf__remboursements') }} r
full outer join {{ ref('stg_erp__encaissements') }} e
    on e.id_remboursement = r.id_remboursement
