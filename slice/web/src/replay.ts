import { useEffect, useState } from "react";
import type { Replay } from "./types";

function locationIndex(key: string) {
  const value = Number(new URLSearchParams(location.hash.slice(1)).get(key));
  return Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0;
}
export function useReplayInvestigation() {
  const [replay, setReplay] = useState<Replay | null>(null);
  const [scenario, scenarioState] = useState(0);
  const [turnIndex, turnState] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch("./recording.json", { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("Recorded asset unavailable");
      const value = await response.json() as Replay;
      if (!Array.isArray(value.investigations) || !value.investigations.length ||
          value.investigations.some(inv => !Array.isArray(inv.turns) || !inv.turns.length))
        throw new Error("Invalid recording");
      const index = Math.min(locationIndex("scenario"), value.investigations.length - 1);
      scenarioState(index);
      turnState(Math.min(locationIndex("turn"), value.investigations[index].turns.length - 1));
      setReplay(value);
    }).catch(e => { if (e.name !== "AbortError") setError(e.message); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (replay) window.history.replaceState(null, "", `#scenario=${scenario}&turn=${turnIndex}`);
  }, [replay, scenario, turnIndex]);
  function setScenario(index: number) {
    if (!replay) return;
    scenarioState(Math.max(0, Math.min(index, replay.investigations.length - 1)));
    turnState(0);
  }
  function setTurnIndex(index: number) {
    if (replay) turnState(Math.max(0, Math.min(index, replay.investigations[scenario].turns.length - 1)));
  }
  return { mode: "replay" as const, current: replay?.investigations[scenario] || null,
    ready: replay !== null, error, setError, replay, scenario, turnIndex, setScenario, setTurnIndex };
}
