import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    # Check if the redirection to /login works when unauthorized,
    # or you might get 200 OK if the user logic permits.
    # From main.py, "/" redirects to "/login" if no user in session.
    # TestClient follows redirects by default, so we should land on /login and get a 200 HTML response.
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Login" in response.content or b"login" in response.content

def test_login_page():
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
