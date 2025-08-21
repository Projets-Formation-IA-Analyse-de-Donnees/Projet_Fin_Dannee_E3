from flask import Flask
from .routes.search import search_bp
from .routes.cluster import clusters_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(search_bp)
    app.register_blueprint(clusters_bp)
   
    return app
