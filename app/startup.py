import os
import requests
import uuid
from qdrant_client import QdrantClient, models
from app.embeddings import get_embeddings_batch, load_model
import logging 

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("Startup.log", mode='w'), # 'w' pour écraser le log à chaque lancement
                        logging.StreamHandler()
                    ])


QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = "articles_chunked" 
URL_ARTICLE = os.getenv("URL_ARTICLE")
API_KEY = os.getenv("API_KEY_ETL") 


client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_all_articles_from_api():
    """Récupère tous les articles depuis l'API de E1."""
    headers = { 'x-api-key': API_KEY }
    try:
        
        response = requests.get(URL_ARTICLE, headers=headers, timeout=60) 
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la récupération des articles: {e}")
        return None

def chunk_text_robust(content: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Découpe un texte en chunks de taille fixe avec un chevauchement.
    Cette méthode est robuste aux variations de formatage.
    """
    if not isinstance(content, str) or not content.strip():
        return []

   
    chunks_by_paragraph = content.split('\n\n')
    
    final_chunks = []
    for paragraph in chunks_by_paragraph:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Si un paragraphe est plus grand que notre taille cible, on le découpe
        if len(paragraph) > chunk_size:
            start_index = 0
            while start_index < len(paragraph):
                end_index = start_index + chunk_size
                final_chunks.append(paragraph[start_index:end_index])
                start_index += chunk_size - chunk_overlap
        else:
            final_chunks.append(paragraph)
            
    return final_chunks

def initialize_vector_index():
    """
    Initialise la collection de vecteurs dans Qdrant et la peuple avec des chunks d'articles.
    """
    logging.info("Initialisation du service de modèle...")
    model = load_model()
    
    try:
        logging.info(f"Tentative de recréation de la collection '{COLLECTION_NAME}'...")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=model.get_sentence_embedding_dimension(), 
                distance=models.Distance.COSINE
            )
        )
        logging.info(f"Collection '{COLLECTION_NAME}' créée/réinitialisée.")
    except Exception as e:
        logging.error(f"Erreur critique lors de la création de la collection: {e}")
        return

    logging.info("Démarrage de la récupération des articles...")
    articles = get_all_articles_from_api()
    if not articles:
        logging.warning("Aucun article à indexer.")
        return

    logging.info("Démarrage du processus de segmentation (chunking)...")
    texts_to_embed = []
    metadata_for_points = []

    for article in articles:
        content = article.get("content")
        if not content:
            continue
        
        chunks = chunk_text_robust(content, chunk_size=1000, chunk_overlap=200)
        
        for i, chunk_text in enumerate(chunks):
            texts_to_embed.append(chunk_text)
            metadata_for_points.append({
                "chunk_text": chunk_text,
                "chunk_index": i, 
                "title": article.get("num"),
                "original_id": article.get("_key"),
                "code_parent": article.get("code_parent")
            })
    
    if not texts_to_embed:
        logging.warning("Aucun contenu textuel trouvé après segmentation.")
        return
        
    logging.info(f"{len(articles)} articles ont été segmentés en {len(texts_to_embed)} chunks.")

   
    logging.info(f"Vectorisation par batch de {len(texts_to_embed)} chunks...")
    vectors = get_embeddings_batch(texts_to_embed)
    
   
    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=metadata 
        ) for vector, metadata in zip(vectors, metadata_for_points)
    ]
    

    if points:
        BATCH_SIZE = 128
        logging.info(f"Démarrage de l'insertion de {len(points)} points (chunks)...")
        try:
           
            client.upload_points(
                collection_name=COLLECTION_NAME,
                points=points,
                batch_size=BATCH_SIZE,
                parallel=2 
            )
            logging.info(f"Indexation terminée. {len(points)} chunks insérés.")
        except Exception as e:
            logging.error(f"Erreur lors de l'insertion des vecteurs dans Qdrant: {e}")


if __name__ == "__main__":
    logging.info("--- Lancement du script d'initialisation (avec chunking) ---")
    initialize_vector_index()
    logging.info("--- Script terminé ---")