# Migration Notes — Legacy to Independence-Release Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_MIGRATION_NOTES
status: canonical
```

## Purpose
This bootstrap document classifies existing repository material using the required three-way migration view from Gesamtkonzept §3. It does not migrate business logic; it only classifies how current material should be treated.

## Directly reusable
- `scanner/clients/**` technical client code, subject to later target-architecture integration decisions.
- `scanner/utils/**` generic utility code that is not tied to legacy scoring authority.
- `scripts/**` and similar technical helpers that support repository operations.
- Technical fetch, mapping, and liquidity helper code that can be reused without importing legacy business rules as authority.

## Structural template only
- Existing repository layout patterns that are useful as implementation scaffolding but not as canonical design truth.
- Legacy pipeline/orchestration code that may inform future module boundaries without remaining the active target path.
- Existing report/output plumbing patterns that can guide future implementation after canonical Independence-Release contracts are defined.

## Not carried forward as primary architecture
- Legacy scoring, ranking, and decision architecture as a source of canonical truth.
- Legacy business documentation outside the new canonical Independence-Release set.
- Any assumption that `scanner/pipeline/**` remains the implied target implementation path for new architecture work.
