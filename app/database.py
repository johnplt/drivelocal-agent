import os
from typing import List, Dict, Any
import psycopg

def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("La variable d'environnement DATABASE_URL est introuvable.")
    return psycopg.connect(database_url)

def chercher_vehicules_vectoriel(vector: list, ville: str, max_prix_jour: float = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            v.vehicule_id,
            m.marque,
            m.modele,
            m.categorie,
            m.description,
            v.prix_jour_eur,
            a.nom AS agence_nom,
            a.ville,
            (m.embedding <=> %s::vector) AS distance
        FROM vehicules v
        JOIN modeles_vehicules m ON v.modele_id = m.modele_id
        JOIN agences a ON v.agence_id = a.agence_id
        WHERE LOWER(a.ville) = LOWER(%s)
          AND v.disponible = TRUE
    """
    params = [str(vector), ville]

    if max_prix_jour is not None:
        query += " AND v.prix_jour_eur <= %s"
        params.append(max_prix_jour)

    query += " ORDER BY distance ASC LIMIT 5;"

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for r in rows:
        results.append({
            "vehicule_id": r[0],
            "marque": r[1],
            "modele": r[2],
            "categorie": r[3],
            "description": r[4],
            "prix_jour_eur": float(r[5]),
            "agence_nom": r[6],
            "ville": r[7],
            "score_similarite": round(1 - float(r[8]), 3)
        })

    cur.close()
    conn.close()
    return results

def get_options() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT option_id, nom, prix_jour_eur, description FROM options_location;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"option_id": r[0], "nom": r[1], "prix_jour_eur": float(r[2]), "description": r[3]}
        for r in rows
    ]