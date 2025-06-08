import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers.utils import logging as hf_logging

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
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
logger.info("Initialisation terminée")
def connect_arango_db():
    """Connexion à la base ArangoDB."""
    logger.info("Connexion à ArangoDB...")
    try:
        client = ArangoClient(hosts=f"http://{os.getenv('ARANGO_HOST')}")
        db = client.db(
            "legifrance",
            username=os.getenv("ARANGO_USER"),
            password=os.getenv("ARANGO_PASSWORD")
        )
        logger.info("Connexion etablie.")
    except Exception as e:
        logger.warning(f"Erreur de connexion a ArangoDB:{e}")

    return db

def generer_embeddings(db):
    """Genere et insere les embeddings pour les articles avec contenu."""
    articles = db.collection("articles")
    embeddings = db.collection("embeddings")

    count = 0
    cursor = articles.all()
    for doc in tqdm(cursor, desc="Génération des embeddings"):
        _key = doc["_key"]
        content = doc.get("content")

        if content and not embeddings.has(_key):
            vecteur = model.encode(content).tolist()
            embeddings.insert({"_key": _key, "embedding": vecteur})
            count += 1

    logger.info(f"{count} nouveaux embeddings inseres dans ArangoDB.")

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
    

    generer_embeddings(db)
    verifier_articles_sans_embeddings(db)

if __name__ == "__main__":
    main()
