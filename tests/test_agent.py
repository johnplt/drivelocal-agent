import pytest
from app.agent import arbitrer_location

def test_arbitrage_dans_budget():
    """Vérifie qu'une demande raisonnable est acceptée directement."""
    res = arbitrer_location(
        besoin_texte="Une petite citadine économique pour la ville",
        ville="Paris",
        nb_jours=2,
        budget_max=300.0,
        options_souhaitees=[]
    )
    assert res["status"] == "ok"
    assert "offre_retenue" in res
    assert res["prix_total_eur"] <= 300.0

def test_arbitrage_depassement_budget():
    """Vérifie que la logique d'arbitrage génère des propositions si le budget est trop bas."""
    res = arbitrer_location(
        besoin_texte="Grand SUV familial très haut de gamme",
        ville="Paris",
        nb_jours=5,
        budget_max=100.0,  # Insuffisant pour 5 jours de SUV
        options_souhaitees=[1]
    )
    assert res["status"] == "arbitrage_requis"
    assert "propositions" in res
    assert len(res["propositions"]) > 0