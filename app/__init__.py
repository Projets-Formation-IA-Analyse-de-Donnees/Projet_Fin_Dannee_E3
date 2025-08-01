from flask import Flask
from app.routes.arango_route import arango_bp
from app.routes.postgres_route import pg_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(pg_bp)
    app.register_blueprint(arango_bp)
    
    return app
