-- Activer l'extension pour les embeddings vectoriels
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Agences
CREATE TABLE IF NOT EXISTS agences (
    agence_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    ville VARCHAR(100) NOT NULL,
    adresse TEXT NOT NULL
);

-- 2. Modèles de véhicules (Catalogue + Embeddings)
CREATE TABLE IF NOT EXISTS modeles_vehicules (
    modele_id SERIAL PRIMARY KEY,
    marque VARCHAR(50) NOT NULL,
    modele VARCHAR(50) NOT NULL,
    categorie VARCHAR(50) NOT NULL, -- Citadine, SUV, Berline, Cabriolet, Utilitaire
    transmission VARCHAR(20) DEFAULT 'Automatique',
    places INT DEFAULT 5,
    description TEXT NOT NULL,
    embedding vector(384) -- Dimension pour MiniLM-L12-v2
);

-- 3. Flotte de véhicules par agence
CREATE TABLE IF NOT EXISTS vehicules (
    vehicule_id SERIAL PRIMARY KEY,
    agence_id INT REFERENCES agences(agence_id) ON DELETE CASCADE,
    modele_id INT REFERENCES modeles_vehicules(modele_id) ON DELETE CASCADE,
    prix_jour_eur DECIMAL(10,2) NOT NULL,
    disponible BOOLEAN DEFAULT TRUE
);

-- 4. Options
CREATE TABLE IF NOT EXISTS options_location (
    option_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prix_jour_eur DECIMAL(10,2) NOT NULL,
    description TEXT
);

-- 5. Réservations
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id SERIAL PRIMARY KEY,
    client_nom VARCHAR(100) NOT NULL,
    vehicule_id INT REFERENCES vehicules(vehicule_id),
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    prix_total DECIMAL(10,2) NOT NULL,
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE',
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);