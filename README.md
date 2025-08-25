# API de Recherche Sémantique et de Clustering de Textes Juridiques
Ce projet a pour but de créer un service d'intelligence artificielle qui expose les capacités d'un modèle de langage spécialisé pour les textes juridiques. Il se matérialise sous la forme d'une API RESTful qui permet la recherche sémantique et la catégorisation (clustering) d'articles de loi.

L'architecture est conçue dans une approche MLOps, en intégrant des pipelines automatisés et des outils de conteneurisation pour garantir la qualité, la reproductibilité et la facilité de déploiement du service.

## Fonctionnalités Clés
- Recherche Sémantique : Permet aux utilisateurs de trouver les articles de loi les plus pertinents par rapport à une requête en langage naturel, avec un filtrage possible par code de loi.

- Clustering d'Articles : Regroupe les articles par thèmes sémantiques. L'API expose un endpoint pour récupérer le cluster dominant d'une liste d'articles, ce qui est utile pour l'analyse et la navigation.

- Pipeline de Données (ETL) : Un script dédié récupère les données depuis une API externe (E1), les segmente en "chunks", les vectorise à l'aide d'un modèle spécialisé et les indexe dans une base de données vectorielle Qdrant.

- Authentification par Clé API : L'accès aux endpoints de l'API est sécurisé et nécessite une clé API valide dans les en-têtes de la requête.

- Pipeline de CI/CD : Un workflow GitHub Actions automatise les tests, le calcul de la couverture et la création d'une image Docker prête au déploiement pour chaque nouvelle version du code.


## Structure du projet
Ce projet est organisé de manière modulaire pour une maintenance et un déploiement facilités. Chaque dossier et fichier a un rôle précis dans le pipeline qui va de l'ingestion des données à l'exposition du modèle d'intelligence artificielle via une API.

- app/ : Contient l'application Flask et les "blueprints" de l'API.
    - auth.py : Module de gestion de l'authentification par clé API.

    - embeddings.py : Gère le chargement et la vectorisation des textes à l'aide du modèle d'embedding.

    - run_clustering.py : Script indépendant pour lancer l'algorithme de clustering sur les données et srocker les resultat en base.

    - startup.py : Script d'ETL (Extraction, Transformation, Chargement) pour la récupération des données, leur vectorisation et leur indexation initiale dans Qdrant.

    - test_data.json : Fichier de données mockées utilisé dans le pipeline de CI pour les tests d'intégration.

    - routes/ : Regroupe les fichiers de routage pour les endpoints Search et Clusters.

        - cluster.py : Gère le point de terminaison de l'API pour le clustering.

        - search.py : Gère le point de terminaison de l'API pour la recherche sémantique.


- tests/ : Contient tous les tests automatisés du projet.

    - conftest.py : Fichier de configuration pour les "fixtures" de Pytest.

    - test_integration_api.py : Tests d'intégration pour les points de terminaison de l'API.

    - test_unit_logic.py : Tests unitaires pour la logique de segmentation (chunking).

- benchmark_models.py : Script de benchmark pour le suivi des expériences avec MLflow.



- run.py : Point d'entrée de l'application Flask pour lancer l'API.



- .github/ : Contient la configuration du pipeline d'intégration continue (CI/CD) de GitHub Actions.

    - workflows/ : Contient les fichiers de workflow du projet.

        - ci.yml : Le pipeline de CI/CD qui automatise les tests et la création d'images Docker.

- docker-compose.yml : Fichier de configuration Docker qui orchestre les conteneurs de l'application (Flask) et de la base de données vectorielle (Qdrant).

- Dockerfile : Contient les instructions pour construire l'image Docker de l'application Flask.

- requirements.txt : Liste des dépendances Python nécessaires au projet.

## Table des matières

- [Lancement du projet](docs/setup.md)
- [Orchestration](docs/orchestration.md)
- [Authentification](docs/auth.md)
- [Endpoints de l’API](docs/api_endpoints.md)

