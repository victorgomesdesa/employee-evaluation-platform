import { useCallback, useEffect, useState } from "react";

import { getLeaders } from "../services/api";
import type { Leader } from "../types/hierarchy";

const STORAGE_KEY = "actingLeaderId";

interface ActingLeaderState {
  leaders: Leader[];
  selectedLeader: Leader | null;
  isLoading: boolean;
  error: boolean;
  selectLeader: (leader: Leader) => void;
  clearLeader: () => void;
  reloadLeaders: () => void;
}

export function useActingLeader(): ActingLeaderState {
  const [leaders, setLeaders] = useState<Leader[]>([]);
  const [selectedLeader, setSelectedLeader] = useState<Leader | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadLeaders() {
      setIsLoading(true);
      setError(false);

      try {
        const availableLeaders = await getLeaders(controller.signal);
        const savedId = localStorage.getItem(STORAGE_KEY);
        const parsedId = savedId === null ? Number.NaN : Number(savedId);
        const savedLeader = Number.isInteger(parsedId)
          ? availableLeaders.find((leader) => leader.id === parsedId)
          : undefined;

        setLeaders(availableLeaders);

        if (savedLeader) {
          setSelectedLeader(savedLeader);
        } else {
          localStorage.removeItem(STORAGE_KEY);
          setSelectedLeader(null);
        }
      } catch (loadError) {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }

        console.error("Failed to load leaders", loadError);
        setError(true);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadLeaders();

    return () => controller.abort();
  }, [requestVersion]);

  const selectLeader = useCallback((leader: Leader) => {
    localStorage.setItem(STORAGE_KEY, String(leader.id));
    setSelectedLeader(leader);
  }, []);

  const clearLeader = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setSelectedLeader(null);
  }, []);

  const reloadLeaders = useCallback(() => {
    setRequestVersion((currentVersion) => currentVersion + 1);
  }, []);

  return {
    leaders,
    selectedLeader,
    isLoading,
    error,
    selectLeader,
    clearLeader,
    reloadLeaders,
  };
}
