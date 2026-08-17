from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class EvaluationAnswerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, strict=True)

    question_id: int = Field(gt=0, alias="questionId")
    score: int = Field(ge=1, le=4)


class EvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, strict=True)

    employee_id: int = Field(gt=0, alias="employeeId")
    answers: list[EvaluationAnswerCreate] = Field(min_length=6, max_length=6)


class EvaluationAnswerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: int = Field(alias="questionId")
    score: int
    weight: int


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    employee_id: int = Field(alias="employeeId")
    evaluator_id: int = Field(alias="evaluatorId")
    week_reference: date = Field(alias="weekReference")
    created_at: datetime = Field(alias="createdAt")
    total_score: Decimal = Field(alias="totalScore")
    answers: list[EvaluationAnswerResponse]


class PrimaryEvaluatorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    position_name: str = Field(alias="positionName")


class PrimaryEvaluationAnswerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: int = Field(alias="questionId")
    question_text: str = Field(alias="questionText")
    score: int
    weight: int


class PrimaryEvaluationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    employee_id: int = Field(alias="employeeId")
    evaluator: PrimaryEvaluatorResponse
    week_reference: date = Field(alias="weekReference")
    created_at: datetime = Field(alias="createdAt")
    total_score: Decimal = Field(alias="totalScore")
    answers: list[PrimaryEvaluationAnswerResponse]
