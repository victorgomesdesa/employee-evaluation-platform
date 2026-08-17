import { useCallback, useEffect, useMemo, useState } from "react";

import { TeamSection } from "../components/TeamSection";
import { getSubordinates } from "../services/api";
import type { Leader, Subordinate } from "../types/hierarchy";

interface TeamPageProps {
  leader: Leader;
  onChangeLeader: () => void;
  onEvaluate: (employee: Subordinate) => void;
  onViewEvaluation: (employee: Subordinate) => void;
}

export function TeamPage({
  leader,
  onChangeLeader,
  onEvaluate,
  onViewEvaluation,
}: TeamPageProps) {
  const [subordinates, setSubordinates] = useState<Subordinate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadTeam() {
      setSubordinates([]);
      setIsLoading(true);
      setError(false);

      try {
        const team = await getSubordinates(leader.id, controller.signal);
        setSubordinates(team);
      } catch (loadError) {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }

        console.error("Failed to load team", loadError);
        setError(true);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadTeam();

    return () => controller.abort();
  }, [leader.id, requestVersion]);

  const reloadTeam = useCallback(() => {
    setRequestVersion((currentVersion) => currentVersion + 1);
  }, []);

  const orderedSubordinates = useMemo(
    () =>
      [...subordinates].sort((first, second) =>
        first.name.localeCompare(second.name, "pt-BR"),
      ),
    [subordinates],
  );
  const directEmployees = orderedSubordinates.filter(
    (employee) => employee.relationship === "direct",
  );
  const indirectEmployees = orderedSubordinates.filter(
    (employee) => employee.relationship === "indirect",
  );

  return (
    <main className="team-page">
      <header className="team-header">
        <div>
          <span className="eyebrow">Plataforma de avaliações</span>
          <h1>Minha equipe</h1>
          <p>
            Visualizando como: <strong>{leader.name} — {leader.positionName}</strong>
          </p>
        </div>
        <button className="secondary-button" type="button" onClick={onChangeLeader}>
          Trocar líder
        </button>
      </header>

      {isLoading ? (
        <section className="status-card compact" aria-live="polite">
          <span className="loading-indicator" aria-hidden="true" />
          <p>Carregando equipe...</p>
        </section>
      ) : error ? (
        <section className="status-card compact" role="alert">
          <span className="status-icon" aria-hidden="true">!</span>
          <h2>Não foi possível carregar a equipe.</h2>
          <button className="primary-button" type="button" onClick={reloadTeam}>
            Tentar novamente
          </button>
        </section>
      ) : subordinates.length === 0 ? (
        <section className="status-card compact">
          <p>Nenhum subordinado encontrado.</p>
        </section>
      ) : (
        <div className="team-content">
          <TeamSection
            id="direct-team-title"
            title="Subordinados diretos"
            employees={directEmployees}
            emptyMessage="Nenhum subordinado direto encontrado."
            onEvaluate={onEvaluate}
            onViewEvaluation={onViewEvaluation}
          />
          <TeamSection
            id="indirect-team-title"
            title="Subordinados indiretos"
            employees={indirectEmployees}
            emptyMessage="Nenhum subordinado indireto encontrado."
            onEvaluate={onEvaluate}
            onViewEvaluation={onViewEvaluation}
          />
        </div>
      )}
    </main>
  );
}
