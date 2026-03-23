# Reports — Independence-Release Reports Architecture (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_REPORTS
status: canonical
report_root: reports
```

## Directory structure
```text
reports/
├── index/
├── daily/
├── runs/
└── aux/
```

## Verbindliche Dateitypen
The Independence-Release bootstrap reserves the canonical report surface for machine-readable and human-readable report artifacts. At minimum, future implementation tickets may emit:
- structured data exports for deterministic downstream consumption
- human-readable report views for operator review
- run-oriented metadata or index artifacts aligned with the directory roles above

## Directory roles
- `reports/index/`: stable index-style artifacts that point to available reports or latest states.
- `reports/daily/`: daily discovery scan outputs.
- `reports/runs/`: run-specific report bundles and per-run material.
- `reports/aux/`: auxiliary report artifacts that support the primary report set without redefining canonical truth.

## Bootstrap rule
This ticket establishes the report architecture and required directories only. File naming, schemas, and rendering rules must be defined in later canonical tickets.
