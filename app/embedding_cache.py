# app/embedding_cache.py
import numpy as np
from DB_Connexion import connect_arango_db
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBEDDINGS_ARRAY = None
ARTICLE_IDS = None

def load_embedding_cache():
    global EMBEDDINGS_ARRAY, ARTICLE_IDS

    db = connect_arango_db()
    if db is None:
        logger.error("Connexion à la base ArangoDB échouée.")
        return

    embeddings_col = db.collection("embeddings")
    logger.info("Chargement des embeddings en mémoire...")

    all_embeddings = []
    all_ids = []

    for doc in embeddings_col.all():
        all_ids.append(doc["_key"])
        all_embeddings.append(doc["embedding"])

    if not all_embeddings:
        logger.warning("Aucun embedding trouvé.")
        return

    EMBEDDINGS_ARRAY = np.array(all_embeddings)
    ARTICLE_IDS = all_ids

    logger.info(f"{len(ARTICLE_IDS)} embeddings chargés dans le cache.")
