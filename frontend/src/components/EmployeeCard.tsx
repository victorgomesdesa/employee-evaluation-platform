import type { Subordinate } from "../types/hierarchy";

interface EmployeeCardProps {
  employee: Subordinate;
  onEvaluate: (employee: Subordinate) => void;
  onViewEvaluation: (employee: Subordinate) => void;
}

export function EmployeeCard({
  employee,
  onEvaluate,
  onViewEvaluation,
}: EmployeeCardProps) {
  const relationshipLabel =
    employee.relationship === "direct"
      ? "Direto"
      : `Indireto · nível ${employee.depth}`;

  return (
    <article className="employee-card">
      <div className="employee-avatar" aria-hidden="true">
        {employee.name.charAt(0).toLocaleUpperCase("pt-BR")}
      </div>
      <div className="employee-details">
        <h3>{employee.name}</h3>
        <p className="employee-position">{employee.positionName}</p>
        <a href={`mailto:${employee.email}`}>{employee.email}</a>
      </div>
      <div className="employee-actions">
        <span className={`relationship-badge ${employee.relationship}`}>
          {relationshipLabel}
        </span>
        <div className="employee-action-buttons">
          <button
            className="card-action-button"
            type="button"
            onClick={() => onViewEvaluation(employee)}
            aria-label={`Ver avaliação de ${employee.name}`}
          >
            Ver avaliação
          </button>
          <button
            className="card-action-button"
            type="button"
            onClick={() => onEvaluate(employee)}
            aria-label={`Avaliar ${employee.name}`}
          >
            Avaliar
          </button>
        </div>
      </div>
    </article>
  );
}
