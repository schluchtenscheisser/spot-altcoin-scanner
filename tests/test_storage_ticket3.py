from scanner.storage import init_db


def test_schema_includes_ticket3_tables(tmp_path):
    db = init_db(tmp_path / "t3.db")
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "symbol_metadata" in tables
        assert "symbol_run_decisions" in tables
        cols = {r[1] for r in db.execute("PRAGMA table_info(run_metadata)").fetchall()}
        assert "eligible_pre_1d_count" in cols
        assert "selected_for_4h_count" in cols
    finally:
        db.close()
