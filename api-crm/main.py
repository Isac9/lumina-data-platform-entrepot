"""
API du CRM (simulée) de Lumina Énergie.

Elle renvoie les agents commerciaux et les clients, PAGE PAR PAGE,
comme une vraie API d'entreprise (Salesforce, HubSpot, Zoho...).
Documentation interactive : http://localhost:8000/docs
"""

import json
import os

from fastapi import FastAPI, HTTPException, Query

DOSSIER_CRM = os.environ.get("DOSSIER_CRM", "/donnees/crm")

app = FastAPI(title="API CRM - Lumina Énergie (simulée)", version="1.0")


def charger(nom):
    chemin = os.path.join(DOSSIER_CRM, f"{nom}.json")
    if not os.path.exists(chemin):
        raise HTTPException(status_code=503, detail=f"Fichier {nom}.json introuvable : lancez le générateur.")
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def paginer(elements, entite, page, taille):
    if entite:
        elements = [e for e in elements if e["code_entite"] == entite.upper()]
    debut = (page - 1) * taille
    return {"page": page, "taille": taille, "total": len(elements), "donnees": elements[debut:debut + taille]}


@app.get("/sante")
def sante():
    return {"statut": "ok"}


@app.get("/agents")
def lister_agents(entite: str | None = None, page: int = Query(1, ge=1), taille: int = Query(500, ge=1, le=1000)):
    return paginer(charger("agents"), entite, page, taille)


@app.get("/clients")
def lister_clients(entite: str | None = None, page: int = Query(1, ge=1), taille: int = Query(500, ge=1, le=1000)):
    return paginer(charger("clients"), entite, page, taille)
