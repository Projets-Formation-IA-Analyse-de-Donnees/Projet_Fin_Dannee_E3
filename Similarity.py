import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from DB_Connexion import connect_arango_db

# Chargement des variables d’environnement
load_dotenv()

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("recherche_semantique.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Initialisation du modèle
logger.info("Initialisation du modèle d'embedding.")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
logger.info("Modèle chargé.")



def rechercher_articles_proches(texte, db, top_k=5):
    """Encode un texte et retourne les articles les plus proches dans la base."""
    logger.info("Génération de l'embedding pour le texte utilisateur.")
    embedding_texte = model.encode([texte])

    embeddings_col = db.collection("embeddings")
    articles_col = db.collection("articles")

    logger.info("Chargement des embeddings de la base.")
    embeddings_db = []
    ids = []

    for doc in embeddings_col.all():
        embeddings_db.append(doc["embedding"])
        ids.append(doc["_key"])

    logger.info(f"{len(embeddings_db)} embeddings chargés.")

    logger.info("Calcul des similarités cosinus.")
    sims = cosine_similarity(embedding_texte, embeddings_db)[0]
    top_indices = np.argsort(sims)[::-1][:top_k]

    logger.info("Récupération des articles les plus proches.")
    resultats = []
    for idx in top_indices:
        key = ids[idx]
        article = articles_col.get(key)

        if article:
            titre = article.get("num") or key
            contenu = article.get("content", "")
            resultats.append({
                "num": titre,
                "titre": titre,
                "content": contenu,
                "similarite": float(sims[idx])
            })
    else:
        logger.warning(f"Aucun article trouvé pour la clé : {key}")


    return resultats

def main():
    db = connect_arango_db()
    if db is None:
        logger.error("Impossible de se connecter à la base de données.")
        return

    texte_utilisateur = "sécurité des systèmes d'information"
    logger.info(f"Recherche d'articles similaires au texte : {texte_utilisateur}")
    resultats = rechercher_articles_proches(texte_utilisateur, db)

    logger.info("Résultats :")
    for res in resultats:
        logger.info(f"Article {res['titre']} ({res['similarite']:.4f})\nExtrait : {res['content'][:150]}...\n")


if __name__ == "__main__":
    main()
