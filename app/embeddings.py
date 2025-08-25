from sentence_transformers import SentenceTransformer
from typing import List
import logging


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("Embeddings.log", mode='w'), # 'w' pour écraser le log à chaque lancement
                        logging.StreamHandler()
                    ])

_models = {}


DEFAULT_MODEL = "OrdalieTech/Solon-embeddings-large-0.1"


def load_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """
    Charge et met en cache le modèle SentenceTransformer.
    """
    if model_name not in _models:
        logging.info(f"Chargement du modèle {model_name}...")
        _models[model_name] = SentenceTransformer(model_name)
    logging.info(f"Modèle {model_name} chargé depuis le cache.")
    return _models[model_name]


def get_embedding(text: str, model_name: str = DEFAULT_MODEL, is_query: bool = False) -> List[float]:
    """
    Retourne le vecteur embedding pour UN SEUL texte.
    
    Args:
        text (str): Le texte à vectoriser.
        model_name (str): Le nom du modèle Hugging Face.
        is_query (bool): Mettre à True si le texte est une requête de recherche.
    """
    logging.info(f"Génération d'un embedding pour un texte (is_query={is_query})...")
    if is_query:
        text = "query: " + text
        
    model = load_model(model_name)
    logging.info("Embedding généré avec succès.")
    return model.encode(text).tolist()


def get_embeddings_batch(texts: List[str], model_name: str = DEFAULT_MODEL, is_query: bool = False) -> List[List[float]]:
    """
    Retourne une liste de vecteurs embeddings pour une LISTE de textes.
    
    Args:
        texts (List[str]): La liste de textes à vectoriser.
        model_name (str): Le nom du modèle Hugging Face.
        is_query (bool): Mettre à True si les textes sont des requêtes de recherche.
    """
    logging.info(f"Génération d'embeddings pour un lot de {len(texts)} textes (is_query={is_query})...")
    if is_query:
        texts = ["query: " + t for t in texts]
        
    model = load_model(model_name)
    logging.info("Embeddings générés avec succès.")
    return model.encode(texts).tolist()