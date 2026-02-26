from scanner.pipeline.output import ReportGenerator


def test_output_schema_version_is_expected() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 1}})
    report = generator.generate_json_report([], [], [], [], "2026-02-26")

    assert report["schema_version"] == "v1.9"
    assert report["meta"]["version"] == "1.9"
