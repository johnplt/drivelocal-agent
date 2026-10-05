import os
from huggingface_hub import InferenceClient
from app.database import chercher_vehicules_vectoriel, get_options

HF_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialisation du client Inference Hugging Face
hf_client = InferenceClient(token=HF_TOKEN)

def get_embedding(text: str) -> list[float]:
    """Génère un embedding vectoriel via le SDK Hugging Face."""
    embedding = hf_client.feature_extraction(text, model=HF_MODEL)
    
    # Conversion du retour NumPy/Tensor en liste standard Python si nécessaire
    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()
        
    # Extraction si le résultat est dans une liste imbriquée [[...]]
    if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
        return embedding[0]
        
    return embedding

def arbitrer_location(besoin_texte: str, ville: str, nb_jours: int, budget_max: float, options_souhaitees: list[int] = None):
    options_souhaitees = options_souhaitees or []
    
    # 1. Génération de l'embedding via Hugging Face SDK
    user_emb = get_embedding(besoin_texte)
    
    # 2. Recherche vectorielle
    offres = chercher_vehicules_vectoriel(user_emb, ville)
    options_dispos = get_options()
    
    opts_retenues = [o for o in options_dispos if o["option_id"] in options_souhaitees]
    cout_options_jour = sum(o["prix_jour_eur"] for o in opts_retenues)
    
    if not offres:
        return {"status": "erreur", "message": f"Aucun véhicule disponible à {ville}."}

    meilleure_offre = offres[0]
    prix_total_estime = (meilleure_offre["prix_jour_eur"] + cout_options_jour) * nb_jours

    if prix_total_estime <= budget_max:
        return {
            "status": "ok",
            "message": "L'offre correspond parfaitement à vos critères et entre dans votre budget.",
            "offre_retenue": meilleure_offre,
            "options": opts_retenues,
            "prix_total_eur": prix_total_estime,
            "economie_eur": round(budget_max - prix_total_estime, 2)
        }

    depassement = prix_total_estime - budget_max
    propositions_arbitrage = []

    prix_max_vehicule_jour = (budget_max / nb_jours) - cout_options_jour
    if prix_max_vehicule_jour > 0:
        offres_eco = chercher_vehicules_vectoriel(user_emb, ville, max_prix_jour=prix_max_vehicule_jour)
        if offres_eco:
            alt = offres_eco[0]
            propositions_arbitrage.append({
                "type": "CHANGEMENT_VEHICULE",
                "titre": f"Passer sur la {alt['marque']} {alt['modele']}",
                "nouveau_prix_total": round((alt["prix_jour_eur"] + cout_options_jour) * nb_jours, 2),
                "detail": f"Économie de {round((meilleure_offre['prix_jour_eur'] - alt['prix_jour_eur']) * nb_jours, 2)}€ en choisissant la catégorie {alt['categorie']}."
            })

    if opts_retenues:
        prix_sans_options = meilleure_offre["prix_jour_eur"] * nb_jours
        if prix_sans_options <= budget_max:
            propositions_arbitrage.append({
                "type": "RETRAIT_OPTIONS",
                "titre": "Retirer certaines options payantes",
                "nouveau_prix_total": round(prix_sans_options, 2),
                "detail": f"En supprimant les options, le montant passe à {prix_sans_options}€."
            })

    prix_jour_complet = meilleure_offre["prix_jour_eur"] + cout_options_jour
    jours_possibles = int(budget_max // prix_jour_complet)
    if 0 < jours_possibles < nb_jours:
        propositions_arbitrage.append({
            "type": "REDUCTION_DUREE",
            "titre": f"Réduire la durée à {jours_possibles} jour(s)",
            "nouveau_prix_total": round(jours_possibles * prix_jour_complet, 2),
            "detail": f"Conserver le véhicule idéal ({meilleure_offre['modele']}) et toutes vos options mais sur {jours_possibles} jours."
        })

    return {
        "status": "arbitrage_requis",
        "message": f"Votre configuration initiale dépasse le budget de {round(depassement, 2)}€.",
        "offre_ideale": meilleure_offre,
        "prix_initial_eur": round(prix_total_estime, 2),
        "propositions": propositions_arbitrage
    }