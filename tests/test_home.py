def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
