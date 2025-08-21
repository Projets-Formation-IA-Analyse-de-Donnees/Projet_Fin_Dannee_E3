import os
import numpy as np
import umap.umap_ as umap
import hdbscan
import logging
from qdrant_client import QdrantClient, models


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT"))
COLLECTION_NAME = "articles_chunked"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT,timeout=60)

def fetch_points_by_code(collection_name: str, code_id: str):
    """
    Récupère tous les points (avec vecteurs et payloads) pour un code de loi spécifique.
    """
    logging.info(f"Étape 1/4 : Récupération des points pour le code '{code_id}'...")
    
    scroll_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="code_parent",
                match=models.MatchValue(value=code_id)
            )
        ]
    )
    
  
    all_points = client.scroll(
        collection_name=collection_name,
        scroll_filter=scroll_filter,
        limit=10000, 
        with_payload=True, 
        with_vectors=True
    )[0] 

    logging.info(f"{len(all_points)} points récupérés pour le code '{code_id}'.")
    return all_points

def main(code_id: str, umap_params: dict, hdbscan_params: dict):
    """
    Fonction principale pour l'exécution du clustering sur un code spécifique
    et la mise à jour non-destructive des données.
    """
    logging.info(f"--- Démarrage du clustering pour le code : {code_id} ---")
    
    points = fetch_points_by_code(COLLECTION_NAME, code_id)
    if not points:
        logging.warning(f"Aucun point trouvé pour le code {code_id}. Le traitement est ignoré.")
        return
        
    vectors = np.array([p.vector for p in points])

    logging.info("Étape 2/4 : Réduction de dimensionnalité avec UMAP...")
    reducer = umap.UMAP(
        n_neighbors=umap_params['n_neighbors'],
        n_components=umap_params['n_components'],
        metric='cosine', 
        random_state=42
    )
    embeddings_reduced = reducer.fit_transform(vectors)
    logging.info("Réduction terminée.")

    logging.info("Étape 3/4 : Clustering avec HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=hdbscan_params['min_cluster_size'],
        min_samples=hdbscan_params['min_samples'],
        metric='euclidean',
        gen_min_span_tree=True,
        prediction_data=True
    )
    cluster_labels = clusterer.fit_predict(embeddings_reduced)
    
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    logging.info(f"HDBSCAN a trouvé {n_clusters} clusters (hors bruit).")
    try:
        if n_clusters > 0:
            score = clusterer.relative_validity_
            logging.info(f"Score de qualité du clustering (DBCV) : {score:.4f}")
        else:
            logging.info("Score de qualité non calculé (aucun cluster trouvé).")
    except Exception as e:
        logging.warning(f"Impossible de calculer le score DBCV : {e}")

    logging.info("Étape 4/4 : Préparation de la mise à jour non-destructive...")
    
    points_to_update = []
    for point, label in zip(points, cluster_labels):
     
        payload_base = point.payload or {}
        
        updated_payload = {
            "chunk_text": payload_base.get("chunk_text"),
            "chunk_index": payload_base.get("chunk_index"),
            "title": payload_base.get("title"),
            "original_id": payload_base.get("original_id"),
            "code_parent": payload_base.get("code_parent"),
            "cluster_id": int(label) 
        }
        
        points_to_update.append(
            models.PointStruct(
                id=point.id,
                vector=point.vector,
                payload=updated_payload
            )
        )
    try:
        logging.info(f"Mise à jour des {len(points_to_update)} points dans Qdrant par lots...")
        BATCH_SIZE = 512 

        for i in range(0, len(points_to_update), BATCH_SIZE):
            batch = points_to_update[i:i + BATCH_SIZE]
            current_batch_num = i // BATCH_SIZE + 1
            total_batches = (len(points_to_update) + BATCH_SIZE - 1) // BATCH_SIZE
            
            logging.info(f" -> Envoi du lot {current_batch_num}/{total_batches}...")
            client.upsert(collection_name=COLLECTION_NAME, points=batch, wait=True)
        
        logging.info("Mise à jour de la base de données terminée.")
    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour des points dans Qdrant : {e}")
        raise e


if __name__ == "__main__":
    
   
    
  
    code_defense_id = "LEGITEXT000006071307" 
    defense_umap_params = {'n_neighbors': 15, 'n_components': 30}
    defense_hdbscan_params = {'min_cluster_size': 82, 'min_samples': 13}

   
    code_fonc_pub_id = "LEGITEXT000044416551" 
    fonc_pub_umap_params = {'n_neighbors': 15, 'n_components': 30} 
    fonc_pub_hdbscan_params = {'min_cluster_size': 34, 'min_samples': 29} 
    
    
    try:
        main(code_id=code_defense_id, umap_params=defense_umap_params, hdbscan_params=defense_hdbscan_params)
        main(code_id=code_fonc_pub_id, umap_params=fonc_pub_umap_params, hdbscan_params=fonc_pub_hdbscan_params)
        logging.info("--- Tous les traitements de clustering sont terminés avec succès. ---")
    except Exception as e:
        logging.error(f"Le script de clustering s'est arrêté à cause d'une erreur : {e}")

