import os
import time
import numpy as np
import hdbscan
from collections import Counter
from qdrant_client import QdrantClient
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score
import umap.umap_ as umap # Assurez-vous d'avoir installé 'umap-learn'

# -------------------------------
# CONFIG QDRANT
# -------------------------------
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "articles" # Assurez-vous que c'est bien la collection avec les bons embeddings !

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# -------------------------------
# 1. Récupération et nettoyage des embeddings (INCHANGÉ)
# -------------------------------
def get_embeddings_from_qdrant(filter_code=None):
    """Récupère tous les vecteurs valides de Qdrant."""
    vectors, ids, payloads = [], [], []
    total_points, invalid_vectors = 0, 0

    print("🚀 Démarrage de la récupération des vecteurs depuis Qdrant...")
    
    # Utilisation de scroll pour gérer de grands volumes de données
    try:
        scroll_result = client.scroll(
            collection_name=COLLECTION_NAME,
            with_payload=True,
            with_vectors=True,
            limit=1000
        )
        
        # Le résultat est maintenant une tuple (points, next_page_offset)
        current_points = scroll_result[0]
        next_page = scroll_result[1]

        while current_points:
            for point in current_points:
                total_points += 1
                vec = point.vector
                
                # Appliquer le filtre si spécifié
                if filter_code and point.payload.get("code_parent") != filter_code:
                    continue

                # Validation robuste du vecteur
                if (
                    isinstance(vec, list)
                    and len(vec) > 0 # Vérifier que la liste n'est pas vide
                    and not any(v is None for v in vec)
                    and not any(np.isnan(v) for v in vec)
                ):
                    vectors.append(vec)
                    ids.append(point.id)
                    payloads.append(point.payload)
                else:
                    invalid_vectors += 1

            if not next_page:
                break
            
            scroll_result = client.scroll(
                collection_name=COLLECTION_NAME,
                with_payload=True,
                with_vectors=True,
                limit=1000,
                offset=next_page
            )
            current_points = scroll_result[0]
            next_page = scroll_result[1]
    
    except Exception as e:
        print(f"❌ Erreur lors de la communication avec Qdrant : {e}")
        return np.array([]), [], []


    print(f"✅ {len(vectors)} vecteurs valides sur {total_points} points récupérés.")
    if invalid_vectors:
        print(f"⚠️ {invalid_vectors} vecteurs invalides ont été filtrés.")
        
    return np.array(vectors), ids, payloads


# -------------------------------
# 2. Pipeline de Clustering : UMAP + HDBSCAN (NOUVEAU)
# -------------------------------
def run_clustering_pipeline(X_original_normalized, umap_params, hdbscan_params):
    """
    Exécute le pipeline complet : UMAP pour la réduction, puis HDBSCAN pour le clustering.
    Retourne les labels et le score silhouette.
    """
    
    # --- Étape A : Réduction de dimensionnalité avec UMAP ---
    print(f"🔄 [UMAP] Réduction vers {umap_params['n_components']} dimensions...")
    
    reducer = umap.UMAP(
        n_neighbors=umap_params['n_neighbors'],
        n_components=umap_params['n_components'],
        min_dist=umap_params['min_dist'],
        metric='cosine',  # La meilleure métrique pour les embeddings sémantiques
        random_state=42   # Garantit la reproductibilité des résultats
    )
    X_reduced = reducer.fit_transform(X_original_normalized)
    
    # --- Étape B : Clustering avec HDBSCAN sur les données réduites ---
    print(f"🔄 [HDBSCAN] Détection des clusters...")
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=hdbscan_params['min_cluster_size'],
        min_samples=hdbscan_params.get('min_samples'), # min_samples est optionnel
        metric=hdbscan_params['metric'], # 'euclidean' est efficace sur les données réduites par UMAP
        cluster_selection_epsilon=hdbscan_params.get('cluster_selection_epsilon', 0.0)
    )
    labels = clusterer.fit_predict(X_reduced)

    # --- Étape C : Évaluation ---
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    silhouette = -1 # Score par défaut si le clustering échoue
    if n_clusters > 1:
        # Le score silhouette est le plus pertinent sur les données que le clusterer a vues
        silhouette = silhouette_score(X_reduced, labels)

    cluster_sizes = Counter(labels[labels != -1])
    avg_size = np.mean(list(cluster_sizes.values())) if cluster_sizes else 0

    print("\n--- Résultats pour cette configuration ---")
    print(f"📊 Clusters trouvés : {n_clusters}")
    print(f"🔇 Articles isolés (bruit) : {n_noise} ({n_noise / len(labels):.1%})")
    print(f"📏 Taille moyenne des clusters : {avg_size:.2f}")
    print(f"🏆 Score Silhouette (sur données réduites) : {silhouette:.3f}")
    
    return labels, silhouette


