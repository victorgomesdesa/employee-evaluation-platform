from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Evaluation, EvaluationAnswer, EvaluationQuestion
from app.repositories import EvaluationQuestionRepository

EXPECTED_QUESTION_TEXTS = [
    "Entrega de Resultados",
    "Execução e Qualidade do Trabalho",
    "Capacidade de Aprendizado e Desenvolvimento",
    "Resolução de Problemas e Pensamento Crítico",
    "Colaboração, Influência e Liderança",
    "Visão Estratégica e Potencial de Crescimento",
]


def create_evaluation(
    session: Session,
    *,
    evaluator_id: int = 2,
    employee_id: int = 4,
    week_reference: date = date(2026, 8, 10),
    total_score: Decimal = Decimal("3.10"),
) -> Evaluation:
    evaluation = Evaluation(
        evaluator_id=evaluator_id,
        employee_id=employee_id,
        week_reference=week_reference,
        total_score=total_score,
    )
    session.add(evaluation)
    session.flush()
    return evaluation


@pytest.mark.integration
def test_question_repository_returns_exact_seed_fixture(
    database_session: Session,
) -> None:
    questions = EvaluationQuestionRepository(database_session).get_all()

    assert len(questions) == 6
    assert [question.id for question in questions] == [1, 2, 3, 4, 5, 6]
    assert [question.text for question in questions] == EXPECTED_QUESTION_TEXTS
    assert [question.weight for question in questions] == [25, 20, 20, 15, 10, 10]
    assert [question.display_order for question in questions] == [1, 2, 3, 4, 5, 6]
    assert sum(question.weight for question in questions) == 100


@pytest.mark.integration
def test_evaluation_references_distinct_employee_roles(
    database_session: Session,
) -> None:
    evaluation = create_evaluation(database_session)

    assert evaluation.evaluator.name == "Bob Sinclair"
    assert evaluation.employee.name == "David Okafor"
    assert evaluation.evaluator_id != evaluation.employee_id
    assert evaluation.created_at is not None

    database_session.rollback()


@pytest.mark.integration
def test_total_score_preserves_exact_decimal_value(database_session: Session) -> None:
    evaluation = create_evaluation(database_session, total_score=Decimal("3.10"))
    stored_score = database_session.scalar(
        select(Evaluation.total_score).where(Evaluation.id == evaluation.id)
    )

    assert stored_score == Decimal("3.10")

    database_session.rollback()


@pytest.mark.integration
def test_weekly_evaluation_uniqueness_is_enforced(database_session: Session) -> None:
    evaluation_data = {
        "evaluator_id": 2,
        "employee_id": 4,
        "week_reference": date(2026, 8, 10),
        "total_score": Decimal("3.10"),
    }
    database_session.add_all(
        [Evaluation(**evaluation_data), Evaluation(**evaluation_data)]
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


@pytest.mark.integration
def test_evaluation_answer_accepts_scores_from_one_to_four(
    database_session: Session,
) -> None:
    evaluation = create_evaluation(database_session)
    answers = [
        EvaluationAnswer(
            evaluation_id=evaluation.id,
            question_id=score,
            score=score,
            weight=10,
        )
        for score in range(1, 5)
    ]
    database_session.add_all(answers)
    database_session.flush()

    assert [answer.score for answer in answers] == [1, 2, 3, 4]

    database_session.rollback()


@pytest.mark.integration
@pytest.mark.parametrize("score", [0, 5])
def test_evaluation_answer_rejects_out_of_range_score(
    database_session: Session,
    score: int,
) -> None:
    evaluation = create_evaluation(database_session)
    database_session.add(
        EvaluationAnswer(
            evaluation_id=evaluation.id,
            question_id=1,
            score=score,
            weight=25,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


@pytest.mark.integration
def test_evaluation_answer_weight_is_independent_snapshot(
    database_session: Session,
) -> None:
    evaluation = create_evaluation(database_session)
    answer = EvaluationAnswer(
        evaluation_id=evaluation.id,
        question_id=1,
        score=4,
        weight=99,
    )
    database_session.add(answer)
    database_session.flush()

    question_weight = database_session.scalar(
        select(EvaluationQuestion.weight).where(EvaluationQuestion.id == 1)
    )
    stored_weight = database_session.scalar(
        select(EvaluationAnswer.weight).where(EvaluationAnswer.id == answer.id)
    )

    assert question_weight == 25
    assert stored_weight == 99

    database_session.rollback()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("evaluator_id", "employee_id"),
    [(999999, 4), (2, 999999)],
    ids=["evaluator", "employee"],
)
def test_evaluation_employee_foreign_keys_are_enforced(
    database_session: Session,
    evaluator_id: int,
    employee_id: int,
) -> None:
    database_session.add(
        Evaluation(
            evaluator_id=evaluator_id,
            employee_id=employee_id,
            week_reference=date(2026, 8, 10),
            total_score=Decimal("3.10"),
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


@pytest.mark.integration
def test_evaluation_answer_evaluation_foreign_key_is_enforced(
    database_session: Session,
) -> None:
    database_session.add(
        EvaluationAnswer(
            evaluation_id=999999,
            question_id=1,
            score=4,
            weight=25,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()


@pytest.mark.integration
def test_evaluation_answer_question_foreign_key_is_enforced(
    database_session: Session,
) -> None:
    evaluation = create_evaluation(database_session)
    database_session.add(
        EvaluationAnswer(
            evaluation_id=evaluation.id,
            question_id=999999,
            score=4,
            weight=25,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()

    database_session.rollback()
