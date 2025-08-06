import os
import requests
import uuid
from qdrant_client import QdrantClient, models
from app.embeddings import get_embeddings_batch, load_model

# --- Variables d'Environnement ---
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = "articles"
URL_ARTICLE = os.getenv("URL_ARTICLE")
API_KEY = os.getenv("API_KEY_ETL") 

# --- Client Qdrant ---
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_all_articles_from_api():
    """Récupère tous les articles depuis l'API de E1."""
    headers = {
        'x-api-key': API_KEY
    }
    try:
        response = requests.get(URL_ARTICLE,headers=headers)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des articles: {e}")
        return None


def initialize_vector_index():
    """
    Initialise la collection de vecteurs dans Qdrant et la peuple si elle est vide.
    """
    # 1. Charger le modèle une seule fois pour obtenir sa configuration
    print("Initialisation du service de modèle...")
    model = load_model()
    
    # 2. Vérifier si la collection est déjà remplie
    try:
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        if collection_info.points_count > 0:
            print(f"Collection '{COLLECTION_NAME}' déjà remplie. Démarrage rapide.")
            return  # Arrête la fonction ici si le travail est déjà fait
    except Exception:
        # La collection n'existe probablement pas, on la crée ci-dessous
        print(f"Collection '{COLLECTION_NAME}' non trouvée ou vide. Tentative de création...")
        try:
            client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=model.get_sentence_embedding_dimension(), 
                    distance=models.Distance.COSINE
                )
            )
            print(f"Collection '{COLLECTION_NAME}' créée.")
        except Exception as e:
            print(f"Erreur lors de la création de la collection: {e}")
            return

    # 3. Si la collection était vide, lancer le processus d'indexation
    print("Démarrage du processus d'indexation...")
    articles = get_all_articles_from_api()
    if not articles:
        print("Aucun article à indexer.")
        return

    # 4. Préparer et vectoriser les données par batch
    valid_articles = [article for article in articles if article.get("content")]
    if not valid_articles:
        print("Aucun article avec du contenu valide trouvé.")
        return
        
    contents_to_embed = [article["content"] for article in valid_articles]
    
    print(f"Vectorisation par batch de {len(contents_to_embed)} articles...")
    vectors = get_embeddings_batch(contents_to_embed)
    
    # 5. Préparer les points pour l'insertion dans Qdrant
    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),  # On génère un nouvel ID au format UUID
            vector=vectors[i],
            payload={
                "title": a.get("num"),
                "original_id": a["_key"],
                "code_parent": a.get("code_parent")
            }
        ) for i, a in enumerate(valid_articles)
    ]



    
    
    # 6. Insérer les points dans la collection
    if points:
        BATCH_SIZE = 256  # On insère 256 points à la fois
        total_batches = (len(points) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Démarrage de l'insertion de {len(points)} vecteurs en {total_batches} paquets...")
        
        try:
            # On parcourt la liste de points par tranches de BATCH_SIZE
            for i in range(0, len(points), BATCH_SIZE):
                batch = points[i:i + BATCH_SIZE]
                print(f" -> Insertion du paquet {i//BATCH_SIZE + 1}/{total_batches}...")
                client.upsert(collection_name=COLLECTION_NAME, points=batch, wait=True)
            
            print(f"Indexation terminée. {len(points)} vecteurs insérés.")
        except Exception as e:
            print(f"Erreur lors de l'insertion des vecteurs dans Qdrant: {e}")


if __name__ == "__main__":
    print("--- Lancement du script d'initialisation ---")
    initialize_vector_index()
    print("--- Script terminé ---")