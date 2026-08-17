import type { EvaluationQuestion, Score } from "../types/evaluation";

const SCORE_LABELS: Record<Score, string> = {
  1: "Abaixo do esperado",
  2: "Parcialmente esperado",
  3: "Dentro do esperado",
  4: "Acima do esperado",
};

interface QuestionScoreProps {
  question: EvaluationQuestion;
  value?: Score;
  disabled: boolean;
  onChange: (score: Score) => void;
}

export function QuestionScore({
  question,
  value,
  disabled,
  onChange,
}: QuestionScoreProps) {
  const scores: Score[] = [1, 2, 3, 4];

  return (
    <fieldset className="question-card" disabled={disabled}>
      <legend>
        <span className="question-order">{question.displayOrder}</span>
        <span>{question.text}</span>
      </legend>
      <p className="question-weight">Peso: {question.weight}%</p>
      <div className="score-options">
        {scores.map((score) => (
          <label
            className={`score-option ${value === score ? "selected" : ""}`}
            key={score}
          >
            <input
              type="radio"
              name={`question-${question.id}`}
              value={score}
              checked={value === score}
              onChange={() => onChange(score)}
            />
            <span className="score-number">{score}</span>
            <span className="score-label">{SCORE_LABELS[score]}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
