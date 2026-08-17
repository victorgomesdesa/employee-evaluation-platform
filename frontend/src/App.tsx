import { useState, type ReactNode } from "react";

import { LeaderSelector } from "./components/LeaderSelector";
import { ThemeToggle } from "./components/ThemeToggle";
import { useActingLeader } from "./hooks/useActingLeader";
import { useTheme } from "./hooks/useTheme";
import { EvaluationPage } from "./pages/EvaluationPage";
import { EmployeeEvaluationPage } from "./pages/EmployeeEvaluationPage";
import { TeamPage } from "./pages/TeamPage";
import type { Subordinate } from "./types/hierarchy";

export function App() {
  const {
    leaders,
    selectedLeader,
    isLoading,
    error,
    selectLeader,
    clearLeader,
    reloadLeaders,
  } = useActingLeader();
  const { theme, toggleTheme } = useTheme();
  const [employeeToEvaluate, setEmployeeToEvaluate] =
    useState<Subordinate | null>(null);
  const [employeeToView, setEmployeeToView] = useState<Subordinate | null>(null);

  let content: ReactNode;

  if (isLoading) {
    content = (
      <main className="app-shell">
        <section className="status-card" aria-live="polite">
          <span className="loading-indicator" aria-hidden="true" />
          <p>Carregando líderes...</p>
        </section>
      </main>
    );
  } else if (error) {
    content = (
      <main className="app-shell">
        <section className="status-card" role="alert">
          <span className="status-icon" aria-hidden="true">!</span>
          <h1>Não foi possível carregar os líderes.</h1>
          <p>Verifique sua conexão e tente novamente.</p>
          <button className="primary-button" type="button" onClick={reloadLeaders}>
            Tentar novamente
          </button>
        </section>
      </main>
    );
  } else if (!selectedLeader) {
    content = (
      <main className="app-shell">
        <LeaderSelector leaders={leaders} onSelect={selectLeader} />
      </main>
    );
  } else if (employeeToEvaluate) {
    content = (
      <EvaluationPage
        leader={selectedLeader}
        employee={employeeToEvaluate}
        onBack={() => setEmployeeToEvaluate(null)}
      />
    );
  } else if (employeeToView) {
    content = (
      <EmployeeEvaluationPage
        leader={selectedLeader}
        employee={employeeToView}
        onBack={() => setEmployeeToView(null)}
        onEvaluate={() => {
          setEmployeeToView(null);
          setEmployeeToEvaluate(employeeToView);
        }}
      />
    );
  } else {
    content = (
      <TeamPage
        leader={selectedLeader}
        onEvaluate={setEmployeeToEvaluate}
        onViewEvaluation={setEmployeeToView}
        onChangeLeader={() => {
          setEmployeeToEvaluate(null);
          setEmployeeToView(null);
          clearLeader();
        }}
      />
    );
  }

  return (
    <>
      <ThemeToggle theme={theme} onToggle={toggleTheme} />
      {content}
    </>
  );
}
