from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from app.agent import arbitrer_location

app = FastAPI(title="DriveLocal Agent API", version="0.1.0")

class DemandLocation(BaseModel):
    besoin_texte: str
    ville: str
    nb_jours: int
    budget_max: float
    options_ids: Optional[List[int]] = []

@app.get("/")
def read_root():
    return {"message": "DriveLocal Agent API est prête"}

@app.post("/api/arbitrer")
def api_arbitrer(demande: DemandLocation):
    resultat = arbitrer_location(
        besoin_texte=demande.besoin_texte,
        ville=demande.ville,
        nb_jours=demande.nb_jours,
        budget_max=demande.budget_max,
        options_souhaitees=demande.options_ids
    )
    return resultat