"""Serial local execution; investigation transitions belong to the lifecycle module."""

import threading
import time
from typing import TypedDict

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from slice.financial import financial_answer
from slice.lifecycle import Investigations, StorageUnavailable
from slice.runtime import Runtime, Stopped


class State(TypedDict):
    investigation: str
    turn: str
    last_completed: str


class Engine:
    def __init__(self, store, runtime=None):
        self.store = store
        self.investigations = Investigations(store)
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

    def submit(self, identity, question, language, request_id, retry=None, diagnostics=False):
        data = self.investigations.get(identity)
        existing = next((t for t in data['turns'] if t['request_id'] == request_id), None)
        if existing:
            if existing['question'] != question or existing['language'] != language:
                raise ValueError('Request identity already has different inputs')
            return existing
        if not self.gate.acquire(blocking=False):
            raise ValueError('One local investigation is already running')
        try:
            result = self.investigations.queue(identity, question, language, request_id, retry, diagnostics)
            self.events[result['id']] = threading.Event()
            threading.Thread(target=self.execute, args=(identity, result['id']), daemon=True).start()
            return result
        except Exception:
            self.gate.release()
            raise

    def step(self, state, name):
        identity, tid = state['investigation'], state['turn']
        if self.events[tid].is_set():
            raise Stopped(True)
        started = time.monotonic()
        turn = self.investigations.start_step(identity, name)
        updates = {}
        if name == 'interpret' and 'intent' not in turn:
            intent, record = self.runtime.interpret(turn['question'], turn['context'], self.events[tid])
            if not turn.get('diagnostics'):
                record.pop('content', None)
            updates.update(intent=intent, model_record=record)
        elif name == 'evidence' and 'answer' not in turn:
            data = self.investigations.get(identity)
            updates['answer'] = financial_answer(
                turn['intent'], self.store.snapshot(data['snapshot_id']), turn['question'])
        self.investigations.finish_step(identity, name, updates, time.monotonic() - started,
                                       (name == 'interpret' and 'intent' in turn)
                                       or (name == 'evidence' and 'answer' in turn))
        return {**state, 'last_completed': name}

    def execute(self, identity, tid):
        started = time.monotonic()
        status, error = 'complete', None
        try:
            self.graph.invoke({'investigation': identity, 'turn': tid, 'last_completed': ''},
                              {'configurable': {'thread_id': identity}})
        except Stopped as exc:
            status = ('timeout' if exc.timeout else 'cancelled') if exc.confirmed else 'stop_unconfirmed'
            error = ('Local inference stopped.' if exc.confirmed else
                     'Stop unconfirmed. Restart the controlled Ollama server before retrying.')
        except (StorageUnavailable, psycopg.Error):
            status, error = 'interrupted', 'Storage interrupted execution; completed steps can be reused.'
        except Exception as exc:
            status = 'error'
            error = str(exc) if isinstance(exc, ValueError) else 'Local execution failed; retry once.'
        finally:
            try:
                self.investigations.finalize(identity, status, time.monotonic() - started, error)
            finally:
                self.events.pop(tid, None)
                self.gate.release()

    def retry_storage(self, identity, discard=False):
        current = self.investigations.get(identity)
        if any(t['id'] in self.events for t in current['turns']):
            raise ValueError('Wait for execution cleanup before storage recovery')
        return self.investigations.retry_storage(identity, discard)

    def cancel(self, tid):
        if tid in self.events:
            self.events[tid].set()
