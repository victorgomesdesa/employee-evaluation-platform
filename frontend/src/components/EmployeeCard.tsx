import type { Subordinate } from "../types/hierarchy";

interface EmployeeCardProps {
  employee: Subordinate;
}

export function EmployeeCard({ employee }: EmployeeCardProps) {
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
      <span className={`relationship-badge ${employee.relationship}`}>
        {relationshipLabel}
      </span>
    </article>
  );
}
