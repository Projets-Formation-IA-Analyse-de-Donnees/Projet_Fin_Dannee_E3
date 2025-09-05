# Orchestration et Modularité
Le projet est conçu de manière modulaire pour une gestion flexible des pipelines de données et des tâches de maintenance. Le processus de création de l'index de recherche sémantique repose sur un enchaînement logique de scripts :

- startup.py : Ce script d'ETL (Extraction, Transformation, Chargement) récupère les données depuis l'API_ETL (E1), les segmente en chunks, les vectorise et les indexe dans la base de données vectorielle Qdrant. Il doit être exécuté en premier pour initialiser la base de données.

- run_clustering.py : Une fois les données vectorisées en place, ce script applique les algorithmes de réduction de dimension (UMAP) et de clustering (HDBSCAN) pour regrouper les articles par thèmes sémantiques. Il met ensuite à jour chaque point de données avec son cluster_id correspondant. Cette opération est réalisée par lots pour optimiser les performances.

Cette structure en deux étapes permet d'exécuter l'indexation et le clustering indépendamment, offrant ainsi la possibilité de lancer le clustering à la demande sans avoir à réindexer toutes les données.

## Ordre conseillé d'exécution

- startup.py : Charge les données brutes et crée les vecteurs dans la collection Qdrant.

- run_clustering.py : Applique le clustering sur les vecteurs déjà en place et enrichit les données avec l'identifiant de cluster.

## Monitoring et Qualité
Le projet intègre une approche de qualité continue qui s'appuie sur plusieurs éléments :

- Tests automatisés : Les tests unitaires et d'intégration sont exécutés à chaque modification du code via le pipeline de GitHub Actions. Ces tests garantissent que les endpoints de l'API et la logique interne fonctionnent comme prévu.

- Logs : Les scripts d'exécution génèrent des journaux détaillés qui sont stockés dans des fichiers dédiés (Endpoint_Cluster.log, Endpoint_Search.log, Clustering.log, etc.). Ces logs permettent de suivre en détail l'avancement des tâches (nombre de points indexés, nombre de clusters trouvés, etc.) et de diagnostiquer facilement les problèmes. 



## Table des matières

- [Lancement du projet](setup.md)
- [Authentification](auth.md)
- [Endpoints de l’API](api_endpoints.md)

