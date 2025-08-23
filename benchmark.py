import logging
import time
import os
import numpy as np
import itertools
import requests
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import umap.umap_ as umap
import hdbscan
import mlflow
from sentence_transformers import SentenceTransformer
from typing import List





E1_API_ALL_ARTICLES_URL = os.getenv("URL_ARTICLE")
E1_API_KEY = os.getenv("API_KEY_ETL")


CODE_IDS_TO_TEST = [
    "LEGITEXT000006071307", 
    "LEGITEXT000044416551", 
]


EMBEDDING_MODELS_TO_TEST = [
    "OrdalieTech/Solon-embeddings-large-0.1",      
    "camembert/camembert-base",                     
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", 
    "sentence-transformers/all-MiniLM-L6-v2",       
]

DIM_REDUCTION_GRID = {
    "UMAP": [
        {"n_neighbors": 15, "n_components": 30},
        {"n_neighbors": 30, "n_components": 30},
        {"n_neighbors": 50, "n_components": 30},
        {"n_neighbors": 15, "n_components": 10},
        {"n_neighbors": 30, "n_components": 10},
        {"n_neighbors": 50, "n_components": 10}
    ],
    "PCA": [
        {"n_components": 10},
        {"n_components": 20},
        {"n_components": 30},
        {"n_components": 50},
    ]
}

CLUSTERING_GRID = {
    "HDBSCAN": [
        {"min_cluster_size": 34, "min_samples": 29},
        {"min_cluster_size": 82, "min_samples": 13},
        {"min_cluster_size": 100, "min_samples": 25},
        {"min_cluster_size": 80, "min_samples": 30},
    ],
    "KMeans": [
        {"n_clusters": 10},
        {"n_clusters": 25},
        {"n_clusters": 50}, 
    ]
}

    
    


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_all_articles_from_api() -> List[dict]:
    """Appelle l'API E1 une seule fois pour récupérer TOUS les articles."""
    logging.info(f"Appel de l'API E1 sur {E1_API_ALL_ARTICLES_URL} pour récupérer tous les articles...")
    headers = {'x-api-key': E1_API_KEY}
    try:
        response = requests.get(E1_API_ALL_ARTICLES_URL, headers=headers, timeout=180)
        response.raise_for_status()
        articles = response.json()
        logging.info(f"{len(articles)} articles au total ont été récupérés avec succès.")
        return articles
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de l'appel à l'API E1 : {e}")
        return []

_models_cache = {}
def get_embeddings_batch(texts: List[str], model_name: str) -> List[List[float]]:
    if model_name not in _models_cache:
        logging.info(f"Chargement du modèle SentenceTransformer: {model_name}...")
        _models_cache[model_name] = SentenceTransformer(model_name)
    model = _models_cache[model_name]
    return model.encode(texts, show_progress_bar=True).tolist()

