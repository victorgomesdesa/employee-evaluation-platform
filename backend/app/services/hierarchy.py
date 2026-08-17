from app.repositories import HierarchyRepository
from app.schemas import Relationship, SubordinateResponse


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
