"""Serial graph execution with durable step receipts and attempt lineage."""

import copy
import threading
import time
from typing import TypedDict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from slice.core import financial_answer
from slice.runtime import Runtime, Stopped
from slice.store import now, uid


class State(TypedDict):
    investigation: str
    turn: str
    last_completed: str


class Engine:
    def __init__(self, store, runtime=None):
        self.store = store
        self.runtime = runtime or Runtime()
        self.gate = threading.Lock()
        self.events = {}
        self.pool = ConnectionPool(
            store.dsn,
            min_size=0,
            max_size=1,
            max_idle=5,
            open=True,
            kwargs={"autocommit": True, "row_factory": dict_row},
        )
        self.checkpoints = PostgresSaver(self.pool)
        self.checkpoints.setup()
        graph = StateGraph(State)
        for name in ("interpret", "evidence", "answer"):
            graph.add_node(name, lambda state, step=name: self.step(state, step))
        graph.add_edge(START, "interpret")
        graph.add_edge("interpret", "evidence")
        graph.add_edge("evidence", "answer")
        graph.add_edge("answer", END)
        self.graph = graph.compile(checkpointer=self.checkpoints)

    def submit(
        self, identity, question, language, request_id, retry=None, diagnostics=False
    ):
        data = self.store.get(identity)
        existing = next(
            (t for t in data["turns"] if t["request_id"] == request_id), None
        )
        if existing:
            if existing["question"] != question or existing["language"] != language:
                raise ValueError("Request identity already has different inputs")
            return existing
        if not self.gate.acquire(blocking=False):
            raise ValueError("One local investigation is already running")
        try:

            def append(body):
                if body["saved"]:
                    raise ValueError(
                        "Saved results are immutable; Continue or Refresh creates a new investigation"
                    )
                if any(t["status"] in ("running", "queued") for t in body["turns"]):
                    raise ValueError("Reattach to the existing turn")
                previous = (
                    next((t for t in body["turns"] if t["id"] == retry), None)
                    if retry
                    else None
                )
                if retry and (
                    not previous
                    or previous["status"]
                    not in (
                        "error",
                        "cancelled",
                        "interrupted",
                        "timeout",
                        "stop_unconfirmed",
                    )
                    or previous.get("retry_of")
                    or any(t.get("retry_of") == retry for t in body["turns"])
                ):
                    raise ValueError(
                        "Only one explicit retry per failed turn is permitted"
                    )
                if previous and (
                    question != previous["question"] or language != previous["language"]
                ):
                    raise ValueError("Retry inputs must match the failed turn")
                turn = {
                    "id": uid(),
                    "request_id": request_id,
                    "question": question,
                    "language": language,
                    "status": "queued",
                    "created_at": now(),
                    "context": copy.deepcopy(body["pending"] or body["accepted"]),
                    "retry_of": retry,
                    "diagnostics": diagnostics,
                    "steps": [
                        {"name": s, "status": "pending"}
                        for s in ("interpret", "evidence", "answer")
                    ],
                }
                if previous:
                    turn["context"] = copy.deepcopy(previous["context"])
                    # Completed durable steps are reused; only the interrupted step is restarted.
                    for key in ("intent", "model_record", "answer"):
                        if key in previous:
                            turn[key] = copy.deepcopy(previous[key])
                body["turns"].append(turn)

            result = self.store.change(identity, append)["turns"][-1]
            self.events[result["id"]] = threading.Event()
            threading.Thread(
                target=self.execute, args=(identity, result["id"]), daemon=True
            ).start()
            return result
        except Exception:
            self.gate.release()
            raise

    def update(self, identity, tid, fn):
        def apply(body):
            fn(next(t for t in body["turns"] if t["id"] == tid), body)

        return self.store.change(identity, apply)

    def step(self, state, name):
        identity, tid = state["investigation"], state["turn"]
        if self.events[tid].is_set():
            raise Stopped(True)
        started = time.monotonic()

        def start(turn, body):
            turn["status"] = "running"
            step = next(s for s in turn["steps"] if s["name"] == name)
            step.update(status="running", started_at=now())

        data = self.update(identity, tid, start)
        turn = next(t for t in data["turns"] if t["id"] == tid)
        updates = {}
        if name == "interpret" and "intent" not in turn:
            intent, record = self.runtime.interpret(
                turn["question"], turn["context"], self.events[tid]
            )
            if not turn.get("diagnostics"):
                record.pop("content", None)
            updates.update(intent=intent, model_record=record)
        elif name == "evidence" and "answer" not in turn:
            snapshot = self.store.snapshot(data["snapshot_id"])
            updates["answer"] = financial_answer(
                turn["intent"], snapshot, turn["question"]
            )

        def finish(t, body):
            t.update(updates)
            s = next(s for s in t["steps"] if s["name"] == name)
            s.update(
                status="complete",
                seconds=time.monotonic() - started,
                reused=(name == "interpret" and "intent" in turn)
                or (name == "evidence" and "answer" in turn),
            )
            if name == "answer":
                t["status"] = "complete"
                t["completed_at"] = now()
                if t["answer"]["operation"] == "clarify":
                    body["pending"] = t["intent"]
                elif t["answer"]["operation"] in ("report", "compare"):
                    body.update(accepted=t["intent"], pending=None)
                else:
                    body["pending"] = None

        self.update(identity, tid, finish)
        return {**state, "last_completed": name}

    def execute(self, identity, tid):
        started = time.monotonic()
        try:
            self.graph.invoke(
                {"investigation": identity, "turn": tid, "last_completed": ""},
                {"configurable": {"thread_id": identity}},
            )
        except Stopped as exc:
            status = (
                ("timeout" if exc.timeout else "cancelled")
                if exc.confirmed
                else "stop_unconfirmed"
            )
            self.fail(
                identity,
                tid,
                status,
                "Local inference stopped."
                if exc.confirmed
                else "Stop unconfirmed. Restart the controlled Ollama server before retrying.",
            )
        except Exception as exc:  # noqa: BLE001 - persist a terminal failure for the worker boundary
            self.fail(
                identity,
                tid,
                "error",
                str(exc)
                if isinstance(exc, ValueError)
                else "Local execution failed; inspect the application and retry once.",
            )
        finally:
            self.update(
                identity,
                tid,
                lambda t, b: t.update(wall_seconds=time.monotonic() - started),
            )
            self.events.pop(tid, None)
            self.gate.release()

    def fail(self, identity, tid, status, error):
        def mark(turn, body):
            turn.update(status=status, error=error)
            for step in turn["steps"]:
                if step["status"] == "running":
                    step["status"] = status

        self.update(identity, tid, mark)

    def cancel(self, tid):
        if tid in self.events:
            self.events[tid].set()
