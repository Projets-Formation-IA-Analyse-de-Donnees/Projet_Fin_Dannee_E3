import pytest
from unittest.mock import MagicMock, patch
from app.run_clustering import main
import numpy as np

def test_main_clustering_logic_success(mocker):
    """Teste la logique principale de clustering sans dépendance réelle à Qdrant."""
    
    mock_point_1 = MagicMock()
    mock_point_1.id = 'id1'
    mock_point_1.vector = np.random.rand(50) 
    mock_point_1.payload = {'code_parent': 'CODE_TEST', 'original_id': 'art1', 'title': 'Titre 1'}
    
    mock_point_2 = MagicMock()
    mock_point_2.id = 'id2'
    mock_point_2.vector = np.random.rand(50)
    mock_point_2.payload = {'code_parent': 'CODE_TEST', 'original_id': 'art2', 'title': 'Titre 2'}

    mocker.patch(
        'app.run_clustering.client.scroll',
        return_value=([mock_point_1, mock_point_2], None)
    )
    
    mocker.patch(
        'app.run_clustering.umap.UMAP.fit_transform',
        return_value=np.array([[1.0, 2.0], [3.0, 4.0]])
    )
    mocker.patch(
        'app.run_clustering.hdbscan.HDBSCAN.fit_predict',
        return_value=np.array([0, 1]) 
    )

    mock_upsert = mocker.patch('app.run_clustering.client.upsert')

    main(
        code_id="CODE_TEST",
        umap_params={'n_neighbors': 15, 'n_components': 2},
        hdbscan_params={'min_cluster_size': 2, 'min_samples': 2}
    )

    assert mock_upsert.called
    upsert_call = mock_upsert.call_args[1]
    points_to_update = upsert_call['points']

    assert points_to_update[0].id == 'id1'
    assert points_to_update[0].payload['cluster_id'] == 0
    
    assert points_to_update[1].id == 'id2'
    assert points_to_update[1].payload['cluster_id'] == 1