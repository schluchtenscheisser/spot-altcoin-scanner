from __future__ import annotations

import ast
from pathlib import Path

LEGACY_EXPORTER_IMPORTS = {
    "scanner.tools.export_evaluation_dataset",
    "scanner.pipeline.global_ranking",
    "scanner.backtest.e2_model",
}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def test_daily_intraday_do_not_import_legacy_snapshot_exporter_cluster() -> None:
    runner_paths = [Path("scanner/runners/daily.py"), Path("scanner/runners/intraday.py")]

    for path in runner_paths:
        imports = _imported_modules(path)
        assert imports.isdisjoint(LEGACY_EXPORTER_IMPORTS), path
