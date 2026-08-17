from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database.session import get_session
from app.main import app
from scripts.seed import seed_database


@pytest.fixture(scope="session")
def database_session() -> Generator[Session, None, None]:
    database_url = settings.test_database_url
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL não foi configurada.")

    database_name = make_url(database_url).database or ""
    if not database_name.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL deve apontar para um banco com sufixo _test.")

    alembic_config = Config("alembic.ini")
    alembic_config.attributes["database_url"] = database_url
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    try:
        with testing_session() as session:
            with session.begin():
                assert seed_database(session) is True
            with session.begin():
                assert seed_database(session) is False
            yield session
    finally:
        engine.dispose()
        command.downgrade(alembic_config, "base")


@pytest.fixture
def api_client(database_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_session] = lambda: database_session

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
