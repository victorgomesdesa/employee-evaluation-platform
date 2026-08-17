from app.repositories import HierarchyRepository
from app.schemas import LeaderResponse, Relationship, SubordinateResponse


class HierarchyService:
    def __init__(self, repository: HierarchyRepository) -> None:
        self._repository = repository

    def get_subordinates(self, leader_id: int) -> list[SubordinateResponse]:
        records = self._repository.get_subordinates(leader_id)

        return [
            SubordinateResponse(
                id=record.id,
                name=record.name,
                email=record.email,
                position_name=record.position_name,
                relationship=(
                    Relationship.DIRECT
                    if record.depth == 1
                    else Relationship.INDIRECT
                ),
                depth=record.depth,
            )
            for record in records
        ]

    def get_leaders(self) -> list[LeaderResponse]:
        records = self._repository.get_leaders()

        return [
            LeaderResponse(
                id=record.id,
                name=record.name,
                position_name=record.position_name,
            )
            for record in records
        ]

    def is_subordinate(self, leader_id: int, employee_id: int) -> bool:
        return any(
            record.id == employee_id
            for record in self._repository.get_subordinates(leader_id)
        )
