from sentence_transformers import SentenceTransformer
from typing import List

# Dictionnaire cache pour éviter de recharger les modèles plusieurs fois
_models = {}

# CHANGEMENT ICI : Le nouveau modèle par défaut
DEFAULT_MODEL = "OrdalieTech/Solon-embeddings-large-0.1"


def load_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """
    Charge et met en cache le modèle SentenceTransformer.
    """
    if model_name not in _models:
        print(f"Chargement du modèle {model_name}...")
        # Note : ce modèle est grand, le premier chargement peut être long.
        _models[model_name] = SentenceTransformer(model_name)
    return _models[model_name]


def get_embedding(text: str, model_name: str = DEFAULT_MODEL, is_query: bool = False) -> List[float]:
    """
    Retourne le vecteur embedding pour UN SEUL texte.
    
    Args:
        text (str): Le texte à vectoriser.
        model_name (str): Le nom du modèle Hugging Face.
        is_query (bool): Mettre à True si le texte est une requête de recherche.
    """
    # CHANGEMENT ICI : Logique pour ajouter le préfixe si c'est une requête
    if is_query:
        text = "query: " + text
        
    model = load_model(model_name)
    return model.encode(text).tolist()


def get_embeddings_batch(texts: List[str], model_name: str = DEFAULT_MODEL, is_query: bool = False) -> List[List[float]]:
    """
    Retourne une liste de vecteurs embeddings pour une LISTE de textes.
    
    Args:
        texts (List[str]): La liste de textes à vectoriser.
        model_name (str): Le nom du modèle Hugging Face.
        is_query (bool): Mettre à True si les textes sont des requêtes de recherche.
    """
    # CHANGEMENT ICI : Logique pour ajouter le préfixe si ce sont des requêtes
    if is_query:
        texts = ["query: " + t for t in texts]
        
    model = load_model(model_name)
    return model.encode(texts).tolist()