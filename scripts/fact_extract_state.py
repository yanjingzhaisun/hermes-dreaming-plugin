#!/usr/bin/env python3
"""PORTED: paths parameterized, reads HERMES_HOME.
Durable extraction receipts and shared state. Standard library only."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

DEFAULT_ROOT = Path(os.path.expanduser(os.environ.get('HERMES_HOME', '~/.hermes'))) / 'backups/fact-extract-v2/shared'


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


class RunReceipt:
    def __init__(self, directory, window, dry_run=False):
        self.started = time.monotonic()
        self.data = dict(version=2, run_id=uuid.uuid4().hex, status='started',
                         started_at=now(), finished_at=None, window=window,
                         eligible=0, processed=0, pending=0, skipped_reason={},
                         added=0, failures=[], dry_run=dry_run)
        self.path = Path(directory) / (self.data['run_id'] + '.json')
        self.save()

    def save(self):
        atomic_json(self.path, self.data)

    def skip(self, reason):
        counts = self.data['skipped_reason']
        counts[reason] = counts.get(reason, 0) + 1

    def finish(self, status):
        self.data.update(status=status, finished_at=now(),
                         elapsed_s=round(time.monotonic()-self.started, 6))
        self.save()


@contextmanager
def bounded_lock(path, timeout=2.0):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a+') as f:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError('extraction lock busy')
                time.sleep(min(0.05, max(0, deadline-time.monotonic())))
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)


def failure_path(root, session_id, unit_key):
    return Path(root)/'failures'/(digest([session_id, unit_key])+'.json')


def record_failure(root, session_id, unit_key, error, stage='extraction'):
    path = failure_path(root, session_id, unit_key)
    with bounded_lock(path.with_suffix('.lock')):
        item = json.loads(path.read_text()) if path.exists() else dict(
            session_id=session_id, unit_key=unit_key, first_failed_at=now(),
            failure_count=0, resolution_count=0)
        item.update(status='unresolved', last_failed_at=now(), error=error,
                    stage=stage, failure_count=item['failure_count']+1)
        atomic_json(path, item)
        return item


def resolve_failure(root, session_id, unit_key):
    path = failure_path(root, session_id, unit_key)
    # Absence and repeated success never create a fictitious resolution.
    if not path.exists(): return False
    with bounded_lock(path.with_suffix('.lock')):
        item = json.loads(path.read_text())
        if item['status'] == 'resolved': return False
        item.update(status='resolved', resolved_at=now(),
                    resolution_count=item['resolution_count']+1)
        atomic_json(path, item)
        return True


def query_failures(root, include_resolved=False):
    # Pure reads: no mkdir, lock, chmod, or SQLite initialization.
    result = []
    for path in sorted((Path(root)/'failures').glob('*.json')):
        item = json.loads(path.read_text())
        if include_resolved or item['status'] == 'unresolved': result.append(item)
    return result


def source_chunks(rows, max_chars=18000):
    current, size = [], 0
    for ident, role, text in rows:
        for offset, start in enumerate(range(0, len(text), max_chars-100)):
            piece = text[start:start+max_chars-100]
            if current and size+len(piece)+10 > max_chars:
                yield current
                current, size = [], 0
            current.append(dict(id=ident, offset=offset, role=role, content=piece))
            size += len(piece)+10
    if current: yield current


def atom_key(item):
    return digest({k:item[k] for k in ('id','offset','role','content')})


def source_unit(session_id, chunk):
    content_hash = digest(chunk)
    return dict(unit_key=digest([session_id, chunk[0]['id'],chunk[-1]['id'],content_hash]),
                first_id=chunk[0]['id'], last_id=chunk[-1]['id'],
                content_hash=content_hash, atoms=[atom_key(x) for x in chunk],
                source=chunk, status='pending', facts=None)


def session_path(root, session_id):
    return Path(root)/'sessions'/(hashlib.sha256(session_id.encode()).hexdigest()+'.json')


def pending_sessions(root):
    result=[]
    for p in sorted((Path(root)/'sessions').glob('*.json')):
        entry=json.loads(p.read_text())
        if any(u['status']=='pending' for u in entry['units']): result.append(entry['session_id'])
    return result


class SourceConflict(ValueError):
    pass


def consume_sources(root, session_id, chunks, extract, validate, write,
                    legacy_holds=(), max_units=None, on_progress=None, with_provenance=False):
    """One shared lock covers selection -> saved plan -> writes -> completion.

    Atom-level ownership makes grouping independent of which pipeline came first.
    Saved facts survive DB failures; history is never regenerated on replay.
    """
    path=session_path(root,session_id)
    with bounded_lock(path.with_suffix('.lock')):
        state=json.loads(path.read_text()) if path.exists() else dict(version=2,session_id=session_id,units=[])
        if state.get('version')!=2 or state.get('session_id')!=session_id:
            raise SourceConflict('shared ledger identity mismatch')
        atoms={atom_key(x):x for c in chunks for x in c}
        owned={key:u for u in state['units'] for key in u['atoms']}
        slots={(x['id'],x['offset']):atom_key(x) for u in state['units'] for x in u['source']}
        for key,item in atoms.items():
            old=slots.get((item['id'],item['offset']))
            if old is not None and old!=key:
                raise SourceConflict('source text changed at an already registered message fragment')
        held=set(legacy_holds)
        for chunk in chunks:
            fresh=[x for x in chunk if atom_key(x) not in owned and atom_key(x) not in held]
            if fresh:
                unit=source_unit(session_id,fresh)
                state['units'].append(unit)
                owned.update({key:unit for key in unit['atoms']})
        atomic_json(path,state)  # Persist pending input before the first API call.
        result=dict(processed=0,added=0,pending=0,already_consumed=0,legacy_held=len(held.intersection(atoms)))
        if on_progress:
            on_progress('pending',sum(u['status']=='pending' and bool(set(u['atoms']).intersection(atoms)) for u in state['units']))
        for unit in state['units']:
            overlap=set(unit['atoms']).intersection(atoms)
            if not overlap: continue
            if unit['status']=='done':
                result['already_consumed']+=len(overlap)
                resolve_failure(root,session_id,unit['unit_key'])
                continue
            if overlap!=set(unit['atoms']):
                raise SourceConflict('requested window only partially overlaps a pending unit')
            if max_units is not None and result['processed']>=max_units:
                result['pending']+=1
                continue
            transcript='\n'.join(('用户' if x['role']=='user' else '助手')+': '+x['content'] for x in unit['source'])
            try:
                if unit['facts'] is None:
                    unit['facts']=validate(extract(transcript),transcript)
                    atomic_json(path,state)
                else:
                    validate(unit['facts'],transcript)
                ids=[]
                for index,fact in enumerate(unit['facts']):
                    provenance=dict(producer='session-extraction',session_id=session_id,unit_key=unit['unit_key'],
                                    fact_index=index,source_atoms=unit['atoms'],message_ids=sorted({x['id'] for x in unit['source']}))
                    fid,added=write(fact,provenance) if with_provenance else write(fact)
                    ids.append(fid);result['added']+=int(added)
                unit.update(status='done',fact_ids=ids,completed_at=now())
                atomic_json(path,state)
                resolve_failure(root,session_id,unit['unit_key'])
                result['processed']+=1
                if on_progress:on_progress('completed',result['added'])
            except (Exception,SystemExit) as exc:
                record_failure(root,session_id,unit['unit_key'],getattr(exc,'reason',type(exc).__name__))
                exc.extraction_recorded=True
                raise
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Read-only extraction health query')
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--include-resolved', action='store_true')
    args = parser.parse_args()
    print(json.dumps(query_failures(args.root, args.include_resolved), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
