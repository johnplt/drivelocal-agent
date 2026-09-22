import streamlit as st
import requests

# Titre de l'application
st.set_page_config(page_title="DriveLocal — Concierge de Location", page_icon="🚗", layout="wide")

st.title("🚗 DriveLocal — Concierge & Arbitrage de Location")
st.markdown("Trouvez le véhicule idéal grâce à la recherche sémantique (pgvector) et ajustez votre budget en temps réel.")

st.divider()

# Formulaire de demande
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 Vos critères de séjour")
    besoin_texte = st.text_area(
        "Décrivez votre besoin en langage naturel :",
        value="Un grand SUV familial spacieux et confortable pour partir à la montagne avec du matériel.",
        height=100
    )
    ville = st.selectbox("Ville de prise en charge :", ["Paris", "Lyon", "Marseille"])
    nb_jours = st.slider("Nombre de jours :", min_value=1, max_value=14, value=3)
    budget_max = st.number_input("Budget maximum (€) :", min_value=50, max_value=3000, value=200, step=10)

with col_right:
    st.subheader("🛠️ Options complémentaires")
    options_dict = {
        1: "Assurance Tous Risques (15€/j)",
        2: "Siège Bébé / Enfant (5€/j)",
        3: "Conducteur Additionnel (8€/j)",
        4: "GPS / Boîtier Wifi (4€/j)"
    }
    options_selectionnees = st.multiselect(
        "Sélectionnez vos options :",
        options=list(options_dict.keys()),
        format_func=lambda x: options_dict[x],
        default=[1]
    )

st.divider()

if st.button("🔎 Analyser et trouver mon véhicule", type="primary"):
    payload = {
        "besoin_texte": besoin_texte,
        "ville": ville,
        "nb_jours": nb_jours,
        "budget_max": float(budget_max),
        "options_ids": options_selectionnees
    }

    try:
        # Appel à l'API FastAPI
        response = requests.post("http://localhost:8000/api/arbitrer", json=payload)
        res = response.json()

        if res.get("status") == "ok":
            st.success(f"✅ {res['message']}")
            
            o = res["offre_retenue"]
            st.metric(label="Prix Total", value=f"{res['prix_total_eur']} €", delta=f"-{res['economie_eur']} € sous le budget")
            st.markdown(f"### 🚘 **{o['marque']} {o['modele']}** ({o['categorie']})")
            st.write(f"**Agence :** {o['agence_nom']} ({o['ville']})")
            st.write(f"**Description :** {o['description']}")
            st.caption(f"Score de similarité sémantique (pgvector) : {o['score_similarite']}")

        elif res.get("status") == "arbitrage_requis":
            st.warning(f"⚠️ {res['message']}")
            
            o = res["offre_ideale"]
            st.markdown(f"#### Véhicule idéal trouvé : **{o['marque']} {o['modele']}** ({o['prix_jour_eur']}€/j)")
            st.write(f"Prix total envisagé (avec options) : **{res['prix_initial_eur']} €**")
            
            st.subheader("💡 Propositions d'arbitrage de l'Agent :")
            
            for prop in res.get("propositions", []):
                with st.expander(f"📌 {prop['titre']} — **Nouveau Total : {prop['nouveau_prix_total']} €**"):
                    st.write(prop["detail"])
                    st.button("Choisir cette option", key=prop["type"])

        else:
            st.error(res.get("message", "Une erreur est survenue."))

    except requests.exceptions.ConnectionError:
        st.error("Impossible de contacter l'API FastAPI (http://localhost:8000). Assure-toi qu'elle tourne !")