#!/usr/bin/env python3
"""PORTED: paths parameterized, reads HERMES_HOME.
Sweep api_server sessions. Default: 26h window, >=6 user messages.

--since/--until: bounded historical replay, grouped into --slice-hours shards.
Durable plans precede fact writes; replay reuses identical generated facts.
Only adds facts; never edits or deletes existing fact content.

Partial success: a session whose whole provider chain runs out is marked
FAIL (status=provider_failed) with its cursor kept, and the sweep continues.
The receipt carries summary.statuses + summary.incomplete per session, and
stderr gets one detail line; exit code is non-zero only when every session
attempted this round failed.
"""
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from fact_extract_state import (RunReceipt, source_chunks, pending_sessions, bounded_lock,
                                record_failure, resolve_failure)

HERMES_HOME = Path(os.path.expanduser(os.environ.get('HERMES_HOME', '~/.hermes')))
STATE_DB = HERMES_HOME / 'state.db'
STORE_DB = HERMES_HOME / 'memory_store.db'
WINDOW_SECONDS = 26 * 3600
JOURNAL = HERMES_HOME / 'backups/fact-extract-v2/sweep'


def timestamp(value):
    dt = datetime.datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    return dt.timestamp()


def atomic_json(path, data):
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush(); os.fsync(f.fileno())
    temp.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def chunks(rows, max_chars=18000):
    return source_chunks(rows,max_chars)


# 会话级终态：这三种算「该会话正常结束」，其余（provider_failed/failed，以及将来
# 可能新增的未知状态）一律按失败计——未知状态 fail-closed，不允许被静默当成成功。
SESSION_OK_STATUSES = ('ok','already_consumed','legacy_coverage_held')


def session_summary(sessions):
    """per-session 状态汇总：条数 + 按状态计数 + 失败会话明细（incomplete）。"""
    statuses={}
    for item in sessions:statuses[item['status']]=statuses.get(item['status'],0)+1
    incomplete=[{'session_id':item['session_id'],'status':item['status'],'error':item['error']}
                for item in sessions if item['status'] not in SESSION_OK_STATUSES]
    return {'sessions':len(sessions),'statuses':statuses,
            'ok':sum(n for k,n in statuses.items() if k in SESSION_OK_STATUSES),
            'failed':sum(n for k,n in statuses.items() if k not in SESSION_OK_STATUSES),
            'incomplete':incomplete,'complete':not incomplete}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--since',type=timestamp)
    ap.add_argument('--until',type=timestamp)
    ap.add_argument('--slice-hours',type=float,default=24)
    ap.add_argument('--dry-run',action='store_true')
    for option in ('db','backup-root','log-path','queue-path'):
        ap.add_argument('--'+option)
    args=ap.parse_args()
    if args.slice_hours<=0: ap.error('--slice-hours must be positive')
    end=args.until if args.until is not None else time.time()
    start=args.since if args.since is not None else end-WINDOW_SECONDS
    if start>=end: ap.error('--since must precede --until')
    receipt=RunReceipt(JOURNAL/'runs', {'since':start,'until':end,'slice_hours':args.slice_hours}, args.dry_run)
    try:
        code=run_sweep(args,start,end,receipt)
    except (Exception,SystemExit) as exc:
        receipt.data['failures'].append({'status':'failed','error':type(exc).__name__,'detail':str(exc)[:300]})
        receipt.finish('partial' if receipt.data['processed'] else 'failed')
        print('sweep failed; receipt='+str(receipt.path),file=sys.stderr)
        return 1
    # S follows successful core work; failure cannot roll back shared source progress.
    if not args.dry_run:
        soft_review_after_core(args,receipt)
    summary=receipt.data.get('summary') or {}
    # 部分成功语义：有会话失败不等于整轮失败——仍是 partial（本轮干出了活），
    # 只有「一条都没落库」才算 failed。exit code 与 receipt 状态解耦：只有本轮
    # 尝试过的会话全部失败时非 0（卡片 t_ee69010c 第 3 条）。两种情况都往 stderr
    # 写一行明细，避免「今天有 6 场没抽出来」被静默吞掉。
    status='completed'
    if summary.get('incomplete'):
        status='partial' if receipt.data['processed'] else 'failed'
    if receipt.data.get('soft_review',{}).get('status') not in (None,'ok','disabled','dry_run') and status=='completed':
        status='partial'
    receipt.finish(status)
    if summary.get('incomplete'):
        print(f"{'sweep failed' if status=='failed' else 'sweep incomplete'}: "
              f"{summary['failed']}/{summary['sessions']} sessions failed "
              f"statuses={json.dumps(summary['statuses'],ensure_ascii=False,sort_keys=True)} "
              f"incomplete={json.dumps(summary['incomplete'],ensure_ascii=False)} "
              f"receipt={receipt.path}",file=sys.stderr)
    return code


