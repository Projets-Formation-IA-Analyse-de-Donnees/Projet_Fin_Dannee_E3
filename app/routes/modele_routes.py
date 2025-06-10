from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from sklearn.metrics.pairwise import cosine_similarity
from DB_Connexion import connect_arango_db
import numpy as np
from dotenv import load_dotenv
from app import embedding_cache 
from app.modele_cache import load_model
import logging
import sys

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


modele_bp = Blueprint("modele", __name__, url_prefix="/modele")

embedding_cache.load_embedding_cache()
model = load_model()



@modele_bp.route("/recherche_semantique", methods=["POST"])
@require_api_key()
def recherche_semantique():
    texte = request.json.get("texte")
    if not texte:
        return jsonify({"error": "Texte requis"}), 400

    if embedding_cache.EMBEDDINGS_ARRAY is None:
        return jsonify({"error": "Cache non initialisé"}), 500

    try:
        if model is None:
            logger.error("Modèle non chargé.")
            return jsonify({"error": "Modèle non chargé"}), 500

        embedding_input = model.encode([texte])
    except Exception as e:
        logger.exception("Erreur lors du calcul de l'embedding :")
        return jsonify({"error": f"Erreur modèle : {str(e)}"}), 500

    sims = cosine_similarity(embedding_input, embedding_cache.EMBEDDINGS_ARRAY)[0]
    top_k = np.argsort(sims)[::-1][:5]

    db = connect_arango_db()
    articles_col = db.collection("articles")

    resultats = []
    for idx in top_k:
        article = articles_col.get(embedding_cache.ARTICLE_IDS[idx])
        resultats.append({
            "num": article.get("num"),
            'key': article.get("_key"),
            "titre": article.get("titre"),
            "content": article.get("content"),
            "similarite": float(sims[idx])
        })

    return jsonify(resultats)


