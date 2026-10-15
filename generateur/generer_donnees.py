"""
Générateur de données FICTIVES pour le groupe fictif « Lumina Énergie ».

Lumina Énergie vend des équipements solaires payés à crédit (mensualités)
dans 3 pays : Côte d'Ivoire (CI), Sénégal (SN) et Burkina Faso (BF).

Ce script fabrique 3 sources, comme dans une vraie entreprise :
  1. CRM            -> fichiers JSON (servis ensuite par une API)
  2. Portefeuille   -> base PostgreSQL "portefeuille" (prêts, échéances, remboursements)
  3. ERP            -> fichiers CSV, un dossier par pays, chacun avec SON format
"""

import csv
import json
import os
import random
import time
from datetime import date, timedelta

import psycopg2
from psycopg2.extras import execute_values

random.seed(42)  # mêmes données à chaque exécution
AUJOURDHUI = date.today()
DEBUT_ACTIVITE = date(2024, 1, 1)
DOSSIER = os.environ.get("DOSSIER_DONNEES", "/donnees")

CONNEXION_SOURCES = dict(
    host=os.environ.get("SOURCES_HOTE", "localhost"),
    port=int(os.environ.get("SOURCES_PORT", "5432")),
    dbname="portefeuille",
    user="portefeuille_app",
    password="portefeuille",
)

PRENOMS = [
    "Aminata", "Fatou", "Awa", "Mariam", "Adjoua", "Akissi", "Aya", "Aïcha",
    "Rokia", "Salimata", "Ndeye", "Khady", "Moussa", "Ibrahim", "Seydou",
    "Mamadou", "Issa", "Koffi", "Kouadio", "Yves", "Serge", "Abdoulaye",
    "Ousmane", "Boubacar", "Cheikh", "Modou", "Adama", "Lassina", "Rasmané",
    "Inoussa", "Clarisse", "Estelle", "Brice", "Hervé", "Nafissatou",
]

ENTITES = {
    "CI": {
        "nb_clients": 800,
        "villes": ["Abidjan", "Bouaké", "Yamoussoukro", "Daloa", "San-Pédro", "Korhogo"],
        "noms": ["Kouassi", "Koné", "Traoré", "Yao", "N'Guessan", "Bamba", "Ouattara",
                 "Kouamé", "Coulibaly", "Diabaté", "Konan", "Aka", "Brou", "Touré", "Dosso"],
        "canaux": {"Orange Money": 35, "MTN MoMo": 25, "Wave": 25, "Moov Money": 10, "Espèces agence": 5},
        # Format des fichiers ERP propres à ce pays
        "erp": {"separateur": ";", "format_date": "%d/%m/%Y", "milliers_espace": False},
        "comptes": {"vente": "706100", "banque": "521100", "mobile": "585100"},
    },
    "SN": {
        "nb_clients": 500,
        "villes": ["Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Touba"],
        "noms": ["Diop", "Ndiaye", "Fall", "Sow", "Diallo", "Ba", "Sy", "Gueye",
                 "Faye", "Mbaye", "Sarr", "Cissé", "Thiam", "Niang", "Seck"],
        "canaux": {"Wave": 45, "Orange Money": 35, "Free Money": 10, "Virement bancaire": 10},
        "erp": {"separateur": ",", "format_date": "%Y-%m-%d", "milliers_espace": False},
        "comptes": {"vente": "7061", "banque": "5211", "mobile": "5851"},
    },
    "BF": {
        "nb_clients": 400,
        "villes": ["Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Banfora", "Ouahigouya"],
        "noms": ["Ouédraogo", "Sawadogo", "Zongo", "Kinda", "Nikiéma", "Ilboudo",
                 "Zoungrana", "Tapsoba", "Kaboré", "Sanou", "Traoré", "Compaoré"],
        "canaux": {"Orange Money": 55, "Moov Money": 35, "Espèces agence": 10},
        "erp": {"separateur": ";", "format_date": "%d/%m/%Y", "milliers_espace": True},
        "comptes": {"vente": "70610", "banque": "52110", "mobile": "58510"},
    },
}

# code, libellé, prix en FCFA (XOF), durées possibles (mois), poids de vente
PRODUITS = [
    ("KIT-S", "Kit solaire S (3 lampes + radio)", 90_000, [6], 35),
    ("KIT-M", "Kit solaire M (5 lampes + TV 24 pouces)", 250_000, [12], 30),
    ("KIT-L", "Kit solaire L (8 lampes + TV 32 pouces + frigo)", 650_000, [12, 18], 10),
    ("FOYER", "Foyer de cuisson amélioré", 35_000, [6], 15),
    ("POMPE", "Pompe solaire agricole", 900_000, [18, 24], 10),
]
CANAUX_MOBILE = {"Orange Money", "MTN MoMo", "Wave", "Moov Money", "Free Money"}


# ----------------------------------------------------------------- outils
def date_au_hasard(debut, fin):
    if fin <= debut:
        return debut
    return debut + timedelta(days=random.randint(0, (fin - debut).days))


