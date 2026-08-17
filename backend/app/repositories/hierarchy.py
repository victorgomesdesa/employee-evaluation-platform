from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class SubordinateRecord:
    id: int
    name: str
    email: str
    position_name: str
    depth: int


class HierarchyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_subordinates(self, leader_id: int) -> list[SubordinateRecord]:
        query = text(
            """
            WITH RECURSIVE subtree AS (
                SELECT
                    leader_lead.lead_id AS employee_id,
                    1 AS depth
                FROM leader_lead
                WHERE leader_lead.leader_id = :leader_id

                UNION ALL

                SELECT
                    leader_lead.lead_id AS employee_id,
                    subtree.depth + 1 AS depth
                FROM leader_lead
                JOIN subtree
                    ON leader_lead.leader_id = subtree.employee_id
            )
            SELECT
                employee.id,
                employee.name,
                employee.email,
                employee.position_name,
                subtree.depth
            FROM subtree
            JOIN employee ON employee.id = subtree.employee_id
            WHERE employee.id <> :leader_id
            ORDER BY subtree.depth, employee.name, employee.id
            """
        )
        rows = self._session.execute(query, {"leader_id": leader_id}).mappings()

        return [
            SubordinateRecord(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                position_name=row["position_name"],
                depth=row["depth"],
            )
            for row in rows
        ]
