from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationQuestionSeed:
    id: int
    text: str
    weight: int
    display_order: int


EVALUATION_QUESTIONS = (
    EvaluationQuestionSeed(
        id=1,
        text="Entrega de Resultados",
        weight=25,
        display_order=1,
    ),
    EvaluationQuestionSeed(
        id=2,
        text="Execução e Qualidade do Trabalho",
        weight=20,
        display_order=2,
    ),
    EvaluationQuestionSeed(
        id=3,
        text="Capacidade de Aprendizado e Desenvolvimento",
        weight=20,
        display_order=3,
    ),
    EvaluationQuestionSeed(
        id=4,
        text="Resolução de Problemas e Pensamento Crítico",
        weight=15,
        display_order=4,
    ),
    EvaluationQuestionSeed(
        id=5,
        text="Colaboração, Influência e Liderança",
        weight=10,
        display_order=5,
    ),
    EvaluationQuestionSeed(
        id=6,
        text="Visão Estratégica e Potencial de Crescimento",
        weight=10,
        display_order=6,
    ),
)
