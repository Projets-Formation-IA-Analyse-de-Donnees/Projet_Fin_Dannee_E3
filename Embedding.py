import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers.utils import logging as hf_logging
from DB_Connexion import connect_arango_db
hf_logging.set_verbosity_error()

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("embedding_generation.log", mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Initialisation du modèle d'embedding
logger.info("Initialisation du modèle d'embedding.")
try:    
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    logger.info("Initialisation terminée")
except Exception as e:
    logger.warning("Erreur lors d el initialisation")
    pass


def generer_embeddings(db, batch_size=32):
    """Génère et insère les embeddings en batch pour les articles avec contenu."""
    articles = db.collection("articles")
    embeddings = db.collection("embeddings")

    docs_to_encode = []
    keys_to_encode = []

    count = 0
    cursor = articles.all()

    for doc in tqdm(cursor, desc="Préparation des textes"):
        _key = doc["_key"]
        content = doc.get("content")

        if content and not embeddings.has(_key):
            docs_to_encode.append(content)
            keys_to_encode.append(_key)

           
            if len(docs_to_encode) >= batch_size:
                encoded = model.encode(docs_to_encode)
                logger.info(f"Batch de {len(docs_to_encode)} articles encodé.")
                for _key, vector in zip(keys_to_encode, encoded):
                    embeddings.insert({"_key": _key, "embedding": vector.tolist()})
                    count += 1
                docs_to_encode = []
                keys_to_encode = []

    
    if docs_to_encode:
        encoded = model.encode(docs_to_encode)
        for _key, vector in zip(keys_to_encode, encoded):
            embeddings.insert({"_key": _key, "embedding": vector.tolist()})
            count += 1

    logger.info(f"{count} embeddings insérés en batch dans ArangoDB.")


def verifier_articles_sans_embeddings(db):
    """Affiche les articles avec contenu mais sans embedding."""
    articles = db.collection("articles")
    embeddings = db.collection("embeddings")

    sans_embedding = [
        doc["_key"]
        for doc in articles.all()
        if doc.get("content") and not embeddings.has(doc["_key"])
    ]

    if sans_embedding:
        logger.warning(f"{len(sans_embedding)} article(s) avec contenu n'ont pas d'embedding.")
        logger.warning(f"Exemples : {sans_embedding[:5]}")
    else:
        logger.info("Tous les articles avec contenu ont un embedding.")

def main():
    db = connect_arango_db()
    if db is None:
        logger.error("Impossible de poursuivre sans connexion à ArangoDB.")
        return
    generer_embeddings(db)
    verifier_articles_sans_embeddings(db)

if __name__ == "__main__":
    main()
