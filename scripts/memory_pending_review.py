#!/usr/bin/env python3
"""PORTED: paths parameterized, reads HERMES_HOME.
Dreaming 内嵌 memory pending 审批器（2026-10-01 用户拍板：方案 1，并入 dreaming，不单开 cron）。

背景：Hermes 硬编码「background review 不得无人值守 replace/remove 记忆条目」
（runtime/tools/memory_tool.py::_background_delete_gate，无配置开关），
dreaming 夜间的合并提议全部堆进 $HERMES_HOME/pending/memory/ 等人工批。
本脚本把审批权收进 dreaming 流程：--list 出账 → dreaming agent 逐条判 →
--approve / --discard 落账。判断留模型层，本脚本只做机械：列账、重放、丢弃、回执。

用法（PY=<HERMES_PYTHON>）：
  $PY -B scripts/memory_pending_review.py --list
  $PY -B scripts/memory_pending_review.py --dry --approve ID [ID...]
  $PY -B scripts/memory_pending_review.py --approve ID [ID...] --run-id <dream_run_id>
  $PY -B scripts/memory_pending_review.py --discard ID [ID...] --reason "..." [--run-id <dream_run_id>]

回执：`$HERMES_HOME/state/pending-memory-review.jsonl`（逐条追加）。
纪律（与 memory-consolidation skill 的 pending-review SOP 同步）：
  - 同一 matched_entry 的重复提议只留最新，旧的一律 discard（--list 里 dup_group 标出）。
  - pin_alive=false 说明锚点条目已被后来的整理改写：核对改动是否已实质落地，
    已落地 discard（reason=superseded），未落地由 dreaming 当场用 memory 工具直接重写，再 discard。
  - 无 matched_entry 的 legacy 记录 replay 必拒，直接 discard（reason=legacy-unpinned）。
  - target=user（USER.md）的记录与 memory 同规则判决（R-P1-02 已 superseded，
    USER.md 夜间可自动管理）；但身份/红线类内容夜间无人值守不落地，
    一律 discard（reason=identity-main-session，由主会话亲笔路径处理）。
  - matched_entry 命中保护集（dream_protected_check EXPECTED）的一律 discard（reason=protected-block）。
"""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import sys

from tools import write_approval as wa
from tools.memory_tool import load_on_disk_store, apply_memory_pending, destructive_ops

HERMES_HOME = Path(os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes")))
PENDING_DIR = HERMES_HOME / "pending" / "memory"
RECEIPTS = HERMES_HOME / "state" / "pending-memory-review.jsonl"
LOCK = PENDING_DIR / ".review.lock"
MEMORIES_DIR = HERMES_HOME / "memories"


def _now_iso():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()


def _receipt(action, rec_id, result, reason="", run_id=""):
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": _now_iso(), "kind": "PENDING_REVIEW", "action": action,
             "id": rec_id, "result": result, "reason": reason, "run_id": run_id}
    with RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _file_text(target):
    name = "USER.md" if target == "user" else "MEMORY.md"
    p = MEMORIES_DIR / name
    try:
        return p.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return ""


def _op_view(op, file_text):
    pinned = op.get("matched_entry") or ""
    return {
        "action": op.get("action"),
        "target": op.get("target", "memory"),
        "old_text": op.get("old_text") or "",
        "content": op.get("content") or "",
        "matched_entry": pinned,
        "pin_alive": bool(pinned) and [entry.strip("\n") for entry in file_text.split("\n§\n")].count(pinned) == 1,
    }


def cmd_list():
    records = wa.list_pending(wa.MEMORY)
    texts = {}
    out = []
    groups = {}
    for rec in records:
        payload = rec.get("payload", {})
        target = payload.get("target", "memory")
        ops = payload.get("operations") if payload.get("action") == "batch" else [payload]
        views = []
        for op in ops or []:
            op = dict(op or {})
            op.setdefault("target", target)
            op_target = op["target"]
            if op_target not in texts:
                texts[op_target] = _file_text(op_target)
            views.append(_op_view(op, texts[op_target]))
        # Only complete, identical pins on identical targets establish duplicates.
        key = ("pins", tuple((v["target"], v["matched_entry"]) for v in views)) if views and all(
            v["matched_entry"] for v in views) else ("record", rec["id"])
        groups.setdefault(key, []).append(rec["id"])
        out.append({
            "id": rec["id"],
            "created_at": datetime.datetime.fromtimestamp(
                rec.get("created_at", 0), datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
            "origin": rec.get("origin", "?"),
            "target": target,
            "summary": (rec.get("summary") or "")[:200],
            "ops": views,
            "_group_key": key,
        })
    for item in out:
        members = groups[item.pop("_group_key")]
        item["dup_group"] = members if len(members) > 1 else None
    print(json.dumps({"count": len(out), "records": out}, ensure_ascii=False, indent=1))


def _load_record(rec_id):
    _record_id(rec_id)
    p = PENDING_DIR / f"{rec_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8-sig"))


def cmd_approve(ids, dry, run_id):
    store = None if dry else load_on_disk_store()
    ok = fail = 0
    for rec_id in ids:
        rec = _load_record(rec_id)
        if rec is None:
            print(f"{rec_id}: no such pending record")
            fail += 1
            continue
        payload = rec.get("payload", {})
        if dry:
            unpinned = [op for op in destructive_ops(payload) if not op.get("matched_entry")]
            print(f"{rec_id}: dry — target={payload.get('target', 'memory')} "
                  f"ops={len(payload.get('operations') or [payload])} unpinned={len(unpinned)}")
            continue
        result = apply_memory_pending(payload, store)
        if result.get("success"):
            wa.discard_pending(wa.MEMORY, rec_id)
            _receipt("approve", rec_id, "applied", run_id=run_id)
            print(f"{rec_id}: applied")
            ok += 1
        else:
            _receipt("approve", rec_id, "refused", reason=str(result.get("error", ""))[:200], run_id=run_id)
            print(f"{rec_id}: REFUSED — {result.get('error')} (left in queue)")
            fail += 1
    if not dry:
        print(f"approve done: {ok} applied, {fail} failed")
    return 1 if fail else 0


def cmd_discard(ids, reason, run_id, dry=False):
    n = 0
    for rec_id in ids:
        _record_id(rec_id)
        if dry:
            print(f"{rec_id}: dry — discard ({reason})")
            continue
        if wa.discard_pending(wa.MEMORY, rec_id):
            _receipt("discard", rec_id, "dropped", reason=reason, run_id=run_id)
            print(f"{rec_id}: discarded ({reason})")
            n += 1
        else:
            print(f"{rec_id}: no such pending record")
    print(f"discard done: {n} dropped")
    return 0 if dry or n == len(ids) else 1


def _record_id(value):
    if not value or value in (".", "..") or "/" in value or "\\" in value:
        raise ValueError("pending ID must be a filename without path separators")
    return value


def main():
    ap = argparse.ArgumentParser(description="Dreaming memory pending reviewer")
    actions = ap.add_mutually_exclusive_group()
    actions.add_argument("--list", action="store_true")
    actions.add_argument("--approve", nargs="+", type=_record_id, default=None, metavar="ID")
    actions.add_argument("--discard", nargs="+", type=_record_id, default=None, metavar="ID")
    ap.add_argument("--reason", default="")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--run-id", default="")
    args = ap.parse_args()

    if args.discard is not None and not args.reason:
        ap.error("--discard needs --reason")
    if args.list:
        cmd_list()
        return 0
    if args.approve is None and args.discard is None:
        ap.print_help()
        return 0
    if args.dry:
        if args.approve is not None:
            return cmd_approve(args.approve, True, args.run_id)
        return cmd_discard(args.discard, args.reason, args.run_id, dry=True)

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.approve is not None:
            return cmd_approve(args.approve, False, args.run_id)
        return cmd_discard(args.discard, args.reason, args.run_id)


if __name__ == "__main__":
    raise SystemExit(main())
