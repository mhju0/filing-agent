import { useEffect, useRef, useState } from "react";
import type { Investigation, Lang, Turn } from "./types";

export const executing = (turn: Turn) => ["queued", "running", "saving"].includes(turn.status);
export const unresolved = (turn: Turn) => executing(turn) || turn.status === "storage_failed";
const failures = ["error", "cancelled", "timeout", "interrupted", "stop_unconfirmed"];
const draftKey = (id: string | null) => "filing-draft-" + (id || "new");
function readDraft(id: string | null) {
  try {
    const value = JSON.parse(localStorage.getItem(draftKey(id)) || "null");
    return value && Date.now() - value.at < 30 * 86400000 ? value.text : "";
  } catch { return ""; }
}

export function useLiveInvestigation() {
  const records = useRef(new Map<string, Investigation>());
  const revisions = useRef(new Map<string, number>());
  const selected = useRef<string | null>(null);
  const epoch = useRef(0);
  const token = useRef("");
  const mounted = useRef(true);
  const sendingRef = useRef(false);
  const [, render] = useState(0);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [draft, draftState] = useState(() => readDraft(localStorage.getItem("filing-investigation")));
  const [sending, setSending] = useState(false);
  const [running, setRunning] = useState(false);
  const [history, setHistory] = useState<Investigation[] | null>(null);
  const repaint = () => { if (mounted.current) render(n => n + 1); };
  function setDraft(text: string) {
    localStorage.setItem(draftKey(selected.current), JSON.stringify({ text, at: Date.now() }));
    draftState(text);
  }
  async function request<T>(path: string, body?: unknown): Promise<T> {
    const response = await fetch("/api" + path, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? {} : { "Content-Type": "application/json", "X-Filing-Token": token.current },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Local request failed");
    return data;
  }
  function receive(inv: Investigation) {
    const previous = records.current.get(inv.id)?.turns.at(-1);
    const last = inv.turns.at(-1);
    records.current.set(inv.id, inv);
    revisions.current.set(inv.id, (revisions.current.get(inv.id) || 0) + 1);
    if (last && failures.includes(last.status) && previous?.status !== last.status && !readDraft(inv.id)) {
      localStorage.setItem(draftKey(inv.id), JSON.stringify({ text: last.question, at: Date.now() }));
      if (selected.current === inv.id) draftState(last.question);
    }
    setHistory(items => items && items.map(item => item.id === inv.id ? inv : item));
    repaint();
  }
  function select(inv: Investigation | null) {
    epoch.current++;
    selected.current = inv?.id || null;
    if (inv) {
      records.current.set(inv.id, inv);
      localStorage.setItem("filing-investigation", inv.id);
    } else localStorage.removeItem("filing-investigation");
    draftState(readDraft(selected.current));
    setError("");
    repaint();
  }
  useEffect(() => {
    mounted.current = true;
    let inFlight = false;
    async function poll() {
      if (inFlight) return;
      inFlight = true;
      try {
        const session = await request<{token: string; running: boolean}>("/session");
        if (!mounted.current) return;
        token.current = session.token;
        setRunning(session.running);
        const ids = new Set([...records.current.values()].filter(i => i.turns.some(unresolved)).map(i => i.id));
        if (selected.current) ids.add(selected.current);
        for (const id of ids) {
          const revision = revisions.current.get(id) || 0;
          const inv = await request<Investigation>("/investigations/" + id);
          if (mounted.current && revision === (revisions.current.get(id) || 0)) receive(inv);
        }
      } catch (e) {
        if (mounted.current) setError((e as Error).message);
      } finally { inFlight = false; }
    }
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith("filing-draft-") && !readDraft(key.slice("filing-draft-".length))) localStorage.removeItem(key);
    }
    const startEpoch = epoch.current;
    request<{token: string; running: boolean}>("/session").then(async session => {
      if (!mounted.current) return;
      token.current = session.token;
      setRunning(session.running);
      const id = localStorage.getItem("filing-investigation");
      if (id) {
        try {
          const inv = await request<Investigation>("/investigations/" + id);
          if (mounted.current && epoch.current === startEpoch) select(inv);
        } catch (e) { if (mounted.current) setError((e as Error).message); }
      }
      if (mounted.current) setReady(true);
    }).catch(e => { if (mounted.current) setError(e.message); });
    const timer = setInterval(() => void poll(), 650);
    return () => { mounted.current = false; clearInterval(timer); };
  }, []);
  async function action(fn: () => Promise<void>) {
    setError("");
    try { await fn(); } catch (e) { setError((e as Error).message); }
  }
  async function openHistory() {
    const items = await request<Investigation[]>("/history");
    items.forEach(i => records.current.set(i.id, i));
    setHistory(items);
  }
  async function newInvestigation(text = "") {
    if (sendingRef.current) return;
    sendingRef.current = true; setSending(true);
    const version = ++epoch.current;
    try {
      const inv = await request<Investigation>("/investigations", {});
      receive(inv);
      if (epoch.current === version) { select(inv); setDraft(text); }
    } finally { sendingRef.current = false; setSending(false); }
  }
  async function submit(question: string, language: Lang, retry?: Turn) {
    const inv = selected.current ? records.current.get(selected.current) : null;
    if (!question.trim() || sendingRef.current || running || inv?.saved || inv?.turns.some(unresolved)) return;
    sendingRef.current = true; setSending(true);
    const version = epoch.current;
    await action(async () => {
      const target = inv || await request<Investigation>("/investigations", {});
      if (!inv && epoch.current === version) select(target);
      const turn = await request<Turn>("/investigations/" + target.id + "/turns", {
        question, language: retry?.language || language,
        request_id: crypto.randomUUID(), retry_of: retry?.id,
      });
      const latest = records.current.get(target.id) || target;
      receive({ ...latest, turns: latest.turns.some(t => t.id === turn.id) ? latest.turns : [...latest.turns, turn] });
      localStorage.removeItem(draftKey(target.id));
      if (selected.current === target.id) draftState("");
      setRunning(true);
    });
    sendingRef.current = false; setSending(false);
  }
  async function save(identity: string) { receive(await request<Investigation>("/investigations/" + identity + "/save", {})); }
  async function fork(identity: string, mode: string) {
    const version = epoch.current;
    const original = records.current.get(identity);
    const inv = await request<Investigation>("/investigations/" + identity + "/fork", { mode });
    receive(inv);
    if (epoch.current === version && selected.current === identity) {
      select(inv); setDraft(mode === "refresh" ? original?.turns.at(-1)?.question || "" : "");
    }
  }
  async function remove(identity: string) {
    await request("/investigations/" + identity + "/delete", {});
    records.current.delete(identity);
    localStorage.removeItem(draftKey(identity));
    if (selected.current === identity) select(null);
    await openHistory();
  }
  async function recover(identity: string, discard = false) {
    receive(await request<Investigation>("/investigations/" + identity + (discard ? "/discard-unstored" : "/retry-storage"), {}));
  }
  return { mode: "live" as const, current: selected.current ? records.current.get(selected.current) || null : null,
    ready, error, setError, draft, setDraft, sending, running, history, setHistory,
    select, openHistory, newInvestigation, submit, save, fork, remove, recover, action,
    cancel: (id: string) => request("/turns/" + id + "/cancel", {}) };
}
