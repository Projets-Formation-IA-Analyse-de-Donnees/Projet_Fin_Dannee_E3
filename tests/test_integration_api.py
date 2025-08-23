import json
from qdrant_client import models
from unittest.mock import MagicMock 

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

def test_search_endpoint_with_code_filter_success(test_client, mocker):
    """Teste la recherche sur /search avec un filtre code_id."""
    
    mock_point = MagicMock()
    mock_point.payload = {
        'original_id': 'article_filtre_1', 
        'code_parent': 'CODE_TEST_PARENT',
        'highlight': 'Ceci est un extrait de texte.',
        'title': 'Art. Filtre 1'
    }
    mock_point.score = 0.95
    mock_query = mocker.patch(
        'app.routes.search.client.query_points', 
        return_value=MagicMock(points=[mock_point])
    )

    headers = {'x-api-key': 'super-secret-test-key', 'Content-Type': 'application/json'}
    payload = {'query': 'recherche filtre', 'code_id': 'CODE_TEST_PARENT'}
    response = test_client.post('/search', data=json.dumps(payload), headers=headers)
    
    assert response.status_code == 200
    response_data = response.get_json()
    assert len(response_data) == 1
    assert response_data[0]['id'] == 'article_filtre_1'

    call_kwargs = mock_query.call_args[1]
    assert 'query_filter' in call_kwargs
    assert isinstance(call_kwargs['query_filter'], models.Filter)
    assert call_kwargs['query_filter'].must[0].key == "code_parent"
    assert call_kwargs['query_filter'].must[0].match.value == 'CODE_TEST_PARENT'

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

def test_clusters_endpoint_no_chunks_found(test_client, mocker):
    """Teste le cas où Qdrant ne trouve aucun chunk pour les IDs demandés."""
    
    mocker.patch(
        'app.routes.cluster.client.scroll', 
        return_value=([], None)
    )

    headers = {'x-api-key': 'super-secret-test-key', 'Content-Type': 'application/json'}
    payload = {'article_ids': ['id_qui_n_existe_pas']} 
    response = test_client.post('/clusters_for_articles', data=json.dumps(payload), headers=headers)
    
    assert response.status_code == 404
    assert response.is_json
    assert "No chunks found for this code" in response.get_json().get('error')

def test_clusters_endpoint_article_with_no_cluster_id(test_client, mocker):
    """Teste le cas où un chunk n'a pas d'ID de cluster."""
    
    mock_point_no_cluster = MagicMock()
    mock_point_no_cluster.payload = {'original_id': 'article_sans_cluster', 'cluster_id': None}
    
    mocker.patch(
        'app.routes.cluster.client.scroll', 
        return_value=([mock_point_no_cluster], None)
    )

    headers = {'x-api-key': 'super-secret-test-key', 'Content-Type': 'application/json'}
    payload = {'article_ids': ['article_sans_cluster']} 
    response = test_client.post('/clusters_for_articles', data=json.dumps(payload), headers=headers)
    
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data == {'article_sans_cluster': -1}
