import os
from flask import Blueprint, request, jsonify
from qdrant_client import QdrantClient,models
from app.embeddings import get_embedding 
from app.auth import require_api_key


search_bp = Blueprint('search_bp', __name__)


QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = "articles_chunked"


client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)



@search_bp.route('/search', methods=['POST'])
@require_api_key() 
def semantic_search():
    """
    Endpoint pour la recherche sémantique qui accepte un filtre optionnel.
    Exemple: {"query": "...", "code_id": "LEGITEXT000006071307"}
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "La requête doit contenir une clé 'query'"}), 400

    user_query = data['query']
    limit = data.get('limit', 10)
    code_id = data.get('code_id')

    try:
        print(f"Vectorisation de la requête : '{user_query}'")
        query_vector = get_embedding(user_query, is_query=True)

        search_filter = None
        if code_id:
            print(f"Application d'un filtre pour le code_id : {code_id}")
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="code_parent",
                        match=models.MatchValue(value=code_id),
                    )
                ]
            )

        print("Recherche des points similaires dans Qdrant...")
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=search_filter, 
            limit=limit,
            with_payload=True
        )
        
        results = []
        for hit in search_result:
            payload = hit.payload or {}
            results.append({
              
                "id": payload.get("original_id"), 
                "score": hit.score,
                "num": payload.get("title"), 
                "code_parent": payload.get("code_parent"),
                "highlight": payload.get("chunk_text") 
            })
        
        print(f"Recherche terminée. {len(results)} résultats trouvés.")
        return jsonify(results), 200

    except Exception as e:
        print(f"Erreur lors de la recherche sémantique : {e}")
        return jsonify({"error": "Une erreur interne est survenue"}), 500