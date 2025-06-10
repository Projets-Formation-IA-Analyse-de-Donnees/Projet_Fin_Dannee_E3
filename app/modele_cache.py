from sentence_transformers import SentenceTransformer
import logging

# Initialisation du logger
logger = logging.getLogger(__name__)

MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        try:
            logger.info("Chargement du modèle SentenceTransformer...")
            MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            logger.info("Modèle chargé.")
        except Exception as e:
            logger.warning("Modele error:{e}")
            return None
    return MODEL
