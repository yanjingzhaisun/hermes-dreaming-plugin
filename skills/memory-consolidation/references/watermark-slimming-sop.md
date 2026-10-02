# Watermark slimming SOP (dreaming v2)

Each run reads positive integer limits from `memory.memory_char_limit` and `memory.user_char_limit`, then measures MEMORY.md and USER.md independently using UTF-8 character counts. Routine slimming begins at `chars >= ceil(limit*0.85)`. An explicit correction is handled independently of this gate.

## Permissions and invariants

Non-protected USER content may be maintained only when the target deployment explicitly permits it. Identity and protected content are deferred from unattended writes. The protection registry is authoritative; preserve every registered block byte-for-byte and in relative order. The nightly process must not modify or refresh the registry. Any shadow/advice mechanism is not write authorization.

## Execution order

1. Compress wording while preserving negation, dates, conditions, identifiers, source atoms and scope.
2. Merge same-topic entries only after checking every information atom; preserve relative ordering.
3. Move content only after verifying the destination. Recall facts require a live, readable and retrievable fact; operating rules require an existing in-scope skill. Back up and verify destination before removing source.
4. If still above threshold with no safe candidate, raise only the corresponding limit using the deployment formula: `new_limit=max(old_limit, ceil(chars/0.80/100)*100)`. Patch one unambiguous target key and verify the parsed configuration and resulting character count.

Before every write, back up the target and require a unique exact-match patch with an unchanged source hash. Afterward measure both files and run `scripts/dream_protected_check.py`; confirm every EXPECTED entry reports OK. On failure, uncertain coverage or concurrent change, preserve source bytes and record internal deferred.

Configuration changes must preserve all unrelated keys and bytes. No gateway restart is implied.
