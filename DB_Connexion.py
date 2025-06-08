import os
from dotenv import load_dotenv
from arango import ArangoClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("Connexion.log", mode='w')
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()


def connect_arango_db():
    """Connexion à la base ArangoDB."""
    try:
        client = ArangoClient(hosts=f"http://{os.getenv('ARANGO_HOST')}")
        db = client.db(
            "legifrance",
            username=os.getenv("ARANGO_USER"),
            password=os.getenv("ARANGO_PASSWORD")
        )
        logger.info("Connexion à ArangoDB réussie.")
        return db
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à ArangoDB : {e}")
        return None
