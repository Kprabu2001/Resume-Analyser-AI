import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.models import Base
from app.database.session import get_db

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/resume_analyser_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_signup(client):
    r = client.post("/auth/signup", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "test@example.com"


def test_signup_duplicate(client):
    client.post("/auth/signup", json={
        "full_name": "Dup User",
        "email": "dup@example.com",
        "password": "testpass123",
    })
    r = client.post("/auth/signup", json={
        "full_name": "Dup User",
        "email": "dup@example.com",
        "password": "testpass123",
    })
    assert r.status_code == 400


def test_login(client):
    client.post("/auth/signup", json={
        "full_name": "Login User",
        "email": "login@example.com",
        "password": "testpass123",
    })
    r = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "testpass123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post("/auth/signup", json={
        "full_name": "Bad Login",
        "email": "badlogin@example.com",
        "password": "correctpass",
    })
    r = client.post("/auth/login", json={
        "email": "badlogin@example.com",
        "password": "wrongpass",
    })
    assert r.status_code == 401
