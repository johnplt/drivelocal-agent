import os
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from pathlib import Path
import psycopg

def init_seed():
  conn = psycopg.connect(DATABASE_URL)
  cur = conn.cursor()

  # 1. Exécution du schéma SQL pour créer les tables et l'extension pgvector
  sql_path = Path(__file__).parent.parent / "docker" / "init-db.sql"
  if sql_path.exists():
    print("Création des tables à partir du fichier init-db.sql...")
    with open(sql_path, "r", encoding="utf-8") as f:
      cur.execute(f.read())
    conn.commit()

  # 2. Nettoyage et réinitialisation des tables
  cur.execute(
      "TRUNCATE TABLE reservations, options_location, vehicules,"
      " modeles_vehicules, agences RESTART IDENTITY CASCADE;"
  )

# Connexion vers la BDD locale (Port 5435)
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5435/drivelocal")

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

AGENCES_DATA = [
    ("DriveLocal Paris Gare de Lyon", "Paris", "15 Rue de Bercy, 75012 Paris"),
    ("DriveLocal Lyon Part-Dieu", "Lyon", "5 Place Charles Béraudier, 69003 Lyon"),
    ("DriveLocal Marseille Blancarde", "Marseille", "Place de la Blancarde, 13004 Marseille"),
]

MODELES_DATA = [
    {
        "marque": "Renault",
        "modele": "Clio Hybrid",
        "categorie": "Citadine",
        "transmission": "Automatique",
        "places": 5,
        "description": "Voiture citadine économique et compacte, idéale pour la ville et les couples, faible consommation de carburant."
    },
    {
        "marque": "Peugeot",
        "modele": "3008",
        "categorie": "SUV",
        "transmission": "Automatique",
        "places": 5,
        "description": "SUV familial spacieux avec grand coffre, idéal pour les vacances à la montagne, les routes sinueuses et la route en famille."
    },
    {
        "marque": "Tesla",
        "modele": "Model 3",
        "categorie": "Berline",
        "transmission": "Automatique",
        "places": 5,
        "description": "Berline 100% électrique premium avec pilote automatique, très grand confort et grande autonomie pour longs trajets."
    },
    {
        "marque": "BMW",
        "modele": "Série 4 Cab",
        "categorie": "Cabriolet",
        "transmission": "Automatique",
        "places": 4,
        "description": "Voiture cabriolet de luxe pour un week-end romantique en bord de mer, conduite sportive et finitions haut de gamme."
    }
]

VEHICULES_PRICES = [
    (1, 1, 45.00), # Paris - Clio (45€/j)
    (1, 2, 85.00), # Paris - 3008 (85€/j)
    (1, 3, 110.00), # Paris - Tesla (110€/j)
    (2, 1, 40.00), # Lyon - Clio (40€/j)
    (2, 2, 80.00), # Lyon - 3008 (80€/j)
    (3, 4, 130.00), # Marseille - Cabriolet (130€/j)
]

OPTIONS_DATA = [
    ("Assurance Tous Risques ZERO Franchise", 15.00, "Couverture complète sans franchise en cas d'accident."),
    ("Siège Bébé / Enfant", 5.00, "Siège homologué pour la sécurité des enfants."),
    ("Conducteur Additionnel", 8.00, "Permet à une deuxième personne de conduire pendant le séjour."),
    ("GPS / Boîtier Wifi", 4.00, "Système de navigation intégré et connexion internet itinérante.")
]

def init_seed():
    print("Chargement du modèle d'embeddings...")
    model = SentenceTransformer(MODEL_NAME)

    print("Connexion à PostgreSQL...")
    conn = psycopg.connect(DB_URL)
    register_vector(conn)
    cur = conn.cursor()

    # Nettoyage préalable
    cur.execute("TRUNCATE TABLE reservations, options_location, vehicules, modeles_vehicules, agences RESTART IDENTITY CASCADE;")

    # Insert Agences
    print("Insertion des agences...")
    for nom, ville, adresse in AGENCES_DATA:
        cur.execute("INSERT INTO agences (nom, ville, adresse) VALUES (%s, %s, %s)", (nom, ville, adresse))

    # Insert Modèles + Embeddings
    print("Génération des embeddings et insertion des modèles...")
    for m in MODELES_DATA:
        emb = model.encode(m["description"], normalize_embeddings=True).tolist()
        cur.execute(
            """
            INSERT INTO modeles_vehicules (marque, modele, categorie, transmission, places, description, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (m["marque"], m["modele"], m["categorie"], m["transmission"], m["places"], m["description"], emb)
        )

    # Insert Flotte
    print("Insertion des véhicules...")
    for agence_id, modele_id, prix in VEHICULES_PRICES:
        cur.execute("INSERT INTO vehicules (agence_id, modele_id, prix_jour_eur) VALUES (%s, %s, %s)", (agence_id, modele_id, prix))

    # Insert Options
    print("Insertion des options...")
    for nom, prix, desc in OPTIONS_DATA:
        cur.execute("INSERT INTO options_location (nom, prix_jour_eur, description) VALUES (%s, %s, %s)", (nom, prix, desc))

    conn.commit()
    cur.close()
    conn.close()
    print("Base de données initialisée avec succès !")

if __name__ == "__main__":
    init_seed()