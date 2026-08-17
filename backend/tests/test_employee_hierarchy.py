from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Employee, LeaderLead
from scripts.seed import EMPLOYEES, LEADER_LEADS, seed_database

EXPECTED_LEADERS = {
    "Alice Hartman",
    "Bob Sinclair",
    "Carol Nguyen",
    "David Okafor",
    "Eva Müller",
    "Frank Rossi",
    "Henry Patel",
}


@pytest.fixture(scope="module")
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


@pytest.mark.integration
def test_seed_contains_exactly_twenty_employees(database_session: Session) -> None:
    employee_count = database_session.scalar(select(func.count()).select_from(Employee))

    assert employee_count == 20
    assert employee_count == len(EMPLOYEES)


@pytest.mark.integration
def test_seed_is_idempotent(database_session: Session) -> None:
    assert seed_database(database_session) is False

    database_session.rollback()


@pytest.mark.integration
def test_seed_contains_expected_leader_lead_relationships(
    database_session: Session,
) -> None:
    relationships = set(
        database_session.execute(
            select(LeaderLead.leader_id, LeaderLead.lead_id)
        ).tuples()
    )

    assert relationships == set(LEADER_LEADS)


@pytest.mark.integration
def test_seed_contains_exactly_seven_expected_leaders(
    database_session: Session,
) -> None:
    leaders = set(
        database_session.scalars(
            select(Employee.name)
            .join(LeaderLead, Employee.id == LeaderLead.leader_id)
            .distinct()
        )
    )

    assert len(leaders) == 7
    assert leaders == EXPECTED_LEADERS


@pytest.mark.integration
def test_employee_email_uniqueness_is_enforced(database_session: Session) -> None:
    existing_email = EMPLOYEES[0][2]
    database_session.add(
        Employee(
            name="Duplicate Employee",
            email=existing_email,
            position_name="Test Position",
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


@pytest.mark.integration
def test_employee_cannot_lead_itself(database_session: Session) -> None:
    database_session.add(LeaderLead(leader_id=1, lead_id=1))

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()
