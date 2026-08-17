from app.schemas import EvaluationQuestionResponse

EVALUATION_QUESTIONS = (
    EvaluationQuestionResponse(
        id=1,
        text="Entrega de Resultados",
        weight=25,
        display_order=1,
    ),
    EvaluationQuestionResponse(
        id=2,
        text="Execução e Qualidade do Trabalho",
        weight=20,
        display_order=2,
    ),
    EvaluationQuestionResponse(
        id=3,
        text="Capacidade de Aprendizado e Desenvolvimento",
        weight=20,
        display_order=3,
    ),
    EvaluationQuestionResponse(
        id=4,
        text="Resolução de Problemas e Pensamento Crítico",
        weight=15,
        display_order=4,
    ),
    EvaluationQuestionResponse(
        id=5,
        text="Colaboração, Influência e Liderança",
        weight=10,
        display_order=5,
    ),
    EvaluationQuestionResponse(
        id=6,
        text="Visão Estratégica e Potencial de Crescimento",
        weight=10,
        display_order=6,
    ),
)
