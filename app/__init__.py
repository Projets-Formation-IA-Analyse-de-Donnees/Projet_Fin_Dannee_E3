from flask import Flask
from app.routes.modele_routes import modele_bp
from app.embedding_cache import load_embedding_cache 
from app.modele_cache import load_model

def create_app():
    app = Flask(__name__)

    app.register_blueprint(modele_bp)
    load_embedding_cache()
    load_model()
    
    
    return app
