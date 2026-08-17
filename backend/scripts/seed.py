from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import Employee, LeaderLead

EMPLOYEES = (
    (1, "Alice Hartman", "alice.hartman@company.com", "CEO"),
    (2, "Bob Sinclair", "bob.sinclair@company.com", "CTO"),
    (3, "Carol Nguyen", "carol.nguyen@company.com", "CFO"),
    (4, "David Okafor", "david.okafor@company.com", "Engineering Manager"),
    (5, "Eva Müller", "eva.muller@company.com", "Engineering Manager"),
    (6, "Frank Rossi", "frank.rossi@company.com", "Product Manager"),
    (7, "Grace Kim", "grace.kim@company.com", "UX Designer"),
    (8, "Henry Patel", "henry.patel@company.com", "Senior Software Engineer"),
    (9, "Isabelle Dubois", "isabelle.dubois@company.com", "Senior Software Engineer"),
    (10, "James Watanabe", "james.watanabe@company.com", "Software Engineer"),
    (11, "Karen Oliveira", "karen.oliveira@company.com", "Software Engineer"),
    (12, "Liam Johansson", "liam.johansson@company.com", "Software Engineer"),
    (13, "Mia Fernandez", "mia.fernandez@company.com", "Data Engineer"),
    (14, "Noah Chukwu", "noah.chukwu@company.com", "Data Analyst"),
    (15, "Olivia Brooks", "olivia.brooks@company.com", "QA Engineer"),
    (16, "Paul Nakamura", "paul.nakamura@company.com", "QA Engineer"),
    (17, "Quinn Santos", "quinn.santos@company.com", "DevOps Engineer"),
    (18, "Rachel Ivanova", "rachel.ivanova@company.com", "Finance Analyst"),
    (19, "Samuel Osei", "samuel.osei@company.com", "Finance Analyst"),
    (20, "Tina Bergmann", "tina.bergmann@company.com", "HR Specialist"),
)

LEADER_LEADS = (
    (1, 2),
    (1, 3),
    (1, 6),
    (1, 20),
    (2, 4),
    (2, 5),
    (2, 7),
    (2, 17),
    (2, 16),
    (4, 8),
    (4, 12),
    (8, 10),
    (8, 11),
    (5, 9),
    (5, 13),
    (5, 14),
    (3, 18),
    (3, 19),
    (6, 15),
)


def seed_database(session: Session) -> bool:
    existing_employees = session.scalars(select(Employee).order_by(Employee.id)).all()
    existing_links = session.scalars(
        select(LeaderLead).order_by(LeaderLead.leader_id, LeaderLead.lead_id)
    ).all()

    employee_fixture = set(EMPLOYEES)
    link_fixture = set(LEADER_LEADS)
    employee_rows = {
        (employee.id, employee.name, employee.email, employee.position_name)
        for employee in existing_employees
    }
    link_rows = {(link.leader_id, link.lead_id) for link in existing_links}

    if employee_rows == employee_fixture and link_rows == link_fixture:
        return False

    if employee_rows or link_rows:
        raise RuntimeError(
            "O banco já contém dados de funcionários ou hierarquia diferentes da fixture."
        )

    session.add_all(
        Employee(id=id_, name=name, email=email, position_name=position_name)
        for id_, name, email, position_name in EMPLOYEES
    )
    session.flush()
    session.add_all(
        LeaderLead(leader_id=leader_id, lead_id=lead_id)
        for leader_id, lead_id in LEADER_LEADS
    )
    session.flush()
    session.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('employee', 'id'), "
            "(SELECT MAX(id) FROM employee), true)"
        )
    )
    return True


def main() -> None:
    with SessionLocal() as session, session.begin():
        inserted = seed_database(session)

    if inserted:
        print("Fixture de funcionários e hierarquia carregada com sucesso.")
    else:
        print("A fixture de funcionários e hierarquia já está carregada.")


if __name__ == "__main__":
    main()
