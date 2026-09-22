import os
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

# Connexion vers la BDD (Railway ou locale)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgrespassword@localhost:5435/drivelocal",
)
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

AGENCES_DATA = [
    ("DriveLocal Paris Gare de Lyon", "Paris", "15 Rue de Bercy, 75012 Paris"),
    ("DriveLocal Lyon Part-Dieu", "Lyon", "5 Place Charles Béraudier, 69003 Lyon"),
    (
        "DriveLocal Marseille Blancarde",
        "Marseille",
        "Place de la Blancarde, 13004 Marseille",
    ),
]

MODELES_DATA = [
    {
        "marque": "Renault",
        "modele": "Clio Hybrid",
        "categorie": "Citadine",
        "transmission": "Automatique",
        "places": 5,
        "description": (
            "Voiture citadine économique et compacte, idéale pour la ville et"
            " les couples, faible consommation de carburant."
        ),
    },
    {
        "marque": "Peugeot",
        "modele": "3008",
        "categorie": "SUV",
        "transmission": "Automatique",
        "places": 5,
        "description": (
            "SUV familial spacieux avec grand coffre, idéal pour les vacances à"
            " la montagne, les routes sinueuses et la route en famille."
        ),
    },
    {
        "marque": "Tesla",
        "modele": "Model 3",
        "categorie": "Berline",
        "transmission": "Automatique",
        "places": 5,
        "description": (
            "Berline 100% électrique premium avec pilote automatique, très"
            " grand confort et grande autonomie pour longs trajets."
        ),
    },
    {
        "marque": "BMW",
        "modele": "Série 4 Cab",
        "categorie": "Cabriolet",
        "transmission": "Automatique",
        "places": 4,
        "description": (
            "Voiture cabriolet de luxe pour un week-end romantique en bord de"
            " mer, conduite sportive et finitions haut de gamme."
        ),
    },
]

VEHICULES_PRICES = [
    (1, 1, 45.00),  # Paris - Clio (45€/j)
    (1, 2, 85.00),  # Paris - 3008 (85€/j)
    (1, 3, 110.00),  # Paris - Tesla (110€/j)
    (2, 1, 40.00),  # Lyon - Clio (40€/j)
    (2, 2, 80.00),  # Lyon - 3008 (80€/j)
    (3, 4, 130.00),  # Marseille - Cabriolet (130€/j)
]

OPTIONS_DATA = [
    (
        "Assurance Tous Risques ZERO Franchise",
        15.00,
        "Couverture complète sans franchise en cas d'accident.",
    ),
    ("Siège Bébé / Enfant", 5.00, "Siège homologué pour la sécurité des enfants."),
    (
        "Conducteur Additionnel",
        8.00,
        "Permet à une deuxième personne de conduire pendant le séjour.",
    ),
    (
        "GPS / Boîtier Wifi",
        4.00,
        "Système de navigation intégré et connexion internet itinérante.",
    ),
]

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS reservations, options_location, vehicules, modeles_vehicules, agences CASCADE;

CREATE TABLE agences (
    agence_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    ville VARCHAR(100) NOT NULL,
    adresse TEXT NOT NULL
);

CREATE TABLE modeles_vehicules (
    modele_id SERIAL PRIMARY KEY,
    marque VARCHAR(50) NOT NULL,
    modele VARCHAR(50) NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    transmission VARCHAR(20) DEFAULT 'Automatique',
    places INT DEFAULT 5,
    description TEXT NOT NULL,
    embedding vector(384)
);

CREATE TABLE vehicules (
    vehicule_id SERIAL PRIMARY KEY,
    agence_id INT REFERENCES agences(agence_id) ON DELETE CASCADE,
    modele_id INT REFERENCES modeles_vehicules(modele_id) ON DELETE CASCADE,
    prix_jour_eur DECIMAL(10,2) NOT NULL,
    disponible BOOLEAN DEFAULT TRUE
);

CREATE TABLE options_location (
    option_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prix_jour_eur DECIMAL(10,2) NOT NULL,
    description TEXT
);

CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    client_nom VARCHAR(100) NOT NULL,
    vehicule_id INT REFERENCES vehicules(vehicule_id),
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    prix_total DECIMAL(10,2) NOT NULL,
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE',
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_seed():
  print("Connexion à PostgreSQL...")
  conn = psycopg.connect(DATABASE_URL)
  register_vector(conn)
  cur = conn.cursor()

  print("Re-création propre des tables (DROP & CREATE)...")
  cur.execute(SCHEMA_SQL)
  conn.commit()

  print("Chargement du modèle d'embeddings...")
  model = SentenceTransformer(MODEL_NAME)

  # Insert Agences
  print("Insertion des agences...")
  for nom, ville, adresse in AGENCES_DATA:
    cur.execute(
        "INSERT INTO agences (nom, ville, adresse) VALUES (%s, %s, %s)",
        (nom, ville, adresse),
    )

  # Insert Modèles + Embeddings
  print("Génération des embeddings et insertion des modèles...")
  for m in MODELES_DATA:
    emb = model.encode(m["description"], normalize_embeddings=True).tolist()
    cur.execute(
        """
            INSERT INTO modeles_vehicules (marque, modele, categorie, transmission, places, description, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
        (
            m["marque"],
            m["modele"],
            m["categorie"],
            m["transmission"],
            m["places"],
            m["description"],
            emb,
        ),
    )

  # Insert Flotte
  print("Insertion des véhicules...")
  for agence_id, modele_id, prix in VEHICULES_PRICES:
    cur.execute(
        """
            INSERT INTO vehicules (agence_id, modele_id, prix_jour_eur)
            VALUES (%s, %s, %s)
            """,
        (agence_id, modele_id, prix),
    )

  # Insert Options
  print("Insertion des options...")
  for nom, prix, desc in OPTIONS_DATA:
    cur.execute(
        """
            INSERT INTO options_location (nom, prix_jour_eur, description)
            VALUES (%s, %s, %s)
            """,
        (nom, prix, desc),
    )

  conn.commit()
  cur.close()
  conn.close()
  print("Base de données initialisée avec succès !")


if __name__ == "__main__":
  init_seed()