from sentence_transformers import SentenceTransformer
from app.database import chercher_vehicules_vectoriel, get_options

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(MODEL_NAME)

def arbitrer_location(besoin_texte: str, ville: str, nb_jours: int, budget_max: float, options_souhaitees: list[int] = None):
    options_souhaitees = options_souhaitees or []
    
    # 1. Générer l'embedding du besoin utilisateur
    user_emb = model.encode(besoin_texte, normalize_embeddings=True).tolist()
    
    # 2. Recherche vectorielle sans filtre de prix stricte d'abord
    offres = chercher_vehicules_vectoriel(user_emb, ville)
    options_dispos = get_options()
    
    # Filtrer les options retenues
    opts_retenues = [o for o in options_dispos if o["option_id"] in options_souhaitees]
    cout_options_jour = sum(o["prix_jour_eur"] for o in opts_retenues)
    
    if not offres:
        return {"status": "erreur", "message": f"Aucun véhicule disponible à {ville}."}

    meilleure_offre = offres[0]
    prix_total_estime = (meilleure_offre["prix_jour_eur"] + cout_options_jour) * nb_jours

    # Case A : Dans le budget
    if prix_total_estime <= budget_max:
        return {
            "status": "ok",
            "message": "L'offre correspond parfaitement à vos critères et entre dans votre budget.",
            "offre_retenue": meilleure_offre,
            "options": opts_retenues,
            "prix_total_eur": prix_total_estime,
            "economie_eur": budget_max - prix_total_estime
        }

    # Case B : Dépassement de budget -> Arbitrage requis
    depassement = prix_total_estime - budget_max
    propositions_arbitrage = []

    # Arbitrage 1 : Modèle plus économique
    prix_max_vehicule_jour = (budget_max / nb_jours) - cout_options_jour
    if prix_max_vehicule_jour > 0:
        offres_eco = chercher_vehicules_vectoriel(user_emb, ville, max_prix_jour=prix_max_vehicule_jour)
        if offres_eco:
            alt = offres_eco[0]
            propositions_arbitrage.append({
                "type": "CHANGEMENT_VEHICULE",
                "titre": f"Passer sur la {alt['marque']} {alt['modele']}",
                "nouveau_prix_total": (alt["prix_jour_eur"] + cout_options_jour) * nb_jours,
                "detail": f"Économie de {(meilleure_offre['prix_jour_eur'] - alt['prix_jour_eur']) * nb_jours}€ en choisissant la catégorie {alt['categorie']}."
            })

    # Arbitrage 2 : Retrait d'options
    if opts_retenues:
        prix_sans_options = meilleure_offre["prix_jour_eur"] * nb_jours
        if prix_sans_options <= budget_max:
            propositions_arbitrage.append({
                "type": "RETRAIT_OPTIONS",
                "titre": "Retirer certaines options payantes",
                "nouveau_prix_total": prix_sans_options,
                "detail": f"En supprimant les options, le montant passe à {prix_sans_options}€."
            })

    # Arbitrage 3 : Réduction de la durée
    prix_jour_complet = meilleure_offre["prix_jour_eur"] + cout_options_jour
    jours_possibles = int(budget_max // prix_jour_complet)
    if jours_possibles > 0 and jours_possibles < nb_jours:
        propositions_arbitrage.append({
            "type": "REDUCTION_DUREE",
            "titre": f"Réduire la durée à {jours_possibles} jour(s)",
            "nouveau_prix_total": jours_possibles * prix_jour_complet,
            "detail": f"Conserver le véhicule idéal ({meilleure_offre['modele']}) et toutes vos options mais sur {jours_possibles} jours."
        })

    return {
        "status": "arbitrage_requis",
        "message": f"Votre configuration initiale dépasse le budget de {round(depassement, 2)}€.",
        "offre_ideale": meilleure_offre,
        "prix_initial_eur": prix_total_estime,
        "propositions": propositions_arbitrage
    }