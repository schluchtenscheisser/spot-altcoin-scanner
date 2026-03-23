# Snapshots — Independence-Release Snapshot Architecture (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_SNAPSHOTS
status: canonical
snapshot_root: snapshots
history_format: parquet
```

## Snapshot classes
The Independence-Release bootstrap reserves four canonical snapshot classes that are referenced as **A / B / C / D** in the authoritative planning material. Their detailed payload definitions remain deferred to later tickets.

- **Class A**: reserved snapshot class from Gesamtkonzept §6.
- **Class B**: reserved snapshot class from Gesamtkonzept §6.
- **Class C**: reserved snapshot class from Gesamtkonzept §6.
- **Class D**: reserved snapshot class from Gesamtkonzept §6.

## Parquet partitioning (Festlegung 1)
Parquet is the canonical history format for snapshot/history exports. The authoritative partitioning rule referenced by the bootstrap ticket is acknowledged here as binding for future implementation; this ticket intentionally does not invent additional partition keys beyond reserving the history path and Parquet requirement.

## Directory structure
```text
snapshots/
├── history/
└── runs/
```

## Bootstrap rule
Detailed class payloads, filenames, and partition fields must be introduced only when the corresponding authoritative material is available in-repo or in later implementation tickets.
