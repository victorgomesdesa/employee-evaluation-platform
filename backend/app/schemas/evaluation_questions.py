from pydantic import BaseModel, ConfigDict, Field


class EvaluationQuestionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    text: str
    weight: int
    display_order: int = Field(alias="displayOrder")
