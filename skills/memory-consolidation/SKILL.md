---
name: memory-consolidation
description: Safely audit and consolidate Hermes long-term memory and fact_store during a scheduled dreaming run.
version: 2.0.0
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [memory, fact_store, consolidation, dreaming, MEMORY.md, USER.md]
    category: autonomous-ai-agents
---

# Memory Consolidation

## Runtime contract

This skill describes a portable workflow, not a deployment-specific permission grant. Confirm the target instance's active policy and schema before writing. Keep USER.md non-protected writes within the deployment's explicitly configured boundary. Identity facts are deferred to a user-present session. Never modify protection expectations during a nightly run.

Four governing goals: zero blocking on user input; conversational corrections are captured and reconciled from source evidence; MEMORY and USER are independently managed against their watermarks; background staged rewrites are automatically reviewed within their permitted scope.

## Correction handling

Use the original user-authored message and its timestamp. Recency-wins applies only when subject, topic, scope, authorship, evidence and current state all independently match a sortable preference or work convention. Otherwise fail closed, record an internal deferred result and preserve all source data. A correction overrides the routine watermark gate. Re-read the corrected topic at its current version before any slimming operation.

## Pending memory review

Background destructive operations may be staged by Hermes regardless of the front-end `memory.write_approval` setting. The gate may be implemented in runtime code and may have no configuration switch. Review the pending queue after correction reconciliation and before measuring watermarks.

- For duplicate proposals with the same pinned entry, judge only the newest and discard older duplicates.
- Approve only faithful consolidations whose pinned source is still alive and whose protected bytes remain intact.
- Discard stale/superseded, legacy-unpinned, identity-class and protected-block proposals with the prescribed reason.
- If a pin is dead and the intended change is not present, rewrite the live entry using the memory tool first, then discard the stale proposal.
- Never request user input. This procedure covers staged MEMORY/USER writes only; fact_store physical deletion is outside its scope.

## Watermark slimming

Measure MEMORY.md and USER.md independently using UTF-8 character counts and their configured positive integer limits. Routine slimming begins at `chars >= ceil(limit * 0.85)`. Explicit corrections are independent of this gate.

Use this order:

1. Compress wording while preserving negation, dates, conditions, scope, identifiers and source atoms.
2. Merge same-topic entries only after checking every information atom and preserving order constraints.
3. Move content only after a verified destination exists. Recall facts require a live, readable and retrievable fact; operating rules require an existing in-scope skill. Back up and verify destination before removing source.
4. If still above threshold with no safe candidate, raise only the relevant limit using the configured self-adjustment formula and verify the result.

Before every write, require a unique exact match and a fresh source hash. After writing, verify both files' character counts and run `scripts/dream_protected_check.py`. Any mismatch, concurrent change or uncertain coverage means preserve the source and defer the action.

## Fact-store boundary

Additions require source evidence and a read-back check. Semantic updates, merges and physical deletion are not authorized by this portable skill. Preserve historical facts; route uncertain consolidation to the instance's approved review mechanism. Decay is numeric only, requires trustworthy recall telemetry, and never implies physical deletion or evidence reinforcement.

## Receipts and silence

Record run_id and per-operation before/after hashes, tool result, verification and recovery state. Count only verified after-states as successful. A successful run with no user action is silent. Failed or exceptional runs may send one concise alert containing verified counts and honest recovery status; do not include memory contents, identifiers, paths or action requests.

## References

- [Rulings template](references/rulings-template.md)
- [Watermark slimming SOP](references/watermark-slimming-sop.md)
- [Pending review SOP](references/pending-review-sop.md)
- [Judge calibration](references/judge-calibration.md)
