from app.services import vector_service

def test_add_issue_to_vectordb_mock(mocker):
    mock_client = mocker.patch("app.services.vector_service.get_vector_db_client")
    mock_model = mocker.patch("app.services.vector_service.get_embedding_model")
    mock_client.return_value.get_or_create_collection.return_value.add.return_value = None

    import numpy as np
    mock_model.return_value.encode.return_value = np.array([0.1] * 384)

    issue_id = vector_service.add_issue_to_vectordb({"subject": "Test", "body": "Body"}, None)
    assert issue_id.startswith("issue_")
