import json
from unittest.mock import MagicMock # 

TEST_API_KEY = 'super-secret-test-key'

# --- Tests pour le endpoint /search ---

def test_search_endpoint_success(test_client):
    """Teste un appel réussi à /search avec une clé API valide."""
    headers = {'x-api-key': TEST_API_KEY, 'Content-Type': 'application/json'}
    payload = {'query': 'test de recherche'}
    response = test_client.post('/search', data=json.dumps(payload), headers=headers)
    
    assert response.status_code == 200
    assert response.is_json
    assert isinstance(response.get_json(), list)

def test_search_endpoint_missing_api_key(test_client):
    """Teste l'échec de /search sans clé API."""
    headers = {'Content-Type': 'application/json'}
    payload = {'query': 'test'}
    response = test_client.post('/search', data=json.dumps(payload), headers=headers)
    assert response.status_code == 403

def test_search_endpoint_invalid_api_key(test_client):
    """Teste l'échec de /search avec une clé API invalide."""
    headers = {'x-api-key': 'mauvaise-cle', 'Content-Type': 'application/json'}
    payload = {'query': 'test'}
    response = test_client.post('/search', data=json.dumps(payload), headers=headers)
    assert response.status_code == 403

def test_search_endpoint_bad_request(test_client):
    """Teste l'échec de /search avec une requête mal formée (sans 'query')."""
    headers = {'x-api-key': TEST_API_KEY, 'Content-Type': 'application/json'}
    payload = {'pas_la_bonne_cle': 'test'}
    response = test_client.post('/search', data=json.dumps(payload), headers=headers)
    assert response.status_code == 400

# --- Tests pour le endpoint /clusters_for_articles ---

def test_clusters_endpoint_success(test_client, mocker):
    """Teste un appel réussi à /clusters_for_articles en simulant la réponse de Qdrant."""
   
    mock_point = MagicMock()
    mock_point.payload = {'original_id': 'un_vrai_id_article_1', 'cluster_id': 1}

    
    mocker.patch(
        'app.routes.cluster.client.scroll', 
        return_value=([mock_point], None) 
    )

    headers = {'x-api-key': TEST_API_KEY, 'Content-Type': 'application/json'}
    payload = {'article_ids': ['un_vrai_id_article_1']} 

    response = test_client.post('/clusters_for_articles', data=json.dumps(payload), headers=headers)

    assert response.status_code == 200
    assert response.is_json
    response_data = response.get_json()
    assert response_data == {'un_vrai_id_article_1': 1}

def test_clusters_endpoint_bad_request(test_client):
    """Teste l'échec de /clusters_for_articles avec une requête mal formée."""
    headers = {'x-api-key': TEST_API_KEY, 'Content-Type': 'application/json'}
    payload = {'mauvais_param': []}
    response = test_client.post('/clusters_for_articles', data=json.dumps(payload), headers=headers)
    assert response.status_code == 400