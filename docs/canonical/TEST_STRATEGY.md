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
