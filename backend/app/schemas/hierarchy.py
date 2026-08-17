from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Relationship(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"


class LeaderResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    position_name: str = Field(alias="positionName")


class SubordinateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    email: str
    position_name: str = Field(alias="positionName")
    relationship: Relationship
    depth: int
