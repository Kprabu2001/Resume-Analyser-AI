import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.models import Base
from app.dependencies.db_dependency import get_app_session
from app.base.app_session import AppSession

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/resume_analyser_test"

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_app_session():
    raw_session = TestSessionLocal()
    app_session = AppSession(raw_session)
    try:
        yield app_session
    finally:
        app_session.close()


app.dependency_overrides[get_app_session] = override_get_app_session


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


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
    body = r.json()
    assert "access_token" in body.get("data", {})
    assert "refresh_token" in body.get("data", {})


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
