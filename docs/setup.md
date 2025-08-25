# Lancement du projet

Voici les étapes nécessaires pour configurer et lancer l’ensemble du projet 



## Prérequis

- Python 3.10 ou supérieur
- Docker



## Étapes d'installation


### 1. Cloner le dépôt dans votre répertoire de travail
```bash
git clone <lien-du-repo>
cd Projet_Fin_Dannee_E3
```
### 2. Créer un fichier .env à la racine du projet:
```bash
ARANGO_HOST = Host de votre BDD arango
ARANGO_URL = URL de votre BDD arango
ARANGO_USER = Nom Utilisateur arango
ARANGO_PASSWORD = Mot de Passe arango
API_KEY = Clef autnetification de votre API
QDRANT_HOST = Host de votre BDD qdrant
QDRANT_PORT = Port de votre BDD qdrant
URL_ARTICLE = Route de récupération des données via API_ETL 
API_KEY_ETL = Clef d'authentification de l'API_ETL 
```
URL_ARTICLE et API_KEY_ETL font référence au projet E1 mettant à disposition une API_ETL, qui extrait, stock et met à disposition des données.

### 3. Lancer les services Docker
```bash
docker-compose up -d --build
```
### 4. Lancer les scripts depuis le conteneur
```bash
docker compose exec flask_model python startup.py
docker compose exec flask_model python app/run_clustering.py

```




## Table des matières


- [Orchestration](docs/orchestration.md)
- [Authentification](docs/auth.md)
- [Endpoints de l’API](docs/api_endpoints.md)
