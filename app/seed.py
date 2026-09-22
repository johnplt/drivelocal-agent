import os
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

# Récupération de l'URL fournie par Railway (avec fallback local)
DB_URL = os.getenv(
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
            "Berline 100% électrique premium avec pilote automatique, très grand"
            " confort et grande autonomie pour longs trajets."
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
    (
        "Siège Bébé / Enfant",
        5.00,
        "Siège homologué pour la sécurité des enfants.",
    ),
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


def init_seed():
  print("Chargement du modèle d'embeddings...")
  model = SentenceTransformer(MODEL_NAME)

  print("Connexion à PostgreSQL...")
  conn = psycopg.connect(DB_URL)

  # 1. Activation pgvector
  try:
    with conn.cursor() as cur:
      cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    register_vector(conn)
    print("Extension pgvector vérifiée/activée.")
  except Exception as e:
    print(f"Note pgvector: {e}")
    conn.rollback()

  cur = conn.cursor()

  # 2. Création du schéma SQL adapté à tes structures de données
  print("Vérification et création des tables...")
  SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS agences (
        id_agence SERIAL PRIMARY KEY,
        nom VARCHAR(100) NOT NULL,
        ville VARCHAR(100) NOT NULL,
        adresse TEXT
    );

    CREATE TABLE IF NOT EXISTS modeles_vehicules (
        id_modele SERIAL PRIMARY KEY,
        marque VARCHAR(50) NOT NULL,
        modele VARCHAR(50) NOT NULL,
        categorie VARCHAR(50) NOT NULL,
        transmission VARCHAR(50),
        places INT,
        description TEXT,
        embedding vector(384)
    );

    CREATE TABLE IF NOT EXISTS vehicules (
        id_vehicule SERIAL PRIMARY KEY,
        agence_id INT REFERENCES agences(id_agence),
        modele_id INT REFERENCES modeles_vehicules(id_modele),
        prix_jour_eur DECIMAL(10,2) NOT NULL,
        statut VARCHAR(20) DEFAULT 'disponible'
    );

    CREATE TABLE IF NOT EXISTS options_location (
        id_option SERIAL PRIMARY KEY,
        nom VARCHAR(100) NOT NULL,
        prix_jour_eur DECIMAL(10,2) NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS reservations (
        id_reservation SERIAL PRIMARY KEY,
        id_vehicule INT REFERENCES vehicules(id_vehicule),
        date_debut DATE NOT NULL,
        date_fin DATE NOT NULL,
        prix_total DECIMAL(10,2) NOT NULL
    );
    """
  cur.execute(SCHEMA_SQL)
  conn.commit()

  # 3. Réinitialisation des données
  print("Réinitialisation des tables...")
  cur.execute(
      "TRUNCATE TABLE reservations, options_location, vehicules,"
      " modeles_vehicules, agences RESTART IDENTITY CASCADE;"
  )

  # 4. Insertion des agences
  print("Insertion des agences...")
  for nom, ville, adresse in AGENCES_DATA:
    cur.execute(
        "INSERT INTO agences (nom, ville, adresse) VALUES (%s, %s, %s);",
        (nom, ville, adresse),
    )

  # 5. Insertion des modèles + Embeddings
  print("Génération des embeddings et insertion des modèles...")
  for m in MODELES_DATA:
    emb = model.encode(m["description"], normalize_embeddings=True).tolist()
    cur.execute(
        """
        INSERT INTO modeles_vehicules (marque, modele, categorie, transmission, places, description, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
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

  # 6. Insertion des véhicules
  print("Insertion des véhicules...")
  for agence_id, modele_id, prix in VEHICULES_PRICES:
    cur.execute(
        """
        INSERT INTO vehicules (agence_id, modele_id, prix_jour_eur)
        VALUES (%s, %s, %s);
        """,
        (agence_id, modele_id, prix),
    )

  # 7. Insertion des options
  print("Insertion des options...")
  for nom, prix, desc in OPTIONS_DATA:
    cur.execute(
        """
        INSERT INTO options_location (nom, prix_jour_eur, description)
        VALUES (%s, %s, %s);
        """,
        (nom, prix, desc),
    )

  conn.commit()
  cur.close()
  conn.close()
  print("Base de données initialisée avec succès !")


if __name__ == "__main__":
  init_seed()