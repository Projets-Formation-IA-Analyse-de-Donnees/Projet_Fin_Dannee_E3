# Documentation des Endpoints de l'API Flask

Tous les endpoints nécessitent une clé API envoyée dans l'en-tête `x-api-key`.

Vous pouvez la définir dans votre .env.

Pour plus d'informations : [Voir la documentation d'authentification](auth.md)

## Points de Terminaison de l'API

L'API expose deux endpoints principaux:

### Recherche Sémantique


Méthode : POST

Description : Effectue une recherche sémantique basée sur une requête textuelle et renvoie les articles les plus pertinents. Un filtre par code_id est optionnel.

**Exemple de requête :**

```json
{
  "query": "délit de fuite",
  "code_id": "LEGITEXT000006071307"
}
```
**Exemple de réponse :**

```json

[
  {
    "id": "un_id_article",
    "score": 0.85,
    "num": "Art. L1",
    "code_parent": "LEGITEXT000006071307",
    "highlight": "Extrait de texte pertinent..."
  }
]
```
### Clusters d'Articles


Méthode : POST

Description : Trouve le cluster dominant pour chaque article de la liste fournie.

**Exemple de requête :**

```json
{
  "article_ids": ["LEGIARTI000006071307", "LEGIARTI000006071308"]
}

```

**Exemple de réponse :**

```json

{
  "LEGIARTI000006071307": 42,
  "LEGIARTI000006071308": 15
}

```



## Table des matières

- [Lancement du projet](setup.md)
- [Orchestration](orchestration.md)
- [Authentification](auth.md)
