"""Durable investigation transitions and process-local storage recovery."""

import copy
import threading

import psycopg

from slice.store import BLOCKING, now, uid


class StorageUnavailable(ValueError):
    pass


class Investigations:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.working = {}
        self.failed = set()
        self.contexts = {}

    def get(self, identity):
        with self.lock:
            if identity not in self.working:
                return self.store.get(identity)
            body = copy.deepcopy(self.working[identity])
            if identity in self.failed:
                body['turns'][-1]['status'] = 'storage_failed'
                body['turns'][-1]['error'] = "Couldn't store this result"
                body['accepted'], body['pending'] = copy.deepcopy(self.contexts[identity])
            elif body['turns'][-1]['status'] not in BLOCKING:
                body['turns'][-1]['status'] = 'saving'
            return body

    def history(self):
        with self.lock:
            try:
                items = {i['id']: i for i in self.store.history()}
            except psycopg.Error:
                if not self.working:
                    raise StorageUnavailable('Storage unavailable; try again when the database is running')
                items = {}
            items.update({i: self.get(i) for i in self.working})
            return sorted(items.values(), key=lambda i: i['touched_at'], reverse=True)

    def available(self, identity):
        if identity in self.working:
            raise ValueError('Finish execution or resolve storage recovery first')

    def save(self, identity):
        with self.lock:
            self.available(identity)
            return self.store.save(identity)

    def create(self, parent=None, mode=None):
        with self.lock:
            if parent:
                self.available(parent)
            return self.store.create(parent, mode)

    def delete(self, identity):
        with self.lock:
            self.available(identity)
            self.store.delete(identity)

    def queue(self, identity, question, language, request_id, retry, diagnostics):
        with self.lock:
            self.available(identity)

            def append(body):
                if body['saved'] or any(t['status'] in BLOCKING for t in body['turns']):
                    raise ValueError('Saved or unfinished investigations cannot accept a new turn')
                previous = next((t for t in body['turns'] if t['id'] == retry), None)
                if retry and (not previous or previous['status'] not in
                              ('error', 'cancelled', 'interrupted', 'timeout', 'stop_unconfirmed')
                              or previous.get('retry_of')
                              or any(t.get('retry_of') == retry for t in body['turns'])):
                    raise ValueError('Only one explicit retry per failed turn is permitted')
                if previous and (question != previous['question'] or language != previous['language']):
                    raise ValueError('Retry inputs must match the failed turn')
                turn = dict(id=uid(), request_id=request_id, question=question, language=language,
                            status='queued', created_at=now(), diagnostics=diagnostics,
                            context=copy.deepcopy(body['pending'] or body['accepted']), retry_of=retry,
                            steps=[dict(name=s, status='pending') for s in ('interpret', 'evidence', 'answer')])
                if previous:
                    turn['context'] = copy.deepcopy(previous['context'])
                    for key in ('intent', 'model_record', 'answer'):
                        if key in previous:
                            turn[key] = copy.deepcopy(previous[key])
                body['turns'].append(turn)

            body = self.store.change(identity, append)
            self.working[identity] = body
            self.contexts[identity] = copy.deepcopy((body['accepted'], body['pending']))
            return copy.deepcopy(body['turns'][-1])

    def _persist(self, identity):
        candidate = copy.deepcopy(self.working[identity])
        turn = candidate['turns'][-1]

        def replace(body):
            existing = next((t for t in body['turns'] if t['id'] == turn['id']), None)
            if existing is None or body['saved'] or body['snapshot_id'] != candidate['snapshot_id']:
                raise ValueError('Investigation changed while its result was being stored')
            existing.clear()
            existing.update(copy.deepcopy(turn))
            body['accepted'] = copy.deepcopy(candidate['accepted'])
            body['pending'] = copy.deepcopy(candidate['pending'])

        try:
            self.store.change(identity, replace)
        except (psycopg.Error, ValueError) as exc:
            self.failed.add(identity)
            raise StorageUnavailable("Couldn't store this result; retry storage or discard it") from exc

    def start_step(self, identity, name):
        with self.lock:
            turn = self.working[identity]['turns'][-1]
            turn['status'] = 'saving' if name == 'answer' else 'running'
            next(s for s in turn['steps'] if s['name'] == name).update(status='running', started_at=now())
            self._persist(identity)
            return copy.deepcopy(turn)

    def finish_step(self, identity, name, updates, seconds, reused):
        with self.lock:
            turn = self.working[identity]['turns'][-1]
            turn.update(copy.deepcopy(updates))
            next(s for s in turn['steps'] if s['name'] == name).update(
                status='complete', seconds=seconds, reused=reused)
            self._persist(identity)

    def finalize(self, identity, status, seconds, error=None):
        with self.lock:
            body = self.working[identity]
            turn = body['turns'][-1]
            turn.update(status=status, wall_seconds=seconds)
            if error:
                turn['error'] = error
            if status == 'complete':
                turn['completed_at'] = now()
                operation = turn['answer']['operation']
                if operation == 'clarify':
                    body['pending'] = copy.deepcopy(turn['intent'])
                elif operation in ('report', 'compare'):
                    body.update(accepted=copy.deepcopy(turn['intent']), pending=None)
                else:
                    body['pending'] = None
            else:
                for step in turn['steps']:
                    if step['status'] == 'running':
                        step['status'] = status
            # A failed receipt write needs an explicit retry even if storage recovers quickly.
            if identity in self.failed:
                return
            try:
                self._persist(identity)
            except StorageUnavailable:
                return
            self._forget(identity)

    def _forget(self, identity):
        self.working.pop(identity, None)
        self.contexts.pop(identity, None)
        self.failed.discard(identity)

    def retry_storage(self, identity, discard=False):
        with self.lock:
            if identity not in self.failed:
                raise ValueError('No storage recovery is pending')
            original = copy.deepcopy(self.working[identity])
            if discard:
                body = self.working[identity]
                turn = body['turns'][-1]
                body['accepted'], body['pending'] = copy.deepcopy(self.contexts[identity])
                for key in ('answer', 'intent', 'model_record', 'completed_at'):
                    turn.pop(key, None)
                turn.update(status='discarded', error='Unstored result deliberately discarded')
            try:
                self._persist(identity)
            except StorageUnavailable:
                self.working[identity] = original
                raise
            self._forget(identity)
            return self.store.get(identity)
