import json
import logging
from unittest.mock import patch
import app.startup

def mock_get_articles_from_api():
    logging.info("--- USING MOCKED API CALL --- Reading from local test_data.json")
    with open("app/test_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("--- CI Startup Script Initializing ---")

    with patch('app.startup.get_all_articles_from_api', new=mock_get_articles_from_api):
        app.startup.initialize_vector_index()

    logging.info("--- CI Startup Script Finished ---")