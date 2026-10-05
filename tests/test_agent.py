from unittest.mock import patch
import pytest
from app.agent import arbitrer_location

# 1. Jeux de données factices (Mocks)
DUMMY_EMBEDDING = [0.1] * 384

DUMMY_VEHICULES = [
    {
        "vehicule_id": 1,
        "marque": "Renault",
        "modele": "Clio 5",
        "categorie": "Citadine",
        "description": "Petite voiture économique",
        "prix_jour_eur": 35.0,
        "agence_nom": "DriveLocal Paris Centre",
        "ville": "Paris",
        "score_similarite": 0.85,
    },
    {
        "vehicule_id": 2,
        "marque": "Peugeot",
        "modele": "3008",
        "categorie": "SUV",
        "description": "SUV familial spacieux",
        "prix_jour_eur": 75.0,
        "agence_nom": "DriveLocal Paris Centre",
        "ville": "Paris",
        "score_similarite": 0.70,
    },
]

DUMMY_OPTIONS = [
    {
        "option_id": 1,
        "nom": "Siège bébé",
        "prix_jour_eur": 5.0,
        "description": "Siège adapté",
    }
]


# 2. Fixture automatique pour simuler HF et la BDD
@pytest.fixture(autouse=True)
def mock_external_services():
    with (
        patch("app.agent.get_embedding", return_value=DUMMY_EMBEDDING),
        patch(
            "app.agent.chercher_vehicules_vectoriel",
            return_value=DUMMY_VEHICULES,
        ),
        patch("app.agent.get_options", return_value=DUMMY_OPTIONS),
    ):
        yield


# 3. Tes tests
def test_arbitrage_dans_budget():
    """Vérifie qu'une demande raisonnable est acceptée directement."""
    res = arbitrer_location(
        besoin_texte="Une petite citadine économique pour la ville",
        ville="Paris",
        nb_jours=2,
        budget_max=300.0,
        options_souhaitees=[],
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
        options_souhaitees=[1],
    )
    assert res["status"] == "arbitrage_requis"
    assert "propositions" in res
    assert len(res["propositions"]) > 0