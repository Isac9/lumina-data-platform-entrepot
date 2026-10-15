-- =====================================================================
--  Initialisation de l'entrepôt "dwh"
--  Ce script s'exécute UNE SEULE FOIS, au tout premier démarrage.
-- =====================================================================

-- ---------------------------------------------------------------
-- 1) Les "rayons" de l'entrepôt (schémas)
--    raw          : données brutes copiées des sources, sans retouche
--    staging      : données nettoyées (créé par dbt)
--    intermediate : calculs intermédiaires (créé par dbt)
--    marts        : tables finales prêtes pour les tableaux de bord
--    referentiel  : tables de référence (entités, plan de comptes)
-- ---------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS marts;

-- ---------------------------------------------------------------
-- 2) Les utilisateurs "lecteurs" et leurs droits
--    - direction_groupe voit TOUTES les entités
--    - lecteur_ci / lecteur_sn / lecteur_bf voient seulement LEUR pays
--    (le filtrage ligne par ligne = Row-Level Security, posé par dbt)
-- ---------------------------------------------------------------
CREATE ROLE direction_groupe LOGIN PASSWORD 'groupe123';
CREATE ROLE lecteur_ci LOGIN PASSWORD 'ci123';
CREATE ROLE lecteur_sn LOGIN PASSWORD 'sn123';
CREATE ROLE lecteur_bf LOGIN PASSWORD 'bf123';

GRANT USAGE ON SCHEMA marts TO direction_groupe, lecteur_ci, lecteur_sn, lecteur_bf;

-- ---------------------------------------------------------------
-- 3) Tables BRUTES (raw) - une par flux source
--    _charge_le = date/heure du chargement (traçabilité)
-- ---------------------------------------------------------------

-- CRM (API)
CREATE TABLE raw.crm_agents (
    id_agent        integer,
    code_entite     text,
    nom             text,
    prenom          text,
    zone            text,
    date_embauche   text,
    _charge_le      timestamptz DEFAULT now()
);

CREATE TABLE raw.crm_clients (
    id_client        integer,
    code_entite      text,
    nom              text,
    prenom           text,
    telephone        text,
    ville            text,
    date_inscription text,
    id_agent         integer,
    segment          text,
    _charge_le       timestamptz DEFAULT now()
);

-- Gestion de portefeuille (base PostgreSQL source)
CREATE TABLE raw.pf_produits (
    code_produit  text,
    libelle       text,
    prix_xof      numeric,
    _charge_le    timestamptz DEFAULT now()
);

CREATE TABLE raw.pf_prets (
    id_pret           integer,
    id_client         integer,
    code_entite       text,
    code_produit      text,
    date_decaissement date,
    prix_vente        numeric,
    apport_initial    numeric,
    montant_finance   numeric,
    duree_mois        integer,
    mensualite        numeric,
    statut            text,
    _charge_le        timestamptz DEFAULT now()
);

CREATE TABLE raw.pf_echeances (
    id_echeance    integer,
    id_pret        integer,
    numero         integer,
    date_echeance  date,
    montant_du     numeric,
    _charge_le     timestamptz DEFAULT now()
);

-- Table PARTITIONNÉE par mois : chaque mois est rangé dans son propre "tiroir".
-- Une requête sur un mois ne lit que ce tiroir => beaucoup plus rapide.
CREATE TABLE raw.pf_remboursements (
    id_remboursement integer,
    id_pret          integer,
    date_paiement    date NOT NULL,
    montant          numeric,
    canal            text,
    _charge_le       timestamptz DEFAULT now()
) PARTITION BY RANGE (date_paiement);

DO $$
DECLARE
    debut date := date '2023-01-01';
BEGIN
    WHILE debut < date '2028-01-01' LOOP
        EXECUTE format(
            'CREATE TABLE raw.pf_remboursements_%s PARTITION OF raw.pf_remboursements
             FOR VALUES FROM (%L) TO (%L)',
            to_char(debut, 'YYYY_MM'), debut, (debut + interval '1 month')::date
        );
        debut := (debut + interval '1 month')::date;
    END LOOP;
END $$;

-- Tiroir "fourre-tout" pour les dates hors plage (sécurité)
CREATE TABLE raw.pf_remboursements_autres PARTITION OF raw.pf_remboursements DEFAULT;

CREATE INDEX ON raw.pf_remboursements (id_pret);
CREATE INDEX ON raw.pf_echeances (id_pret);

-- ERP (fichiers CSV) : tout est stocké en TEXTE, car chaque pays
-- a son propre format (séparateur, dates, montants). On convertit dans dbt.
CREATE TABLE raw.erp_factures (
    code_entite     text,
    num_facture     text,
    id_pret         text,
    date_facture    text,
    code_compte     text,
    montant_ht      text,
    tva             text,
    montant_ttc     text,
    _fichier_source text,
    _charge_le      timestamptz DEFAULT now()
);

CREATE TABLE raw.erp_encaissements (
    code_entite     text,
    num_piece       text,
    ref_paiement    text,
    date_piece      text,
    code_compte     text,
    montant         text,
    _fichier_source text,
    _charge_le      timestamptz DEFAULT now()
);
