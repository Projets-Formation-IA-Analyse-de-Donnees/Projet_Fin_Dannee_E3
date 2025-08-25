import os
from flask import Blueprint, jsonify,request
from qdrant_client import QdrantClient, models
from app.auth import require_api_key
from collections import Counter
import itertools
import traceback
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("Endpoint_Cluster.log", mode='w'), # 'w' pour écraser le log à chaque lancement
                        logging.StreamHandler()
                    ])


clusters_bp = Blueprint('clusters_bp', __name__)

QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT"))
COLLECTION_NAME = "articles_chunked"
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

@clusters_bp.route('/clusters_for_articles', methods=['POST'])
@require_api_key()
def get_clusters_for_articles():
    """
    Reçoit une liste d'ID d'articles et renvoie leur cluster dominant.
    """
    data = request.get_json()
    if not data or 'article_ids' not in data:
        return jsonify({"error": "La liste 'article_ids' est requise"}), 400

    article_ids = data['article_ids']
    logging.info(f"Requête reçue pour trouver les clusters de {len(article_ids)} articles.")
    
    try:
        logging.info(f"Récupération des chunks pour les articles : {article_ids}")
        response, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="original_id", match=models.MatchAny(any=article_ids))
                ]
            ),
            limit=len(article_ids) * 20,
            with_payload=["original_id", "cluster_id"],
            with_vectors=False
        )
        if not response:
            logging.error("Aucun chunk trouvé dans la base de données.")
            return jsonify({"error": "No chunks found for this code"}), 404
        
        logging.info(f"{len(response)} chunks récupérés. Début de l'agrégation...")
        points_sorted = sorted(response, key=lambda p: p.payload.get('original_id'))

        clusters_by_article = {}
        for article_id, group in itertools.groupby(points_sorted, key=lambda p: p.payload.get('original_id')):
            if article_id:
                clusters_by_article[article_id] = [point.payload.get('cluster_id', -1) for point in group]

        dominant_clusters = {}
        for article_id, cluster_list in clusters_by_article.items():
            if not cluster_list:
                dominant_clusters[article_id] = -1
            else:
                most_common = Counter(cluster_list).most_common(1)[0]
                dominant_clusters[article_id] = most_common[0]
        logging.info("Calcul des clusters dominants terminé.")
        return jsonify(dominant_clusters), 200
    except Exception as e:
        logging.error(f"Erreur lors du traitement des clusters : {e}")
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500