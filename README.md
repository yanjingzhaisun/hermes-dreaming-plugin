# Hermes Memory Stack

Two portable, deploy-anywhere halves of a Hermes Agent memory system: a **fact-store backend** (the `holographic-plus` memory provider) and a **nightly consolidation pipeline** ("dreaming"). Both are extracted from a production single-user deployment and parameterized for another instance.

中文：[README.zh-CN.md](README.zh-CN.md) ｜ 日本語：[README.ja.md](README.ja.md)

## What's in the box

| Half | What it is | Where |
| --- | --- | --- |
| **fact store** | SQLite-backed structured memory: facts, entities, trust scoring, HRR compositional retrieval, optional semantic (embedding) retrieval. Exposes the `fact_store` / `fact_feedback` tools and injects retrieved facts per turn. | [`plugin/holographic-plus/`](plugin/holographic-plus/) + [docs/factstore.md](docs/factstore.md) |
| **dreaming** | Unattended nightly run: capture session facts and user corrections, reconcile only what is provably safe, slim `MEMORY.md` / `USER.md` against their watermarks, review staged background rewrites. Fail-closed, silent on success. | [`cron/`](cron/), [`skills/`](skills/), [`scripts/`](scripts/) + [docs/design.md](docs/design.md) |

They are independent: the store works without the nightly job, and the nightly job's fact-store steps need a store. Hermes already ships a bundled `holographic` provider using the same SQLite fact store. The separately maintained fork adds semantic retrieval, entity-resolution safeguards and CJK entity extraction ([docs/holographic-plus.md](docs/holographic-plus.md)).

## Architecture

```text
                    ┌─ fact_store(add)         ─┐
writes ─────────────┼─ memory-tool mirror       ─┼─→ memory_store.db   ── read by ──→  system-prompt status block
                    ├─ session-finalize hook   ─┤     facts, entities,                per-message prefetch
                    └─ nightly dreaming        ─┘     FTS5, HRR banks,                 search / probe / related /
                                                      embedding sidecar                 reason / contradict
```

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

`plugin/holographic-plus/` is a pinned Git submodule of the independent [holographic-plus repository](http://192.168.71.67:4100/zijianzhou/holographic-plus). Initialize the recorded revision before installing:

```bash
git submodule update --init --recursive
```

1. Prepare a Hermes instance with a holographic memory provider (the bundled `holographic`, or the fork in this repo), the memory tool and cron enabled. The runtime Python must be able to import `tools.memory_tool` and `tools.write_approval`.
2. Set `HERMES_HOME`. Put `scripts/` under `$HERMES_HOME/scripts/`, the skill under `$HERMES_HOME/skills/<category>/memory-consolidation/`, and — if you use the fork — export the pinned plugin files to `$HERMES_HOME/plugins/holographic-plus/` using the [installation instructions](docs/holographic-plus.md#5-安装与回滚). Review the plugin revision's database migration requirements before activation.
3. Initialize the protected-set EXPECTED for the target instance. Verify the frozen blocks before enabling any nightly write — an empty EXPECTED passing the check does **not** mean protection exists.
4. Configure permissions and watermark limits per [docs/porting.md](docs/porting.md), then create a daily cron job: `deliver=local`, pinned low-cost model (e.g. a DeepSeek flash-tier model).
5. Dry-run the first night in an isolated copy: verify per-operation receipt JSONL and the protected-set check, confirm zero pushes, then enable production writes.

## Porting highlights

Hermes deployments differ in tool APIs, approval gates, fact_store schema, session database and cron fields. Map each one; never reuse another instance's protected content. Full checklist in [docs/porting.md](docs/porting.md); design constraints in [docs/design.md](docs/design.md).

The four that bite most often:

1. Scripts must run under the Hermes runtime Python (they import `tools.memory_tool` and the store), not the system Python.
2. `memory.write_approval` only governs foreground writes — the background destructive-staging gate lives in runtime code and has no config switch. The bundled `memory_pending_review.py` brings that approval into the nightly flow.
3. `fact_extract_sweep.py` expects an external `session_fact_extract.py` (the LLM extraction chain). That is each deployment's own model choice and is intentionally not shipped — the sweep degrades to a no-op without it.
4. Anything that writes `hrr_vector` must read the HRR dimension from **one** source of truth (the plugin config). Bypass scripts that hardcode their own dimension corrupt the store: inserts get rejected as dimension-mismatched, or foreign-shape blobs land silently.

## Layout

- [plugin/holographic-plus/](plugin/holographic-plus/): the pinned submodule of the independent memory-provider repository (fork of the bundled `holographic` plugin).
- [docs/factstore.md](docs/factstore.md): fact-store data model, read/write paths, scoring, HRR, trust.
- [docs/holographic-plus.md](docs/holographic-plus.md): what the fork adds, config keys, install/rollback, HRR dimension rules.
- [cron/nightly-prompt.md](cron/nightly-prompt.md): parameterized nightly job prompt template.
- [skills/memory-consolidation/SKILL.md](skills/memory-consolidation/SKILL.md): operating rules and decision boundaries.
- [skills/memory-consolidation/references/](skills/memory-consolidation/references/): rulings template, watermark slimming SOP, pending-review SOP, judge calibration method.
- [scripts/](scripts/): session fact sweep, shared state, protected-set check, staged-write reviewer.

## License

MIT — see [LICENSE](LICENSE). The plugin directory is derived from Hermes Agent's bundled `holographic` provider (MIT, © 2025 Nous Research; original plugin by dusterbloom) — see [plugin/holographic-plus/NOTICE](plugin/holographic-plus/NOTICE).
