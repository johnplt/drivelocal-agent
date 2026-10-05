import os
import psycopg
from huggingface_hub import InferenceClient
from dotenv import load_dotenv


load_dotenv()
# Configuration & Token Hugging Face
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialisation du client Hugging Face SDK
hf_client = InferenceClient(token=HF_TOKEN)


def get_embedding(text: str) -> list[float]:
    """Génère un embedding vectoriel via le SDK officiel Hugging Face."""
    embedding = hf_client.feature_extraction(text, model=HF_MODEL)

    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    if (
        isinstance(embedding, list)
        and len(embedding) > 0
        and isinstance(embedding[0], list)
    ):
        return embedding[0]

    return embedding


def init_seed():
    print("Connexion à Supabase...")
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1. Activation de l'extension pgvector
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Nettoyage et Re-création selon ton schéma Supabase
    print("Création du schéma Supabase (Database.py standard)...")
    cur.execute("""
        DROP TABLE IF EXISTS vehicule_options CASCADE;
        DROP TABLE IF EXISTS options_location CASCADE;
        DROP TABLE IF EXISTS vehicules CASCADE;
        DROP TABLE IF EXISTS modeles_vehicules CASCADE;
        DROP TABLE IF EXISTS agences CASCADE;

        CREATE TABLE agences (
            agence_id SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            ville VARCHAR(100) NOT NULL
        );

        CREATE TABLE modeles_vehicules (
            modele_id SERIAL PRIMARY KEY,
            marque VARCHAR(50) NOT NULL,
            modele VARCHAR(50) NOT NULL,
            categorie VARCHAR(50) NOT NULL,
            description TEXT,
            embedding vector(384)
        );

        CREATE TABLE vehicules (
            vehicule_id SERIAL PRIMARY KEY,
            modele_id INT REFERENCES modeles_vehicules(modele_id),
            agence_id INT REFERENCES agences(agence_id),
            prix_jour_eur DECIMAL(10,2) NOT NULL,
            disponible BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE options_location (
            option_id SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            prix_jour_eur DECIMAL(10,2) NOT NULL,
            description TEXT
        );

        CREATE TABLE vehicule_options (
            vehicule_id INT REFERENCES vehicules(vehicule_id),
            option_id INT REFERENCES options_location(option_id),
            PRIMARY KEY (vehicule_id, option_id)
        );
    """)

    # 3. Insertion Agences
    print("Insertion des agences...")
    agences = [
        ("DriveLocal Paris Centre", "Paris"),
        ("DriveLocal Lyon Part-Dieu", "Lyon"),
        ("DriveLocal Marseille Gare", "Marseille"),
    ]
    cur.executemany(
        "INSERT INTO agences (nom, ville) VALUES (%s, %s);", agences
    )

    # 4. Insertion Modèles avec Embeddings
    print("Génération des embeddings et insertion des modèles...")
    modeles = [
        {
            "marque": "Renault",
            "modele": "Clio 5",
            "cat": "Citadine",
            "desc": "Petite voiture économique idéale pour les trajets urbains et se garer facilement en ville.",
        },
        {
            "marque": "Peugeot",
            "modele": "3008",
            "cat": "SUV",
            "desc": "SUV familial spacieux avec grand coffre, idéal pour les longs trajets et la montagne.",
        },
        {
            "marque": "Tesla",
            "modele": "Model 3",
            "cat": "Berline Électrique",
            "desc": "Berline 100% électrique moderne avec conduite autonome assistée et grande autonomie.",
        },
        {
            "marque": "BMW",
            "modele": "Série 3",
            "cat": "Berline Premium",
            "desc": "Berline élégante et sportive, offre un grand confort de route pour rendez-vous professionnels.",
        },
    ]

    for m in modeles:
        emb = get_embedding(m["desc"])
        cur.execute(
            """
            INSERT INTO modeles_vehicules (marque, modele, categorie, description, embedding)
            VALUES (%s, %s, %s, %s, %s::vector);
        """,
            (m["marque"], m["modele"], m["cat"], m["desc"], str(emb)),
        )

    # 5. Insertion Véhicules
    print("Insertion des véhicules...")
    vehicules = [
        (1, 1, 35.00, True),  # Clio Paris
        (2, 1, 75.00, True),  # 3008 Paris
        (3, 1, 95.00, True),  # Tesla Paris
        (4, 1, 110.00, True),  # BMW Paris
        (1, 2, 38.00, True),  # Clio Lyon
        (2, 2, 70.00, True),  # 3008 Lyon
        (3, 3, 90.00, True),  # Tesla Marseille
    ]
    cur.executemany(
        """
        INSERT INTO vehicules (modele_id, agence_id, prix_jour_eur, disponible)
        VALUES (%s, %s, %s, %s);
    """,
        vehicules,
    )

    # 6. Insertion Options
    print("Insertion des options...")
    options = [
        ("Siège bébé", 5.00, "Siège adapté de 9 à 36kg"),
        ("Conducteur additionnel", 8.00, "Ajout d'un deuxième conducteur"),
        ("GPS Premium", 4.00, "GPS mis à jour avec info trafic"),
        ("Chaînes neige", 6.00, "Paire de chaînes adaptée au véhicule"),
    ]
    cur.executemany(
        """
        INSERT INTO options_location (nom, prix_jour_eur, description)
        VALUES (%s, %s, %s);
    """,
        options,
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Base de données initialisée avec succès sur le bon schéma !")


if __name__ == "__main__":
    init_seed()