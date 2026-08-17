import { useEffect, useMemo, useState, type FormEvent } from "react";

import { QuestionScore } from "../components/QuestionScore";
import {
  ApiError,
  createEvaluation,
  getEvaluationQuestions,
} from "../services/api";
import type {
  EvaluationQuestion,
  EvaluationResponse,
  Score,
} from "../types/evaluation";
import type { Leader, Subordinate } from "../types/hierarchy";

interface EvaluationPageProps {
  leader: Leader;
  employee: Subordinate;
  onBack: () => void;
}

function getSubmitErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return "Não foi possível enviar a avaliação. Tente novamente.";
  }

  switch (error.status) {
    case 403:
      return "Você não pode avaliar este funcionário.";
    case 404:
      return "Funcionário não encontrado.";
    case 409:
      return "Este funcionário já foi avaliado por você nesta semana.";
    case 422:
      return "Não foi possível enviar a avaliação. Verifique as respostas.";
    default:
      return "Não foi possível enviar a avaliação. Tente novamente.";
  }
}

export function EvaluationPage({
  leader,
  employee,
  onBack,
}: EvaluationPageProps) {
  const [questions, setQuestions] = useState<EvaluationQuestion[]>([]);
  const [scores, setScores] = useState<Record<number, Score>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<EvaluationResponse | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadQuestions() {
      setIsLoading(true);
      setLoadError(false);

      try {
        const availableQuestions = await getEvaluationQuestions(controller.signal);
        setQuestions(availableQuestions);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        console.error("Failed to load evaluation questions", error);
        setLoadError(true);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadQuestions();
    return () => controller.abort();
  }, [requestVersion]);

  const orderedQuestions = useMemo(
    () =>
      [...questions].sort(
        (first, second) => first.displayOrder - second.displayOrder,
      ),
    [questions],
  );

  function updateScore(questionId: number, score: Score) {
    setScores((currentScores) => ({
      ...currentScores,
      [questionId]: score,
    }));
    setValidationError(null);
    setSubmitError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const hasMissingAnswers =
      orderedQuestions.length === 0 ||
      orderedQuestions.some((question) => scores[question.id] === undefined);

    if (hasMissingAnswers) {
      setValidationError(
        "Responda todas as perguntas antes de enviar a avaliação.",
      );
      return;
    }

    setValidationError(null);
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const response = await createEvaluation(leader.id, {
        employeeId: employee.id,
        answers: orderedQuestions.map((question) => ({
          questionId: question.id,
          score: scores[question.id],
        })),
      });
      setResult(response);
    } catch (error) {
      const isExpectedApiError =
        error instanceof ApiError && [403, 404, 409, 422].includes(error.status);

      if (!isExpectedApiError) {
        console.error("Failed to submit evaluation", error);
      }
      setSubmitError(getSubmitErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (result) {
    return (
      <main className="evaluation-page">
        <section className="success-card" aria-labelledby="success-title">
          <span className="success-icon" aria-hidden="true">✓</span>
          <span className="eyebrow">Avaliação concluída</span>
          <h1 id="success-title">Avaliação enviada com sucesso.</h1>
          <p>
            A avaliação de <strong>{employee.name}</strong> foi registrada com nota
            total <strong>{result.totalScore.replace(".", ",")}</strong>.
          </p>
          <button className="primary-button" type="button" onClick={onBack}>
            Voltar para minha equipe
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="evaluation-page">
      <header className="evaluation-header">
        <button className="back-button" type="button" onClick={onBack}>
          <span aria-hidden="true">←</span> Voltar para minha equipe
        </button>
        <span className="eyebrow">Avaliação de desempenho</span>
        <h1>Avaliar funcionário</h1>
        <div className="evaluation-context">
          <p>Você está avaliando como: <strong>{leader.name} — {leader.positionName}</strong></p>
          <p>Avaliando: <strong>{employee.name} — {employee.positionName}</strong></p>
        </div>
      </header>

      {isLoading ? (
        <section className="status-card compact" aria-live="polite">
          <span className="loading-indicator" aria-hidden="true" />
          <p>Carregando perguntas...</p>
        </section>
      ) : loadError ? (
        <section className="status-card compact" role="alert">
          <span className="status-icon" aria-hidden="true">!</span>
          <h2>Não foi possível carregar as perguntas.</h2>
          <button
            className="primary-button"
            type="button"
            onClick={() => setRequestVersion((version) => version + 1)}
          >
            Tentar novamente
          </button>
        </section>
      ) : (
        <form className="evaluation-form" onSubmit={handleSubmit} noValidate>
          <div className="questions-list">
            {orderedQuestions.map((question) => (
              <QuestionScore
                key={question.id}
                question={question}
                value={scores[question.id]}
                disabled={isSubmitting}
                onChange={(score) => updateScore(question.id, score)}
              />
            ))}
          </div>

          <section className="submission-panel">
            <div className="immutability-warning">
              <span aria-hidden="true">!</span>
              <p>Após o envio, esta avaliação não poderá ser alterada.</p>
            </div>

            {validationError && (
              <p className="form-message error" role="alert">{validationError}</p>
            )}
            {submitError && (
              <p className="form-message error" role="alert">{submitError}</p>
            )}

            <div className="form-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={onBack}
                disabled={isSubmitting}
              >
                Cancelar
              </button>
              <button
                className="primary-button"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Enviando..." : "Enviar avaliação"}
              </button>
            </div>
          </section>
        </form>
      )}
    </main>
  );
}
