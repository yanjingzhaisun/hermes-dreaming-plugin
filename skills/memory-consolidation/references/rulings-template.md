# Rulings registry template

Use this file as a structural template. Replace every sample with target-instance reviewed policy. Do not copy personal memory text or hashes from another deployment.

## Entry format

```text
### R-<DOMAIN>-<NNN>
- effective_at: YYYY-MM-DD (timezone)
- status: active | superseded | retired
- scope: <file, workflow, or action class>
- ruling: <short, testable boundary>
- evidence: <reviewed source or change record>
- boundary: <what the ruling does not authorize>
```

## Generic examples

### R-MEM-001
- effective_at: 2026-01-15 (UTC)
- status: active
- scope: protected memory blocks
- ruling: Preserve the complete registered block bytes and their relative order during automated edits.
- evidence: Reviewed protection registry for the target instance.
- boundary: This entry does not permit the nightly process to edit or refresh the registry.

### R-DREAM-001
- effective_at: 2026-01-15 (UTC)
- status: active
- scope: correction reconciliation
- ruling: Apply recency-wins only when source authorship, subject, topic, scope and ordering are independently verified.
- evidence: Approved correction-handling policy.
- boundary: Ambiguous, identity-class or safety-boundary changes are deferred to a user-present session.

## Update discipline

Append a new numbered ruling when policy changes. Set the previous entry to superseded and identify the effective time of the replacement. Keep the scope narrow and state negative boundaries explicitly. Never use a nightly run to revise rulings or protection hashes.
