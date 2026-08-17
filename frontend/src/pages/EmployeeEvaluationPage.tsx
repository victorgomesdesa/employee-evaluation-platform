import { useEffect, useState } from "react";

import { EvaluationAnswerCard } from "../components/EvaluationAnswerCard";
import { ApiError, getLatestEvaluation } from "../services/api";
import type { PrimaryEvaluation } from "../types/evaluation";
import type { Leader, Subordinate } from "../types/hierarchy";

interface EmployeeEvaluationPageProps {
  leader: Leader;
  employee: Subordinate;
  onBack: () => void;
  onEvaluate: () => void;
}

function formatReferenceDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

function formatCreatedAt(value: string): string {
  const date = new Date(value);
  const formattedDate = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
  const formattedTime = new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);

  return `${formattedDate} às ${formattedTime}`;
}

function getLoadErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return "Você não pode visualizar as avaliações deste funcionário.";
    }

    if (error.status === 404) {
      return "Funcionário não encontrado.";
    }
  }

  return "Não foi possível carregar a avaliação.";
}

export function EmployeeEvaluationPage({
  leader,
  employee,
  onBack,
  onEvaluate,
}: EmployeeEvaluationPageProps) {
  const [evaluation, setEvaluation] = useState<PrimaryEvaluation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadEvaluation() {
      setEvaluation(null);
      setErrorMessage(null);
      setIsLoading(true);

      try {
        const latestEvaluation = await getLatestEvaluation(
          leader.id,
          employee.id,
          controller.signal,
        );
        setEvaluation(latestEvaluation);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        if (!(error instanceof ApiError) || ![403, 404].includes(error.status)) {
          console.error("Failed to load primary evaluation", error);
        }
        setErrorMessage(getLoadErrorMessage(error));
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadEvaluation();
    return () => controller.abort();
  }, [employee.id, leader.id, requestVersion]);

  const relationshipLabel =
    employee.relationship === "direct"
      ? "Subordinado direto"
      : `Subordinado indireto · nível ${employee.depth}`;

  return (
    <main className="employee-evaluation-page">
      <header className="employee-detail-header">
        <button className="back-button" type="button" onClick={onBack}>
          <span aria-hidden="true">←</span> Voltar para minha equipe
        </button>
        <span className="eyebrow">Detalhes do funcionário</span>
        <div className="employee-profile">
          <div className="profile-avatar" aria-hidden="true">
            {employee.name.charAt(0).toLocaleUpperCase("pt-BR")}
          </div>
          <div>
            <h1>{employee.name}</h1>
            <p>{employee.positionName}</p>
            <a href={`mailto:${employee.email}`}>{employee.email}</a>
          </div>
        </div>
        <div className="detail-context">
          <span>{relationshipLabel}</span>
          <span>Visualizando como: <strong>{leader.name} — {leader.positionName}</strong></span>
        </div>
      </header>

      {isLoading ? (
        <section className="status-card compact" aria-live="polite">
          <span className="loading-indicator" aria-hidden="true" />
          <p>Carregando avaliação...</p>
        </section>
      ) : errorMessage ? (
        <section className="status-card compact" role="alert">
          <span className="status-icon" aria-hidden="true">!</span>
          <h2>{errorMessage}</h2>
          <div className="detail-error-actions">
            <button className="secondary-button" type="button" onClick={onBack}>
              Voltar para minha equipe
            </button>
            <button
              className="primary-button"
              type="button"
              onClick={() => setRequestVersion((version) => version + 1)}
            >
              Tentar novamente
            </button>
          </div>
        </section>
      ) : evaluation === null ? (
        <section className="empty-evaluation-card">
          <span className="empty-evaluation-icon" aria-hidden="true">—</span>
          <h2>Este funcionário ainda não possui avaliações.</h2>
          <p>Você pode iniciar a primeira avaliação deste funcionário.</p>
          <button className="primary-button" type="button" onClick={onEvaluate}>
            Avaliar funcionário
          </button>
        </section>
      ) : (
        <div className="primary-evaluation-content">
          <section className="evaluation-summary" aria-labelledby="evaluation-summary-title">
            <div className="summary-heading">
              <div>
                <span className="eyebrow">Avaliação principal</span>
                <h2 id="evaluation-summary-title">Avaliação mais recente</h2>
              </div>
              <div className="total-score">
                <span>Nota final</span>
                <strong>{evaluation.totalScore.replace(".", ",")}</strong>
                <small>de 4,00</small>
              </div>
            </div>

            <dl className="evaluation-metadata">
              <div>
                <dt>Avaliado por</dt>
                <dd>{evaluation.evaluator.name} — {evaluation.evaluator.positionName}</dd>
              </div>
              <div>
                <dt>Semana de referência</dt>
                <dd>{formatReferenceDate(evaluation.weekReference)}</dd>
              </div>
              <div>
                <dt>Enviada em</dt>
                <dd>{formatCreatedAt(evaluation.createdAt)}</dd>
              </div>
            </dl>
          </section>

          <section className="evaluation-answers" aria-labelledby="evaluation-answers-title">
            <div className="answers-heading">
              <h2 id="evaluation-answers-title">Respostas da avaliação</h2>
              <span>{evaluation.answers.length} respostas</span>
            </div>
            <div className="answer-list">
              {evaluation.answers.map((answer, index) => (
                <EvaluationAnswerCard
                  key={answer.questionId}
                  answer={answer}
                  order={index + 1}
                />
              ))}
            </div>
          </section>

          <div className="detail-actions">
            <button className="secondary-button" type="button" onClick={onBack}>
              Voltar para minha equipe
            </button>
            <button className="primary-button" type="button" onClick={onEvaluate}>
              Avaliar funcionário
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
