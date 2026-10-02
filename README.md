# Holographic Dreaming Plugin

A portable nightly memory-consolidation pipeline ("dreaming") for [Hermes Agent](https://github.com/NousResearch/hermes-agent). While you sleep, it consolidates `MEMORY.md`, `USER.md` and the holographic fact_store: it captures session facts and user corrections, reconciles what is provably safe to reconcile, slims memory files against their watermarks, and reviews staged background rewrites — fully unattended, fail-closed, and silent on success.

中文：[README.zh-CN.md](README.zh-CN.md) ｜ 日本語：[README.ja.md](README.ja.md)

## Architecture

```text
Hermes cron (local delivery, pinned low-cost model)
  → fact_extract_sweep (correction capture + ordinary sweep)
  → correction reconciliation (applied only with structural proof, else internal deferred)
  → pending staged-write review (judge each, apply or discard)
  → MEMORY / USER watermark evaluation (routine slimming at threshold)
  → protected-set verification, per-operation receipts
```

Judgment stays in the model layer; scripts do deterministic verification, execution and receipts. A successful run that needs no owner action emits zero stdout and zero push notifications.

## Five-step quick start

1. Prepare a Hermes instance with the holographic memory provider, the memory tool and cron enabled. The runtime Python must be able to import `tools.memory_tool` and `tools.write_approval`.
2. Set `HERMES_HOME`. Put `scripts/` under `$HERMES_HOME/scripts/` and the skill under `$HERMES_HOME/skills/<category>/memory-consolidation/`.
3. Initialize the protected-set EXPECTED for the target instance. Verify the frozen blocks before enabling any nightly write — an empty EXPECTED passing the check does **not** mean protection exists.
4. Configure permissions and watermark limits per [docs/porting.md](docs/porting.md), then create a daily cron job: `deliver=local`, pinned low-cost model (e.g. a DeepSeek flash-tier model).
5. Dry-run the first night in an isolated copy: verify per-operation receipt JSONL and the protected-set check, confirm zero pushes, then enable production writes.

## Porting highlights

Hermes deployments differ in tool APIs, approval gates, fact_store schema, session database and cron fields. Map each one; never reuse another instance's protected content. Full checklist in [docs/porting.md](docs/porting.md); design constraints in [docs/design.md](docs/design.md).

The three that bite most often:

1. Scripts must run under the Hermes runtime Python (they import `tools.memory_tool`), not the system Python.
2. `memory.write_approval` only governs foreground writes — the background destructive-staging gate lives in runtime code and has no config switch. The bundled `memory_pending_review.py` brings that approval into the nightly flow.
3. `fact_extract_sweep.py` expects an external `session_fact_extract.py` (the LLM extraction chain). That is each deployment's own model choice and is intentionally not shipped.

## Layout

- [cron/nightly-prompt.md](cron/nightly-prompt.md): parameterized nightly job prompt template.
- [skills/memory-consolidation/SKILL.md](skills/memory-consolidation/SKILL.md): operating rules and decision boundaries.
- [skills/memory-consolidation/references/](skills/memory-consolidation/references/): rulings template, watermark slimming SOP, pending-review SOP, judge calibration method.
- [scripts/](scripts/): session fact sweep, shared state, protected-set check, staged-write reviewer.

## License

MIT — see [LICENSE](LICENSE).
