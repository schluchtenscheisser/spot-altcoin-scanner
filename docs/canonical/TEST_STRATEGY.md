# Test Strategy — Independence-Release Bootstrap Validation (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_TEST_STRATEGY
status: canonical
bootstrap_level: structure_and_contracts
```

## Golden strategy (Gesamtkonzept §16, types 1–4)
The Independence-Release test strategy reserves four golden-test types referenced by the authoritative planning material. This bootstrap does not invent payload schemas for them, but it establishes that future implementation tickets must map their tests into a deterministic golden strategy.

- **Type 1**: reserved golden-test category from Gesamtkonzept §16.
- **Type 2**: reserved golden-test category from Gesamtkonzept §16.
- **Type 3**: reserved golden-test category from Gesamtkonzept §16.
- **Type 4**: reserved golden-test category from Gesamtkonzept §16.

## Validation strategy (Gesamtkonzept §17)
Future Independence-Release work must validate:
- canonical documentation and implementation alignment
- deterministic repository/path contracts
- persistence/output structure contracts
- deferred business logic only after its canonical spec exists

## Bootstrap validation in this ticket
This ticket validates the existence of required canonical files and target directories without implementing Independence-Release business logic.

## AI Sparring runtime test strategy

For `tools/ai_sparring/`, canonical tests must cover:
- preflight validation atomicity (no partial writes on preflight failure),
- deterministic context ordering and deduplication,
- provider contract normalization (`provider`, `model`, `text`, `attempts_used`, `request_id`),
- retry behavior (only transient failures retried with fixed budget),
- deterministic round protocol shape (`draft/review/revision` per round),
- deterministic mode-to-prompt-id resolution (`resolved_prompts` for drafter/reviewer),
- round input visibility contract (`draft_(r+1)` sees only prior `review_r` and `revision_r` from round `r`),
- runtime failure status separation (`failed_runtime` vs `failed_partial`),
- workflow/tool dependency coverage for real-provider runtime execution,
- fake-provider compatibility.

No tests in this slice may depend on live network calls.