# -------------------------------
# 3. Benchmark et Utilisation (MIS À JOUR)
# -------------------------------
if __name__ == "__main__":
    
    # --- Étape 1 : Chargement et préparation des données ---
    # On ne le fait qu'une seule fois pour tout le benchmark.
    vectors, ids, payloads = get_embeddings_from_qdrant(filter_code="LEGITEXT000006071307")
    
    if vectors.shape[0] < 10:
        print("❌ Pas assez de vecteurs pour lancer le clustering. Arrêt du script.")
    else:
        # La normalisation est cruciale avant UMAP avec la métrique 'cosine'
        print("\n📏 Normalisation des vecteurs originaux...")
        vectors_normalized = normalize(vectors)

        # --- Étape 2 : Définition des configurations à tester ---
        # Chaque configuration est un dictionnaire avec des paramètres pour UMAP et HDBSCAN.
        configs_to_test = [
            # Config équilibrée, bon point de départ
            {
                "umap": {"n_neighbors": 15, "n_components": 10, "min_dist": 0.0},
                "hdbscan": {"min_cluster_size": 10, "min_samples": 3, "metric": "euclidean"}
            },
            # Vise des clusters plus petits et plus nombreux
            {
                "umap": {"n_neighbors": 10, "n_components": 5, "min_dist": 0.0},
                "hdbscan": {"min_cluster_size": 5, "min_samples": 1, "metric": "euclidean"}
            },
            # Vise des clusters plus larges et une vision plus globale
            {
                "umap": {"n_neighbors": 50, "n_components": 15, "min_dist": 0.1},
                "hdbscan": {"min_cluster_size": 15, "min_samples": 5, "metric": "euclidean"}
            },
            # Autre variation pour des clusters très denses
             {
                "umap": {"n_neighbors": 20, "n_components": 8, "min_dist": 0.0},
                "hdbscan": {"min_cluster_size": 12, "min_samples": None, "metric": "euclidean"}
            },
        ]
        
        best_score = -1
        best_config = None
        best_labels = None
        
        # --- Étape 3 : Lancement du benchmark ---
        start_time_benchmark = time.time()
        for i, cfg in enumerate(configs_to_test):
            print(f"\n============================== CONFIGURATION {i+1}/{len(configs_to_test)} ==============================")
            print(f"UMAP params: {cfg['umap']}")
            print(f"HDBSCAN params: {cfg['hdbscan']}")
            
            labels, silhouette = run_clustering_pipeline(
                vectors_normalized, 
                umap_params=cfg["umap"], 
                hdbscan_params=cfg["hdbscan"]
            )
            
            # On cherche la configuration qui maximise le score Silhouette
            if silhouette > best_score:
                best_score = silhouette
                best_config = cfg
                best_labels = labels

        elapsed_benchmark = time.time() - start_time_benchmark
        print(f"\n\n============================== FIN DU BENCHMARK ({elapsed_benchmark:.2f}s) ==============================")
        print("✨ Résultat final ✨")
        
        if best_config:
            print(f"🏆 Meilleure configuration trouvée :")
            print(f"   - UMAP: {best_config['umap']}")
            print(f"   - HDBSCAN: {best_config['hdbscan']}")
            print(f"   - Score Silhouette : {best_score:.4f}")

            # --- Étape 4 : Analyse optionnelle des meilleurs clusters ---
            if best_labels is not None:
                print("\n🔍 Analyse des clusters de la meilleure configuration :")
                cluster_sizes = Counter(best_labels)
                # Afficher les 5 plus grands clusters (en excluant le bruit -1)
                if -1 in cluster_sizes:
                    del cluster_sizes[-1]
                
                print(f"   -> {len(cluster_sizes)} clusters trouvés.")
                for cluster_id, size in cluster_sizes.most_common(5):
                    print(f"\n   --- Cluster #{cluster_id} (Taille: {size}) ---")
                    # Retrouver les titres des 5 premiers articles de ce cluster
                    indices_in_cluster = [i for i, label in enumerate(best_labels) if label == cluster_id]
                    for j in range(min(5, len(indices_in_cluster))):
                        article_index = indices_in_cluster[j]
                        article_payload = payloads[article_index]
                        print(f"     - Article: {article_payload.get('title', 'N/A')} (ID: {ids[article_index]})")
        else:
            print("Aucune configuration n'a produit de résultat valide.")