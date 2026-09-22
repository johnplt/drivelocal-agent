# DriveLocal

![Texte alternatif](docs/images/drivelocal_image.jpg)


## À quoi sert ce projet ?

DriveLocal est une application Web conçue pour simplifier la recherche et l'optimisation de réservations de véhicules. Grâce à l'utilisation de modèles d'embeddings sémantiques et de la recherche vectorielle, l'application permet à un utilisateur de formuler sa recherche en langage naturel (ex: "un véhicule familial spacieux pour aller à la montagne avec un petit budget"). 

Le système effectue un arbitrage intelligent entre les critères exprimés, le budget cible et la flotte disponible afin de recommander les meilleures options de location et les options complémentaires associées.

## Architecture du Projet

L'application repose sur une architecture microservices entièrement conteneurisée :

* **Frontend (UI) :** Interface utilisateur développée avec Streamlit, permettant la saisie des requêtes en langage naturel et la visualisation dynamique des recommandations.
* **Backend (API) :** Service FastAPI gérant la logique métier, la génération d'embeddings vectoriels et les requêtes d'arbitrage.
* **Base de Données :** Instance PostgreSQL augmentée de l'extension `pgvector` pour le stockage relationnel (agences, véhicules, réservations) et l'indexation vectorielle des caractéristiques des véhicules.
* **Pipeline Sémantique :** Modèle `sentence-transformers/all-MiniLM-L6-v2` exécuté au sein de l'API pour convertir les requêtes textuelles et les fiches véhicules en vecteurs de dimension 384.

## Structure du Dépôt

```text
DriveLocal/
├── .github/
│   └── workflows/          # Pipelines CI/CD (GitHub Actions)
├── app/
│   ├── main.py             # Point d'entrée de l'API FastAPI
│   ├── database.py         # Gestion des connexions PostgreSQL / psycopg
│   ├── models.py           # Schémas Pydantic et modèles de données
│   ├── seed.py             # Initialisation du schéma SQL et injection des données
├── ui/
│   └── app.py              # Interface utilisateur Streamlit
├── docker/
│   ├── Dockerfile.api      # Configuration Docker pour l'API Backend
│   ├── Dockerfile.ui       # Configuration Docker pour le Frontend Streamlit
│   └── init-db.sql         # Schéma de base de données PostgreSQL + pgvector
├── docker-compose.yml      # Orchestration locale des services (API, UI, Database)
├── pyproject.toml          # Gestion des dépendances Python (uv)
└── README.md
```

## Spécifications Techniques
- Langage : Python 3.11+
- Gestionnaire de paquets : uv
- Framework API : FastAPI + Uvicorn
- Framework UI : Streamlit
- Modèle ML : SentenceTransformers (all-MiniLM-L6-v2)
- Base de données : PostgreSQL 15+ avec extension pgvector
- Pilote BDD : psycopg (v3)
- Conteneurisation : Docker & Docker Compose

## Guide de Déploiement / Reproduire le Projet
- Prérequis
- Git
- Docker et Docker Compose
- (Optionnel pour le dev local) uv ou pip

1. Lancement en Environnement Local (Docker Compose)

    Cloner le dépôt et démarrer l'ensemble des services via Docker Compose :

    ```bash
    git clone [https://github.com/votre-compte/drivelocal-agent.git](https://github.com/votre-compte/drivelocal-agent.git)
    cd drivelocal-agent
    docker compose up --build -d
    ```
    L'orchestrateur démarrera la base de données, exécutera l'initialisation du schéma et des données de démonstration via seed.py, puis lancera l'API et l'interface utilisateur.
    
    Accès aux services :
    - Interface Streamlit : http://localhost:8501
    - Documentation API (Swagger) : http://localhost:8000/docs

2. Déploiement Cloud (Railway / Render)

    Le projet est conçu pour s'exécuter sur toute plateforme supportant les conteneurs Docker.
    1. **Base de Données** : Provisionner une instance PostgreSQL et exécuter la commande CREATE EXTENSION IF NOT EXISTS vector;.
    2. **Service Backend (API)** :
        - Pointer vers le fichier docker/Dockerfile.api.
        - Définir la variable d'environnement DATABASE_URL avec la chaîne de connexion PostgreSQL.
    3. **Service Frontend (UI)** :
        - Pointer vers le fichier docker/Dockerfile.ui.
        - Définir la variable d'environnement API_URL pointant vers l'URL publique de l'API déployée (ex: https://votre-api.up.railway.app/api/arbitrer).

## Licence
Ce projet est sous licence MIT. Veuillez consulter le fichier LICENSE pour plus de détails.