select
    id_remboursement,
    id_pret,
    date_paiement,
    montant,
    canal,
    case
        when canal in ('Orange Money', 'MTN MoMo', 'Wave', 'Moov Money', 'Free Money') then 'Mobile money'
        else 'Banque / espèces'
    end as famille_canal
from {{ source('raw', 'pf_remboursements') }}
