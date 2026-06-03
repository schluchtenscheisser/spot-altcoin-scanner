# Spot Altcoin Scanner

Spot Altcoin Scanner is a Python **bootstrap repository** for daily spot-market scan workflows and analysis artifacts.  
The repository is currently runnable with the existing legacy-compatible scanner pipeline, while the **Independence-Release** architecture in `docs/canonical/` is the target architecture for ongoing rebuild tickets.

## Repository status (important)
- **Current runnable state:** legacy-compatible scanner pipeline and tooling in this repository.
- **Target architecture:** Independence-Release contracts and structure under `docs/canonical/`.
- **Legacy runtime status:** usable for current runs, but treated as migration/reference baseline for the Independence-Release transition.

## Requirements
- Python 3.11+
- pip
- Optional (for `run_mode=standard`): CoinMarketCap API key in `CMC_API_KEY`

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

## Configuration
1. Open `config/config.yml` and adjust run settings (for example `general.run_mode`, budget, and filters).
2. Provide API credentials when needed:
   ```bash
   export CMC_API_KEY="<your-key>"
   ```
3. Keep deny/override files aligned with your run:
   - `config/denylist.yaml`
   - `config/unlock_overrides.yaml`
   - `config/mapping_overrides.json`

## Running the scanner
Run the pipeline from the repository root:

```bash
python -m scanner.main --mode standard
```

Other supported mode overrides:

```bash
python -m scanner.main --mode fast
python -m scanner.main --mode offline
python -m scanner.main --mode backtest
```

Notes:
- `--mode` overrides `general.run_mode` from `config/config.yml` for that invocation.
- `standard` mode requires `CMC_API_KEY` to be set.

## Outputs and reports
Typical run artifacts are written to:
- `reports/` (human/machine report outputs)
- `snapshots/` (history and runtime snapshots)
- `evaluation/` (exports, replay, calibration helper artifacts)

## Scheduling (optional)
You can schedule the scanner using cron or CI by calling the same CLI command (`python -m scanner.main --mode ...`) with the required environment variables and working directory.


## Running ad-hoc analysis scripts in GitHub Actions
Use the manual workflow `.github/workflows/run-analysis-script.yml` via `workflow_dispatch` with required input `script_path`.

Rules for `script_path`:
- must be a relative path
- must point to an existing `.py` file under `scripts/`
- empty values, absolute paths, traversal paths, non-`scripts/` paths, missing files, directories, and non-Python files are rejected

Analysis workflow outputs are uploaded as GitHub Actions artifacts only (no `git add`/`commit`/`push` writeback).

If an analysis script writes files, only these output roots are allowed for collection:
- `evaluation/exports/`
- `evaluation/calibration/`
- `artifacts/`
- `reports/aux/`

Some analysis scripts may only print stdout and produce no files; in that case artifact upload can warn about missing files while the run remains valid.

`reports/analysis/` is deprecated/not allowed for this workflow.


## Manual Independence smoke test workflow
Use `.github/workflows/independence-smoke-test.yml` via `workflow_dispatch` to run an end-to-end executability smoke check (Daily Runner -> Intraday Runner -> Evaluation Replay) against a fixed candidate list:
- `SOLUSDT`
- `AVAXUSDT`
- `LINKUSDT`
- `INJUSDT`
- `ARBUSDT`

Scope and guarantees:
- Manual trigger only (`workflow_dispatch`), no schedule/push trigger.
- Runtime outputs are isolated under `${{ runner.temp }}/ir-smoke-workdir`; the workflow verifies no generated run artifacts are written back to `${{ github.workspace }}`.
- Artifacts are uploaded from the temporary smoke workdir only; the workflow does not commit or push generated outputs.
- This smoke workflow validates stage execution and canonical artifact locations only (not business-logic quality assertions or calibration).

## Canonical docs and deeper architecture
**Documentation authority:** See [`docs/AUTHORITY.md`](docs/AUTHORITY.md) for the complete authority hierarchy and documentation taxonomy. When documents conflict, `docs/AUTHORITY.md` defines which source wins.

- Canonical entry point: `docs/canonical/INDEX.md`
- Authority and precedence: `docs/canonical/AUTHORITY.md`
- Runtime target model: `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- Migration framing: `docs/canonical/MIGRATION_NOTES.md`
