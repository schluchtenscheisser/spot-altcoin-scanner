# Decision Note: Legacy Pipeline Boundary Decisions after CODE-A2

## Metadata

- Decision note ID: 2026-06-07__legacy_pipeline_boundary_decision_note
- Related audit: CODE-A2 — `docs/audit/legacy_pipeline_boundary_review_v0.md`
- Related prerequisite audit: CODE-A1 — `docs/audit/active_code_path_inventory_v0.md`
- Status: Draft for repository inclusion
- Decision owner: Martin
- Scope: Boundary decisions for legacy-pipeline dependencies before DOC-D
- Language: English
- Intended repository path: `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`

---

## 1. Context

CODE-A1 identified that `scanner/pipeline/` is a mixed namespace:

- it is not the active Independence Daily/Intraday runtime architecture,
- parts of it are explicitly legacy-labeled or legacy-looking,
- some helpers remain reachable through active runtime, executable tools, tests, and compatibility paths.

CODE-A2 then reviewed four concrete boundary conflicts and turned them into decision-ready options.

This note records Martin’s decisions so that follow-up cleanup tickets and DOC-D current-state documentation can proceed without silently treating all of `scanner/pipeline/` as either active or dead.

---

## 2. Decision summary

| Conflict area | Decision |
|---|---|
| A — `scanner.execution.grading -> scanner.pipeline.liquidity` | `extract_active_utility` |
| B1 — `scanner.pipeline.global_ranking.compute_global_top20` | Legacy |
| B2 — `scanner.backtest.e2_model` | Legacy compatibility helper tied to legacy snapshot exporter |
| C — `scanner.tools.backfill_snapshots --mode full` | `keep_as_compatibility_only` |
| D — old mode names `standard`, `fast`, `offline`, `backtest` | `keep_as_compatibility_only` |

---

## 3. Decision A — extract active liquidity utility

### Area

```text
scanner/execution/grading.py
-> scanner.pipeline.liquidity.compute_tradeability_metrics
```

### Decision

```text
extract_active_utility
```

### Rationale

`compute_tradeability_metrics` is currently used by active execution grading. However, it lives under `scanner/pipeline/`, a namespace that is not the active Independence Daily/Intraday runtime architecture.

The function should therefore be treated as active utility code that is misplaced under a legacy-labeled namespace.

### Consequence

A follow-up cleanup ticket should extract the active tradeability/liquidity utility into an active module family, for example:

```text
scanner/execution/
scanner/execution/liquidity.py
scanner/execution/tradeability_metrics.py
```

The exact destination can be decided in the cleanup ticket.

### DOC-D impact

DOC-D may document active execution/tradeability behavior, but must not imply that the whole `scanner/pipeline/` namespace is active current runtime architecture.

Until extraction is implemented, DOC-D should mention the temporary boundary exception explicitly.

---

## 4. Decision B1 — classify `compute_global_top20` as legacy

### Area

```text
scanner/tools/export_evaluation_dataset.py
-> scanner.pipeline.global_ranking.compute_global_top20
```

### Decision

```text
Legacy
```

### Rationale

`compute_global_top20` belongs to the old snapshot/global-ranking evaluation path. It should not be treated as active current Independence evaluation architecture and must not be used as evidence for current Daily/Intraday ranking behavior.

### Consequence

Follow-up work should either:

- keep it only as part of a legacy snapshot exporter path, or
- deprecate/remove it together with the old exporter if no historical reproduction requirement remains.

### DOC-D impact

DOC-D must not document `compute_global_top20` as current scanner ranking logic.

If the old exporter is mentioned at all, it should be framed as legacy or compatibility tooling, not active current evaluation architecture.

---

## 5. Decision B2 — classify `scanner.backtest.e2_model` as legacy compatibility helper

### Area

```text
scanner/tools/export_evaluation_dataset.py
-> scanner.backtest.e2_model
```

### Decision

```text
Legacy compatibility helper tied to legacy snapshot exporter
```

### Rationale

The evidence indicates that `scanner.backtest.e2_model` is used by the old `export_evaluation_dataset.py` path and has direct tests, but no independent active caller outside that legacy snapshot exporter path was identified.

Because `export_evaluation_dataset.py` also depends on legacy `compute_global_top20`, `e2_model` should not be canonized as active current Independence evaluation infrastructure.

However, while `export_evaluation_dataset.py` still imports it and direct tests exist, it should not be described too narrowly as “test-only” without also noting the remaining executable legacy exporter dependency.

### Preferred classification wording

```text
scanner.backtest.e2_model =
legacy compatibility helper tied to the legacy snapshot evaluation/export path;
not active current Independence evaluation infrastructure;
direct tests exist;
may become legacy_residue_test_only once export_evaluation_dataset.py is deprecated,
removed, or explicitly classified as legacy-only.
```

### Consequence

Follow-up work should decide the fate of the legacy snapshot exporter as a unit, including:

- `scanner/tools/export_evaluation_dataset.py`
- `scanner.pipeline.global_ranking.compute_global_top20`
- `scanner.backtest.e2_model`
- direct tests around this legacy export path

### DOC-D impact

DOC-D may document the current `scanner/evaluation/*` replay/evaluation infrastructure, but should not use `scanner.backtest.e2_model` as evidence for current active Independence evaluation architecture.

---

