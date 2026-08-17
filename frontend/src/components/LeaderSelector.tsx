import { useState, type FormEvent } from "react";

import type { Leader } from "../types/hierarchy";

interface LeaderSelectorProps {
  leaders: Leader[];
  onSelect: (leader: Leader) => void;
}

export function LeaderSelector({ leaders, onSelect }: LeaderSelectorProps) {
  const [selectedId, setSelectedId] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const leader = leaders.find((item) => item.id === Number(selectedId));

    if (leader) {
      onSelect(leader);
    }
  }

  return (
    <section className="selector-card" aria-labelledby="selector-title">
      <div className="brand-mark" aria-hidden="true">EF</div>
      <span className="eyebrow">Plataforma de avaliações</span>
      <h1 id="selector-title">Selecione um líder</h1>
      <p className="selector-description">
        Escolha quem você deseja representar para visualizar a equipe.
      </p>

      {leaders.length === 0 ? (
        <p className="empty-message">Nenhum líder disponível.</p>
      ) : (
        <form className="selector-form" onSubmit={handleSubmit}>
          <label htmlFor="leader">Líder</label>
          <select
            id="leader"
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
          >
            <option value="">Selecione um líder</option>
            {leaders.map((leader) => (
              <option key={leader.id} value={leader.id}>
                {leader.name} — {leader.positionName}
              </option>
            ))}
          </select>
          <button className="primary-button" type="submit" disabled={!selectedId}>
            Visualizar equipe
          </button>
        </form>
      )}
    </section>
  );
}
