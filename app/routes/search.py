import os
from flask import Blueprint, request, jsonify
from qdrant_client import QdrantClient

# On suppose que votre fichier embeddings.py a été mis à jour comme précédemment
from app.embeddings import get_embedding 
from app.auth import require_api_key


search_bp = Blueprint('search_bp', __name__)


QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = "articles"

# Initialisation du client Qdrant
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# --- Définition de la route ---

@search_bp.route('/search', methods=['POST'])
@require_api_key() 
def semantic_search():
    """
    Endpoint pour la recherche sémantique.
    Attend une requête POST avec un JSON contenant une clé "query".
    Exemple: {"query": "quelles sont les sanctions pour un fonctionnaire ?"}
    """
    # 1. Récupérer les données de la requête
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "La requête doit contenir une clé 'query'"}), 400

    user_query = data['query']
    
    # On peut définir le nombre de résultats à retourner (par défaut 5)
    limit = data.get('limit', 5)

    try:
        # 2. Vectoriser la question de l'utilisateur
        print(f"Vectorisation de la requête : '{user_query}'")
        
        # --- LA MODIFICATION CRUCIALE EST ICI ---
        # On ajoute is_query=True pour que le préfixe "query: " soit ajouté
        query_vector = get_embedding(user_query, is_query=True)

        # 3. Interroger la base de données Qdrant
        print("Recherche des points similaires dans Qdrant...")
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True # On veut récupérer les métadonnées
        )
        
        # 4. Formater les résultats pour la réponse
        results = []
        for hit in search_result:
            results.append({
                "id": hit.payload.get("original_id"), 
                "score": hit.score,
                "num": hit.payload.get("title") if hit.payload else "Numéro non disponible"
            })
        
        print(f"Recherche terminée. {len(results)} résultats trouvés.")
        return jsonify(results), 200

    except Exception as e:
        print(f"Erreur lors de la recherche sémantique : {e}")
        return jsonify({"error": "Une erreur interne est survenue"}), 500
