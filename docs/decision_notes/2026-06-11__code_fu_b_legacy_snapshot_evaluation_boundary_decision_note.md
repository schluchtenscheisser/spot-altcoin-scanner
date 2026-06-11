# CODE-FU-B Legacy Snapshot Evaluation Boundary Decision

## Decision

Selected outcome: `own_as_standalone_legacy_tool`

## Scope

This decision covers the legacy snapshot evaluation export cluster:

- `scanner/tools/export_evaluation_dataset.py`
- `scanner.pipeline.global_ranking.compute_global_top20`
- `scanner.backtest.e2_model`

It does not migrate fields into `scanner/evaluation/*` and does not change Daily/Intraday scanner runtime behavior.

## Rationale

- The exporter remains executable and has focused regression coverage for JSONL export behavior, label calculation, global Top-20 rank compatibility, and missing-snapshot handling.
- `compute_global_top20` and `scanner.backtest.e2_model` are still intentional dependencies of that exporter, but current Daily/Intraday runners do not import the exporter cluster.
- Absorbing this path into active `scanner/evaluation/*` would conflate legacy snapshot JSONL compatibility semantics with the current replay/forward-return evaluation infrastructure and would require broader schema and documentation work than CODE-FU-B allows.

## Rejected alternatives

- `deprecate`: rejected because the tool is still executable and covered by tests; removing or warning on it would reduce compatibility without evidence that historical snapshot export consumers are gone.
- `absorb_into_active_evaluation`: rejected because active `scanner/evaluation/*` already owns replay/forward-return evaluation outputs, while this exporter depends on legacy snapshot/global-ranking/E2 semantics and would require a broader migration to become an active evaluation contract.

## Impact on future Evaluation/T30 documentation

Future Evaluation/T30 documentation may reference this cluster only as standalone legacy snapshot evaluation export tooling and compatibility evidence. It must not treat the cluster as active `scanner/evaluation/*` infrastructure, active Daily/Intraday ranking, or the source of current Evaluation/T30 output contracts.

## Follow-ups

- If historical snapshot-export compatibility is no longer needed, open a dedicated deprecation/removal ticket with consumer evidence.
- If any legacy snapshot export fields need to become active Evaluation/T30 contracts, open a dedicated absorption/migration ticket for `scanner/evaluation/*` with schema and report documentation updates.
