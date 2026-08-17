import { LeaderSelector } from "./components/LeaderSelector";
import { useActingLeader } from "./hooks/useActingLeader";
import { TeamPage } from "./pages/TeamPage";

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

  if (isLoading) {
    return (
      <main className="app-shell">
        <section className="status-card" aria-live="polite">
          <span className="loading-indicator" aria-hidden="true" />
          <p>Carregando líderes...</p>
        </section>
      </main>
    );
  }

  if (error) {
    return (
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
  }

  if (!selectedLeader) {
    return (
      <main className="app-shell">
        <LeaderSelector leaders={leaders} onSelect={selectLeader} />
      </main>
    );
  }

  return <TeamPage leader={selectedLeader} onChangeLeader={clearLeader} />;
}
