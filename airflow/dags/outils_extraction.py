"""
Fonctions d'EXTRACTION + CHARGEMENT (le "EL" de ELT).

Chaque fonction lit une source et recopie les données TELLES QUELLES
dans le schéma "raw" de l'entrepôt. La transformation (le "T") est faite
ensuite par dbt.

Stratégie : rechargement complet (TRUNCATE puis INSERT).
=> on peut relancer le pipeline autant de fois qu'on veut, sans doublons.
"""

import csv
import glob
import logging
import os

import requests
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_values

log = logging.getLogger(__name__)

API_CRM = os.environ.get("API_CRM_URL", "http://api-crm:8000")
DOSSIER_ERP = os.environ.get("DOSSIER_ERP", "/opt/donnees/erp")

# Chaque pays envoie ses CSV avec son propre séparateur
SEPARATEURS_ERP = {"CI": ";", "SN": ",", "BF": ";"}


def remplacer_table(table, colonnes, lignes):
    """Vide la table brute puis la recharge, en une seule transaction."""
    conn = PostgresHook(postgres_conn_id="dwh").get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table}")
            if lignes:
                execute_values(
                    cur,
                    f"INSERT INTO {table} ({', '.join(colonnes)}) VALUES %s",
                    lignes,
                    page_size=1000,
                )
    finally:
        conn.close()
    log.info("%s : %s lignes chargées", table, len(lignes))
    return len(lignes)


# ------------------------------------------------------------------ CRM (API)
def lire_api_paginee(chemin):
    page, resultats = 1, []
    while True:
        reponse = requests.get(f"{API_CRM}{chemin}", params={"page": page, "taille": 500}, timeout=30)
        reponse.raise_for_status()
        corps = reponse.json()
        resultats.extend(corps["donnees"])
        if page * corps["taille"] >= corps["total"]:
            return resultats
        page += 1


def charger_crm():
    colonnes_agents = ["id_agent", "code_entite", "nom", "prenom", "zone", "date_embauche"]
    colonnes_clients = ["id_client", "code_entite", "nom", "prenom", "telephone",
                        "ville", "date_inscription", "id_agent", "segment"]
    agents = lire_api_paginee("/agents")
    clients = lire_api_paginee("/clients")
    return {
        "agents": remplacer_table("raw.crm_agents", colonnes_agents,
                                  [tuple(a[c] for c in colonnes_agents) for a in agents]),
        "clients": remplacer_table("raw.crm_clients", colonnes_clients,
                                   [tuple(c[k] for k in colonnes_clients) for c in clients]),
    }


# ------------------------------------------------ Portefeuille (base PostgreSQL)
TABLES_PORTEFEUILLE = {
    "produits": ["code_produit", "libelle", "prix_xof"],
    "prets": ["id_pret", "id_client", "code_entite", "code_produit", "date_decaissement",
              "prix_vente", "apport_initial", "montant_finance", "duree_mois", "mensualite", "statut"],
    "echeances": ["id_echeance", "id_pret", "numero", "date_echeance", "montant_du"],
    "remboursements": ["id_remboursement", "id_pret", "date_paiement", "montant", "canal"],
}


def charger_portefeuille():
    source = PostgresHook(postgres_conn_id="sources_portefeuille")
    resultat = {}
    for table, colonnes in TABLES_PORTEFEUILLE.items():
        lignes = source.get_records(f"SELECT {', '.join(colonnes)} FROM {table}")
        resultat[table] = remplacer_table(f"raw.pf_{table}", colonnes, lignes)
    return resultat


# ------------------------------------------------------------- ERP (fichiers CSV)
def lire_csv_erp(motif):
    lignes = []
    for chemin in sorted(glob.glob(os.path.join(DOSSIER_ERP, "*", motif))):
        code_entite = os.path.basename(os.path.dirname(chemin))
        with open(chemin, encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f, delimiter=SEPARATEURS_ERP[code_entite]):
                lignes.append((code_entite, ligne, os.path.basename(chemin)))
    return lignes


def charger_erp():
    col_factures = ["num_facture", "id_pret", "date_facture", "code_compte", "montant_ht", "tva", "montant_ttc"]
    col_encaissements = ["num_piece", "ref_paiement", "date_piece", "code_compte", "montant"]
    factures = [(e, *[l[c] for c in col_factures], f) for e, l, f in lire_csv_erp("factures_*.csv")]
    encaissements = [(e, *[l[c] for c in col_encaissements], f) for e, l, f in lire_csv_erp("encaissements_*.csv")]
    return {
        "factures": remplacer_table("raw.erp_factures",
                                    ["code_entite", *col_factures, "_fichier_source"], factures),
        "encaissements": remplacer_table("raw.erp_encaissements",
                                         ["code_entite", *col_encaissements, "_fichier_source"], encaissements),
    }