def chunk_text_robust(content: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    if not isinstance(content, str) or not content.strip(): return []
    chunks_by_paragraph = content.split('\n\n')
    final_chunks = []
    for paragraph in chunks_by_paragraph:
        paragraph = paragraph.strip()
        if not paragraph: continue
        if len(paragraph) > chunk_size:
            start_index = 0
            while start_index < len(paragraph):
                final_chunks.append(paragraph[start_index:start_index + chunk_size])
                start_index += chunk_size - chunk_overlap
        else:
            final_chunks.append(paragraph)
    return final_chunks


def run_experiment(code_id, embedding_model, reducer_name, reducer_params, clusterer_name, clusterer_params, vectors):
    run_name = f"{embedding_model.split('/')[-1]}_{reducer_name}_{clusterer_name}"
    logging.info(f"--- Running: {run_name} with params {reducer_params} & {clusterer_params} ---")
    
    mlflow.set_experiment(f"Benchmark_{code_id}")
    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("code_id", code_id)
        mlflow.log_param("embedding_model", embedding_model)
        mlflow.log_param("reducer_algorithm", reducer_name)
        mlflow.log_params(reducer_params)
        mlflow.log_param("clustering_algorithm", clusterer_name)
        mlflow.log_params(clusterer_params)

        start_time = time.time()
        
        if reducer_name == "UMAP":
            reducer = umap.UMAP(**reducer_params, metric='cosine', random_state=42)
        elif reducer_name == "PCA":
            reducer = PCA(**reducer_params, random_state=42)
        else:
            raise ValueError(f"Reducer inconnu: {reducer_name}")
        embeddings_reduced = reducer.fit_transform(vectors)
        
        if clusterer_name == "HDBSCAN":
            clusterer = hdbscan.HDBSCAN(**clusterer_params, metric='euclidean', gen_min_span_tree=True)
        elif clusterer_name == "KMeans":
            clusterer = KMeans(**clusterer_params, random_state=42, n_init='auto')
        else:
            raise ValueError(f"Clusterer inconnu: {clusterer_name}")
        cluster_labels = clusterer.fit_predict(embeddings_reduced)

        processing_time = time.time() - start_time
        mlflow.log_metric("processing_time_sec", processing_time)

        n_clusters_set = set(cluster_labels)
        n_clusters = len(n_clusters_set) - (1 if -1 in n_clusters_set else 0)
        mlflow.log_metric("num_clusters_found", n_clusters if n_clusters > 0 else clusterer_params.get('n_clusters', 0))

        if clusterer_name == "HDBSCAN":
            noise_percentage = np.sum(cluster_labels == -1) / len(cluster_labels) * 100 if len(cluster_labels) > 0 else 0
            mlflow.log_metric("noise_percentage", noise_percentage)
            dbcv_score = -1.0
            try:
                if n_clusters > 1:
                    dbcv_score = clusterer.relative_validity_
                    mlflow.log_metric("dbcv_score", dbcv_score)
            except Exception:
                logging.warning("Score DBCV non calculable.")
            logging.info(f"    -> Résultat: DBCV={dbcv_score:.4f}, Clusters={n_clusters}, Bruit={noise_percentage:.2f}%")
        
        elif clusterer_name == "KMeans":
            silhouette = -1.0
            if n_clusters > 1:
                silhouette = silhouette_score(embeddings_reduced, cluster_labels)
                mlflow.log_metric("silhouette_score", silhouette)
            logging.info(f"    -> Résultat: Silhouette={silhouette:.4f}, Clusters={n_clusters}")




if __name__ == "__main__":
    setup_logging()
    
    logging.info("Étape 1 : Récupération de tous les articles depuis l'API E1...")
    all_articles = get_all_articles_from_api()
    
    if not all_articles:
        logging.error("Aucun article récupéré. Le benchmark ne peut pas continuer.")
    else:
        reducer_configs = [(name, params) for name, p_list in DIM_REDUCTION_GRID.items() for params in p_list]
        clusterer_configs = [(name, params) for name, p_list in CLUSTERING_GRID.items() for params in p_list]
        
        for code_id in CODE_IDS_TO_TEST:
            logging.info(f"\n{'#'*20} DÉMARRAGE DU BENCHMARK POUR LE CODE : {code_id} {'#'*20}")
            
            articles_for_code = [article for article in all_articles if article and article.get("code_parent") == code_id]
            
            if not articles_for_code:
                logging.warning(f"Aucun article trouvé pour le code {code_id} dans les données récupérées. Passage au suivant.")
                continue

            all_chunks = [chunk for article in articles_for_code if article.get("content") for chunk in chunk_text_robust(article["content"])]
            if not all_chunks:
                logging.warning(f"Aucun contenu textuel (chunk) à traiter pour le code {code_id}. Passage au suivant.")
                continue
            
            logging.info(f"Total de {len(all_chunks)} chunks à traiter pour le code {code_id}.")

            for model_name in EMBEDDING_MODELS_TO_TEST:
                logging.info(f"  Génération des embeddings avec le modèle : {model_name}")
                vectors = np.array(get_embeddings_batch(all_chunks, model_name=model_name))
                
                for reducer_config, clusterer_config in itertools.product(reducer_configs, clusterer_configs):
                    reducer_name, reducer_params = reducer_config
                    clusterer_name, clusterer_params = clusterer_config
                    run_experiment(code_id, model_name, reducer_name, reducer_params, clusterer_name, clusterer_params, vectors)

        logging.info(f"\n{'#'*20} BENCHMARKS TERMINÉS {'#'*20}")
