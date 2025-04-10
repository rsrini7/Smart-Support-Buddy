def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_upload_without_data(client):
    response = client.post("/api/upload-msg")
    assert response.status_code == 422


def test_search_empty(client):
    response = client.post("/api/search", json={"query_text": "", "limit": 5})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
