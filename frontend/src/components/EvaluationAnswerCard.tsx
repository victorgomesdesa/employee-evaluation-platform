import type { PrimaryEvaluationAnswer } from "../types/evaluation";

interface EvaluationAnswerCardProps {
  answer: PrimaryEvaluationAnswer;
  order: number;
}

export function EvaluationAnswerCard({
  answer,
  order,
}: EvaluationAnswerCardProps) {
  return (
    <article className="evaluation-answer-card">
      <span className="answer-order" aria-hidden="true">{order}</span>
      <div>
        <h3>{answer.questionText}</h3>
        <div className="answer-metadata">
          <span>Nota: <strong>{answer.score} de 4</strong></span>
          <span>Peso: <strong>{answer.weight}%</strong></span>
        </div>
      </div>
    </article>
  );
}
