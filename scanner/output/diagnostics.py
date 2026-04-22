from __future__ import annotations

from pathlib import Path
import gzip
import json
import os
import tempfile
from typing import Iterable, Mapping, Any

from .schema import validate_diagnostics_record


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def serialize_diagnostics_jsonl_lines(records: Iterable[Mapping[str, Any]]) -> list[str]:
    lines: list[str] = []
    for record in records:
        validated = validate_diagnostics_record(record)
        lines.append(json.dumps(validated, sort_keys=True, separators=(",", ":")))
    return lines


def write_symbol_diagnostics_jsonl_gz(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    payload = "\n".join(serialize_diagnostics_jsonl_lines(records)).encode("utf-8")
    gz_bytes = gzip.compress(payload)
    _atomic_write_bytes(path, gz_bytes)
