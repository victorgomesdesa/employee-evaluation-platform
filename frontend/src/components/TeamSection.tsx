import { EmployeeCard } from "./EmployeeCard";
import type { Subordinate } from "../types/hierarchy";

interface TeamSectionProps {
  id: string;
  title: string;
  employees: Subordinate[];
  emptyMessage: string;
  onEvaluate: (employee: Subordinate) => void;
}

export function TeamSection({
  id,
  title,
  employees,
  emptyMessage,
  onEvaluate,
}: TeamSectionProps) {
  const countLabel = `${employees.length} ${
    employees.length === 1 ? "funcionário" : "funcionários"
  }`;

  return (
    <section className="team-section" aria-labelledby={id}>
      <div className="section-heading">
        <h2 id={id}>{title}</h2>
        <span className="employee-count" aria-label={countLabel}>
          {employees.length}
        </span>
      </div>

      {employees.length === 0 ? (
        <p className="section-empty">{emptyMessage}</p>
      ) : (
        <div className="employee-grid">
          {employees.map((employee) => (
            <EmployeeCard
              key={employee.id}
              employee={employee}
              onEvaluate={onEvaluate}
            />
          ))}
        </div>
      )}
    </section>
  );
}