def ajouter_mois(d, n):
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, min(d.day, 28))


def arrondi_100(x):
    return int(round(x / 100.0)) * 100


def telephone(code):
    if code == "CI":
        return "+225 0" + random.choice("157") + " " + " ".join(f"{random.randint(0, 99):02d}" for _ in range(4))
    if code == "SN":
        return f"+221 7{random.choice('678')} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"
    return f"+226 {random.choice(['70', '76', '65', '05'])} " + " ".join(f"{random.randint(0, 99):02d}" for _ in range(3))


def retard_selon_profil(profil):
    """Nombre de jours de retard d'un paiement selon le comportement du client."""
    if profil == "bon":
        if random.random() < 0.03:
            return random.randint(30, 45)
        return random.choice([-3, -1, 0, 0, 0, 1, 2, 5])
    if profil == "retard":
        return random.choices([0, 10, 25, 45, 75, 100, 140], [25, 20, 20, 15, 10, 5, 5])[0]
    return random.randint(0, 20)  # "defaut", avant d'arrêter de payer


# ----------------------------------------------------------------- génération
def generer():
    agents, clients, prets, echeances, remboursements = [], [], [], [], []
    ids = {"agent": 0, "client": 0, "pret": 0, "echeance": 0, "remboursement": 0}

    for code, ent in ENTITES.items():
        # --- Agents commerciaux (10 par pays)
        agents_pays = []
        for _ in range(10):
            ids["agent"] += 1
            a = {
                "id_agent": ids["agent"],
                "code_entite": code,
                "nom": random.choice(ent["noms"]),
                "prenom": random.choice(PRENOMS),
                "zone": random.choice(ent["villes"]),
                "date_embauche": str(date_au_hasard(date(2022, 1, 1), date(2024, 6, 30))),
            }
            agents.append(a)
            agents_pays.append(a)

        # --- Clients et leurs prêts
        for _ in range(ent["nb_clients"]):
            ids["client"] += 1
            agent = random.choice(agents_pays)
            segment = random.choices(["Particulier", "Commerçant", "Agriculteur"], [80, 12, 8])[0]
            date_inscription = date_au_hasard(date(2023, 10, 1), AUJOURDHUI - timedelta(days=45))
            clients.append({
                "id_client": ids["client"],
                "code_entite": code,
                "nom": random.choice(ent["noms"]),
                "prenom": random.choice(PRENOMS),
                "telephone": telephone(code),
                "ville": agent["zone"] if random.random() < 0.8 else random.choice(ent["villes"]),
                "date_inscription": str(date_inscription),
                "id_agent": agent["id_agent"],
                "segment": segment,
            })

            profil = random.choices(["bon", "retard", "defaut"], [70, 20, 10])[0]
            date_min = max(date_inscription, DEBUT_ACTIVITE)
            nb_prets = 1 if random.random() < 0.8 else 2

            for _ in range(nb_prets):
                if date_min > AUJOURDHUI - timedelta(days=20):
                    break
                poids = [p[4] for p in PRODUITS]
                if segment == "Agriculteur":
                    poids = [10, 10, 5, 5, 70]
                code_produit, _, prix, durees, _ = random.choices(PRODUITS, poids)[0]
                duree = random.choice(durees)
                date_decaissement = date_au_hasard(date_min, AUJOURDHUI - timedelta(days=20))
                apport = arrondi_100(prix * 0.10)
                montant_finance = arrondi_100((prix - apport) * (1 + 0.015 * duree))
                mensualite = arrondi_100(montant_finance / duree)

                ids["pret"] += 1
                id_pret = ids["pret"]
                seuil_defaut = random.randint(1, max(1, duree // 2))
                total_paye = 0

                for n in range(1, duree + 1):
                    ids["echeance"] += 1
                    date_echeance = ajouter_mois(date_decaissement, n)
                    montant_du = mensualite if n < duree else montant_finance - mensualite * (duree - 1)
                    echeances.append((ids["echeance"], id_pret, n, date_echeance, montant_du))

                    if date_echeance > AUJOURDHUI:
                        continue  # pas encore à payer
                    if profil == "defaut" and n > seuil_defaut:
                        continue  # le client a arrêté de payer
                    date_paiement = date_echeance + timedelta(days=retard_selon_profil(profil))
                    if date_paiement > AUJOURDHUI:
                        continue  # paiement en retard, pas encore reçu
                    montant = montant_du
                    if profil == "retard" and random.random() < 0.10:
                        montant = arrondi_100(montant_du / 2)  # paiement partiel
                    canal = random.choices(list(ent["canaux"]), list(ent["canaux"].values()))[0]
                    ids["remboursement"] += 1
                    remboursements.append((ids["remboursement"], id_pret, date_paiement, montant, canal))
                    total_paye += montant

                statut = "SOLDE" if total_paye >= montant_finance else "EN_COURS"
                prets.append((id_pret, clients[-1]["id_client"], code, code_produit, date_decaissement,
                              prix, apport, montant_finance, duree, mensualite, statut))
                date_min = date_decaissement + timedelta(days=60)

    return agents, clients, prets, echeances, remboursements


# ----------------------------------------------------------------- écriture
def ecrire_crm(agents, clients):
    dossier = os.path.join(DOSSIER, "crm")
    os.makedirs(dossier, exist_ok=True)
    for nom, contenu in (("agents", agents), ("clients", clients)):
        with open(os.path.join(dossier, f"{nom}.json"), "w", encoding="utf-8") as f:
            json.dump(contenu, f, ensure_ascii=False, indent=1)


def ecrire_portefeuille(prets, echeances, remboursements):
    for essai in range(30):
        try:
            conn = psycopg2.connect(**CONNEXION_SOURCES)
            break
        except psycopg2.OperationalError:
            print("Base source pas encore prête, nouvel essai dans 2 s...")
            time.sleep(2)
    else:
        raise SystemExit("Impossible de joindre la base source.")

    with conn, conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS remboursements, echeances, prets, produits CASCADE;
            CREATE TABLE produits (
                code_produit text PRIMARY KEY,
                libelle      text NOT NULL,
                prix_xof     numeric(14,0) NOT NULL
            );
            CREATE TABLE prets (
                id_pret           integer PRIMARY KEY,
                id_client         integer NOT NULL,
                code_entite       char(2) NOT NULL,
                code_produit      text REFERENCES produits,
                date_decaissement date NOT NULL,
                prix_vente        numeric(14,0),
                apport_initial    numeric(14,0),
                montant_finance   numeric(14,0),
                duree_mois        integer,
                mensualite        numeric(14,0),
                statut            text
            );
            CREATE TABLE echeances (
                id_echeance   integer PRIMARY KEY,
                id_pret       integer REFERENCES prets,
                numero        integer,
                date_echeance date,
                montant_du    numeric(14,0)
            );
            CREATE TABLE remboursements (
                id_remboursement integer PRIMARY KEY,
                id_pret          integer REFERENCES prets,
                date_paiement    date,
                montant          numeric(14,0),
                canal            text
            );
        """)
        execute_values(cur, "INSERT INTO produits VALUES %s", [p[:3] for p in PRODUITS])
        execute_values(cur, "INSERT INTO prets VALUES %s", prets, page_size=1000)
        execute_values(cur, "INSERT INTO echeances VALUES %s", echeances, page_size=1000)
        execute_values(cur, "INSERT INTO remboursements VALUES %s", remboursements, page_size=1000)
    conn.close()


def formater_montant(valeur, milliers_espace):
    return f"{int(valeur):,}".replace(",", " ") if milliers_espace else str(int(valeur))


def ecrire_erp(prets, remboursements):
    """Un dossier par pays. Volontairement, environ 0,5 % des encaissements
    sont ABSENTS de l'ERP et 0,3 % ont un MONTANT FAUX : le pipeline devra
    les détecter (rapprochement ERP <-> portefeuille)."""
    pret_par_id = {p[0]: p for p in prets}
    for code, ent in ENTITES.items():
        fmt = ent["erp"]
        dossier = os.path.join(DOSSIER, "erp", code)
        os.makedirs(dossier, exist_ok=True)
        sep, fdate, esp = fmt["separateur"], fmt["format_date"], fmt["milliers_espace"]

        with open(os.path.join(dossier, f"factures_{code}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=sep)
            w.writerow(["num_facture", "id_pret", "date_facture", "code_compte", "montant_ht", "tva", "montant_ttc"])
            for p in prets:
                if p[2] != code:
                    continue
                ttc = p[6] + p[7]  # apport + montant financé
                ht = round(ttc / 1.18)
                w.writerow([f"FA-{code}-{p[4].year}-{p[0]:06d}", p[0], p[4].strftime(fdate), ent["comptes"]["vente"],
                            formater_montant(ht, esp), formater_montant(ttc - ht, esp), formater_montant(ttc, esp)])

        with open(os.path.join(dossier, f"encaissements_{code}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=sep)
            w.writerow(["num_piece", "ref_paiement", "date_piece", "code_compte", "montant"])
            for r in remboursements:
                if pret_par_id[r[1]][2] != code:
                    continue
                tirage = random.random()
                if tirage < 0.005:
                    continue  # oubli de saisie dans l'ERP
                montant = r[3] + (random.choice([-500, 500]) if tirage < 0.008 else 0)
                compte = ent["comptes"]["mobile"] if r[4] in CANAUX_MOBILE else ent["comptes"]["banque"]
                w.writerow([f"EN-{code}-{r[0]:07d}", r[0], r[2].strftime(fdate), compte, formater_montant(montant, esp)])


if __name__ == "__main__":
    print(f"Génération des données (date du jour : {AUJOURDHUI})...")
    agents, clients, prets, echeances, remboursements = generer()
    ecrire_crm(agents, clients)
    ecrire_portefeuille(prets, echeances, remboursements)
    ecrire_erp(prets, remboursements)
    print(f"OK : {len(agents)} agents, {len(clients)} clients, {len(prets)} prêts, "
          f"{len(echeances)} échéances, {len(remboursements)} remboursements.")
