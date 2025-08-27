from flask import Flask,Response
from .routes.search import search_bp
from .routes.cluster import clusters_bp
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def create_app():
    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    app.register_blueprint(search_bp)
    app.register_blueprint(clusters_bp)
    
    @app.route('/metrics')
    def get_metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    return app