## 6. Decision C — keep `backfill_snapshots.py --mode full` as compatibility-only

### Area

```text
scanner/tools/backfill_snapshots.py --mode full
-> _run_full_mode
-> scanner.pipeline.run_pipeline
-> scanner.pipeline.scoring/*
```

### Decision

```text
keep_as_compatibility_only
```

### Rationale

`--mode full` is executable and tested, but no active GitHub Actions workflow or current operational process was identified that calls it.

The default path is `--mode minimal`. Full mode reaches the old legacy pipeline orchestrator and legacy scoring modules. This makes it a compatibility or historical-reproduction path, not a future current v2.1 mode and not active Daily/Intraday runtime architecture.

### Consequence

No immediate cleanup is required by this decision note.

A future cleanup ticket may later decide whether to:

- leave full mode as compatibility-only,
- add stronger warnings or guards,
- require an explicit legacy opt-in flag,
- or deprecate/remove full mode if no historical reproduction requirement remains.

Those are cleanup-ticket decisions, not part of this decision note.

### DOC-D impact

DOC-D may document current backfill behavior around the default/minimal path.

If `--mode full` is mentioned, it should be clearly labeled as:

```text
legacy-pipeline compatibility / historical reconstruction path;
not current Independence v2.1 runtime architecture.
```

---

## 7. Decision D — keep old mode names as compatibility-only aliases

### Area

```text
scanner/main.py
modes: standard, fast, offline, backtest
```

### Decision

```text
keep_as_compatibility_only
```

### Rationale

The old mode names remain accepted by active dispatch, but they do not represent distinct current runtime architectures. They route into the Daily runner path rather than reviving old scanner behavior.

Therefore, they should be treated as accepted compatibility aliases, not as canonical current modes.

### Consequence

A future follow-up ticket should clarify or normalize the mode model, for example:

- canonical mode names,
- accepted compatibility aliases,
- config validation consistency,
- whether aliases should remain indefinitely or be deprecated later.

### DOC-D impact

DOC-D may document canonical runtime behavior as Daily and Intraday.

Old mode names may be listed only as compatibility aliases / legacy accepted values, not as separate current scanner modes.

---

## 8. Follow-up ticket map

| Follow-up | Purpose | Priority | Notes |
|---|---|---:|---|
| CODE-FU-A | Extract active liquidity/tradeability utility from `scanner.pipeline.liquidity` into active execution/utility namespace. | P1 | Needed to reduce active-runtime dependency on legacy namespace. |
| CODE-FU-B | Classify and possibly deprecate the legacy snapshot evaluation/export path as a unit. | P2 | Covers `export_evaluation_dataset.py`, `compute_global_top20`, and `e2_model`. |
| CODE-FU-C | Optionally guard, label, or deprecate `backfill_snapshots.py --mode full`. | P2/P3 | Not urgent if clearly treated as compatibility-only. |
| CODE-FU-D | Define canonical mode names and compatibility alias policy. | P2 | Supports clean DOC-D runtime wording and future config consistency. |
| DOC-D | Continue current-state documentation with boundary caveats. | P1 | May proceed partially after this decision note. |

---

## 9. DOC-D guidance after these decisions

DOC-D may proceed with the following constraints:

| DOC-D area | Status | Guidance |
|---|---|---|
| Architecture overview | Proceed with caveat | State that `scanner/pipeline/` is not current runtime architecture, with listed exceptions/compatibility paths. |
| Runtime entry points | Proceed | Document Daily and Intraday runners as current runtime paths. |
| Daily runner | Proceed | Do not use legacy pipeline scoring/ranking as Daily behavior. |
| Intraday runner | Proceed | Document `intraday_promotion` as the Intraday route. |
| Execution/tradeability | Proceed with caveat | Mention temporary extraction decision for `pipeline.liquidity`. |
| Evaluation/replay | Proceed with caveat | Keep old snapshot exporter separate from current evaluation infrastructure. |
| Analysis/backfill tools | Proceed with caveat | Mark `--mode full` as compatibility-only. |
| Output/report paths | Proceed | Use current report/snapshot paths, not legacy pipeline output conventions. |
| Legacy/reference-only section | Proceed | Include legacy exporter, legacy global ranking, e2 compatibility helper, and full-mode backfill under explicit boundary wording. |

---

## 10. Final decision checklist

- [x] A — `scanner.pipeline.liquidity` will be extracted from the legacy namespace as active utility code.
- [x] B1 — `scanner.pipeline.global_ranking.compute_global_top20` is classified as legacy.
- [x] B2 — `scanner.backtest.e2_model` is classified as a legacy compatibility helper tied to the legacy snapshot exporter.
- [x] C — `backfill_snapshots.py --mode full` remains compatibility-only for now.
- [x] D — `standard`, `fast`, `offline`, and `backtest` remain compatibility-only aliases for now.
- [x] DOC-D may proceed partially with the caveats listed above.
- [x] Cleanup actions require separate follow-up tickets.
- [x] This decision note does not change runtime behavior.

---

## 11. No implementation action taken

This decision note records architecture decisions only.

- [x] No scanner code changed.
- [x] No tests changed.
- [x] No schemas changed.
- [x] No workflows changed.
- [x] No runtime behavior changed.
- [x] No files moved.
- [x] No files deleted.
- [x] No cleanup implemented.
- [x] No current-state canonical documentation updated.
