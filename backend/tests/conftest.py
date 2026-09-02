import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import engine, get_db
from app.main import app
from app.models import User


@pytest.fixture
def db_session():
    """Session bound to an outer transaction that is always rolled back.

    `join_transaction_mode="create_savepoint"` lets the code under test call
    `commit()` without escaping the rollback (SQLAlchemy 2.0+). Needs the local
    Postgres up (`docker compose up -d && alembic upgrade head`).
    """
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def test_user(db_session) -> User:
    user = User(
        email="pytest@example.com",
        auth_provider="supabase",
        auth_subject="pytest-subject",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def client(db_session, test_user):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
