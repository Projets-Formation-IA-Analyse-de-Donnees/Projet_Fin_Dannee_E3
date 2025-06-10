from flask import request, abort
import os

API_KEY = os.getenv("API_KEY")

# --- Decorateur clef API ---
def require_api_key():
    """
    Décorateur pour sécuriser les endpoints Flask en exigeant une clé API valide.

    Ce décorateur vérifie la présence et la validité d'une clé API dans les en-têtes de la requête HTTP.
    Si la clé API est manquante ou invalide, il renvoie une réponse d'erreur HTTP 403.
    Si la clé API est valide, il permet l'exécution de la fonction décorée.

    Retourne:
        function: Une fonction wrapper qui sécurise l'accès à l'endpoint Flask.
    """
    def wrapper(fn):
        def decorated(*args, **kwargs):
            if request.headers.get('x-api-key') != API_KEY:
                abort(403, "Clé API invalide ou manquante.")
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper
