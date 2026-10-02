# Pending Memory Review SOP

Hermes may stage background `replace` and `remove` operations in a pending directory even when the front-end `memory.write_approval` setting permits direct writes. The destructive-operation gate can be implemented in runtime code and may have no configuration switch. Verify the behavior in the target version.

## Position in the run

Run the reviewer after correction reconciliation and before watermark measurement:

```bash
$PY -B scripts/memory_pending_review.py --list
```

The script lists candidates; semantic judgment remains at the model layer.

## Decisions

- If proposals share a pinned entry, judge only the newest proposal and discard older duplicates.
- Approve a faithful consolidation only when its pin is alive and protected bytes remain intact.
- For a dead pin, inspect the current MEMORY.md/USER.md entry. If the change is already present, discard as superseded. If it is absent and still valid, rewrite the live entry with the memory tool, then discard the stale staged record.
- Discard legacy proposals without a matched entry, identity-class proposals, and proposals targeting protected blocks, using the configured reason codes.
- Uncertain proposals are internally deferred/discarded under the instance policy; never request user input.

Apply decisions with `--approve ID... --run-id <run_id>` or discard with `--discard ID... --reason <reason> --run-id <run_id>`. Each record produces one PENDING_REVIEW receipt.

## Boundary

This workflow covers staged MEMORY.md and USER.md writes only. Physical fact_store deletion remains outside its authority. Successful decisions remain internal and do not trigger a user notification.

## Troubleshooting

- Many dead pins usually mean later edits changed the anchored entry; follow the current-state check above.
- A legacy-unpinned replay refusal means the proposal lacks a safe source anchor; discard it.
- Import failures usually mean the process is not using the Hermes runtime Python or its runtime modules are absent from `sys.path`.
