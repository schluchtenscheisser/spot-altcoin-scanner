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

## Canonical docs and deeper architecture
- Canonical entry point: `docs/canonical/INDEX.md`
- Authority and precedence: `docs/canonical/AUTHORITY.md`
- Runtime target model: `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- Migration framing: `docs/canonical/MIGRATION_NOTES.md`
