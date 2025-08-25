# Authentification

L'accès à l'API est sécurisé par une clé d'authentification transmise via l'en-tête HTTP `x-api-key`.

Chaque point de terminaison est protégé par un décorateur spécifique, qui vérifie que la clé fournie correspond à celle définie dans le fichier d'environnement .env.



Pour y accéder, il faut inclure l'en-tête personnalisé dans chaque requête.

Cette clé est définie dans le fichier  .env à la variable suivante :
```bash
API_KEY=exemple_clé_API
```
Par exemple, pour tester un endpoint :
```bash
curl -H "x-api-key: exemple_clé_API" http://localhost:5000/...
```



## Table des matières

- [Lancement du projet](docs/setup.md)
- [Orchestration](docs/orchestration.md)
- [Endpoints de l’API](docs/api_endpoints.md)