def soft_review_after_core(args, receipt, *, judge=None, embedding_client=None):
    from fact_semantic_review import drain, mode
    db=getattr(args,'db',None) or STORE_DB
    try:
        # Off is read-only and works on old non-v2 fixtures without side effects.
        if mode(db)['mode']=='off':
            receipt.data['soft_review']={'status':'disabled','calls':0,'tokens':0}
        else:
            receipt.data['soft_review']=drain(db,apply=True,live=judge is None,judge=judge,
                embedding_client=embedding_client,
                backup_root=getattr(args,'backup_root',None),log_path=getattr(args,'log_path',None),
                queue_path=getattr(args,'queue_path',None))
    except Exception as exc:
        receipt.data['soft_review']={'status':'partial','error_class':type(exc).__name__}
    receipt.save()


def run_sweep(args,start,end,receipt):
    conn=sqlite3.connect(f'file:{STATE_DB}?mode=ro',uri=True)
    try:
        return _run_locked(args,start,end,receipt,conn)
    finally:
        conn.close()


def _run_locked(args,start,end,receipt,conn):
    # Keep correction coverage independent from the ordinary HAVING count>=6 gate.
    # Capture is stdlib-only and its state.db handle is opened mode=ro by the module.
    if not args.dry_run:
        from dream_corrections import capture_since
        state_dir = Path(STATE_DB).parent / "state"
        correction_receipt = capture_since(
            STATE_DB,
            state_dir / "corrections.jsonl",
            state_dir / "corrections-cursor.json",
            now=end,
        )
        receipt.data['correction_capture'] = correction_receipt
        receipt.save()
    candidates=conn.execute("""SELECT m.session_id,min(m.timestamp),count(*) FROM messages m
        JOIN sessions s ON s.id=m.session_id WHERE s.source='api_server'
        AND m.role='user' AND m.timestamp>? AND m.timestamp<=?
        AND m.active=1 AND m.content IS NOT NULL AND m.content!=''
        GROUP BY m.session_id HAVING count(*)>=6 ORDER BY min(m.timestamp),m.session_id""",(start,end)).fetchall()
    receipt.data['eligible']=len(candidates)
    receipt.save()
    if args.dry_run:
        receipt.skip('dry_run');return 0
    with bounded_lock(JOURNAL/'sweep.lock'):
        spec=importlib.util.spec_from_file_location('sweep_extractor',str(HERMES_HOME / 'scripts/session_fact_extract.py'))
        extractor=importlib.util.module_from_spec(spec);spec.loader.exec_module(extractor)
        env=extractor.load_env()
        # 回退链顺序是用户 2026-09-15 指定的硬约束；每轮把它写进 receipt 供事后核对。
        receipt.data['provider_chain']=extractor.provider_chain_labels(env)
        receipt.save()
        # v2 technical observations have their own durable ledger; retry at most
        # three each sweep, even when this run has no new source sessions.
        from factstore_v2_common import connect as v2_connect, has_v2
        from contextlib import closing
        with closing(v2_connect(STORE_DB)) as v2_conn:
            v2_ready=has_v2(v2_conn)
        if v2_ready:
            from factstore_v2_ingest import resume_pending
            observations=resume_pending(db=STORE_DB,limit=3)
            receipt.data['v2_observations_retried']=len(observations)
            receipt.data['v2_observations_pending']=sum(x['observation_status']=='pending' for x in observations)
            receipt.save()
        if args.since is None:
            seen={r[0] for r in candidates}
            resumable=pending_sessions(extractor.SHARED_ROOT)
            for directory in (JOURNAL,extractor.LEGACY_SWEEP):
                for path in sorted(directory.glob('*.json')):
                    if len(path.stem)!=64:continue
                    progress=json.loads(path.read_text())
                    if progress.get('pending'):resumable.append(progress['session_id'])
            for sid in resumable:
                if sid not in seen:
                    candidates.append((sid,start,0));seen.add(sid)
            receipt.data['resumed_outside_window']=len(candidates)-receipt.data['eligible']
        if not candidates:
            receipt.skip('no_candidates');return 0
        failures=[]
        sessions=[]
        for sid,first,_ in candidates:
            extractor.CURRENT_SESSION=sid
            key=hashlib.sha256(sid.encode()).hexdigest()
            progress_path=JOURNAL/(key+'.json')
            old_path=extractor.LEGACY_SWEEP/(key+'.json')
            attempt_records=[];status='ok';error=None
            try:
                progress=json.loads(progress_path.read_text()) if progress_path.exists() else (
                    json.loads(old_path.read_text()) if old_path.exists() else {'session_id':sid,'last_id':0})
                lower=start if args.since is not None else 0
                rows=conn.execute("SELECT id,role,content FROM messages WHERE session_id=? AND id>? AND timestamp>? AND timestamp<=? AND active=1 AND role IN ('user','assistant') AND content IS NOT NULL AND content!='' ORDER BY id",(sid,progress['last_id'],lower,end)).fetchall()
                if not rows and not progress.get('pending'):
                    receipt.skip('no_new_messages');continue
                if not progress.get('pending'):
                    progress['pending']=list(chunks(rows))
                    progress['pending_last_id']=max(r[0] for r in rows)
                    atomic_json(progress_path,progress)
                if args.since is not None:
                    allowed={r[0] for r in rows}
                    if any(x['id'] not in allowed for c in progress['pending'] for x in c):
                        raise ValueError('pending source outside explicitly requested interval')
                full_rows=conn.execute("SELECT id,role,content FROM messages WHERE session_id=? AND active=1 AND role IN ('user','assistant') AND content IS NOT NULL AND content!='' ORDER BY id",(sid,)).fetchall()
                pending_before=receipt.data['pending'];added_before=receipt.data['added']
                receipt.data['pending']+=len(progress['pending']);receipt.save()
                def on_progress(event,amount):
                    if event=='pending':receipt.data['pending']=pending_before+amount
                    else:
                        receipt.data['processed']+=1;receipt.data['pending']-=1
                        receipt.data['added']=added_before+amount
                    receipt.save()
                result=extractor.process_sources(sid,progress['pending'],env,rows=full_rows,on_progress=on_progress)
                if result['already_consumed']:receipt.skip('shared_already_consumed');status='already_consumed'
                if result['legacy_held']:receipt.skip('legacy_coverage_held');status='legacy_coverage_held'
                if result['pending']:raise RuntimeError('source units deferred')
                progress['last_id']=progress.pop('pending_last_id')
                progress.pop('pending')
                atomic_json(progress_path,progress)  # v2 only; never old_path
                resolve_failure(extractor.SHARED_ROOT,sid,'sweep-source-read')
            except extractor.ProviderExhausted as exc:
                # 单场 provider 链用尽（含重试）：只标该会话，不写 FAILED 标记、
                # 不抛出去中断本轮；其余会话照常处理。
                status='provider_failed';error=str(exc)[:300]
                if not getattr(exc,'extraction_recorded',False):
                    record_failure(extractor.SHARED_ROOT,sid,'sweep-source-read','ProviderExhausted',stage='source_read')
                failures.append({'session_id':sid,'status':status,'error':'ProviderExhausted','detail':error})
                extractor.log(f'session={sid} outcome=provider_failed error=ProviderExhausted; cursor retained')
            except (Exception,SystemExit) as exc:
                status='failed';error=str(exc)[:300]
                if not getattr(exc,'extraction_recorded',False):
                    record_failure(extractor.SHARED_ROOT,sid,'sweep-source-read',type(exc).__name__,stage='source_read')
                failures.append({'session_id':sid,'status':status,'error':type(exc).__name__,'detail':error})
                extractor.log(f'session={sid} outcome=failed error={type(exc).__name__}; cursor retained')
            finally:
                # 每次 attempt 的 provider/耗时/错误类型都进 receipt（含成功那一次）。
                attempt_records=extractor.drain_attempts()
            sessions.append({'session_id':sid,'status':status,'error':error,'attempts':attempt_records})
        receipt.data['failures']=failures
        receipt.data['sessions']=sessions
        summary=session_summary(sessions)
        receipt.data['summary']=summary
        receipt.save()
        # 单场失败不再拖垮整轮：只有「本轮尝试过的会话全部失败」才返回非 0；
        # 部分失败按 partial 记 receipt + stderr 明细，exit code 保持 0。
        return 1 if sessions and not summary['ok'] else 0

if __name__=='__main__':raise SystemExit(main())
