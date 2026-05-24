# BACKTEST-CHUNK-2: GitHub Actions Workflow for Chunked Historical Replay

## Metadata

- Ticket ID: BACKTEST-CHUNK-2
- Title: GitHub Actions Workflow — Automated Chunked Historical Signal-Quality Replay
- Status: Ready for implementation
- Priority: P1
- Language: Implementation and code artifacts in English

---

## Context and motivation

BACKTEST-CHUNK-1 added chunk-capable execution to the replay runner. This ticket
adds the GitHub Actions workflow that orchestrates a full chunked replay run
automatically, using the frozen Pre-1 history dataset from a GitHub Release Asset.

Goals:
- One `workflow_dispatch` trigger runs the complete replay without manual intervention
- Monthly chunks are derived automatically from the scenario YAML evaluation window
- All chunks share one `replay_id` and write under one canonical run directory
- State is handed off between chunks via `state_final.sqlite`
- Outputs are uploaded as a GitHub Actions Artifact at workflow end, including partial outputs on failure
- A debug `single_chunk` mode allows targeted re-runs and diagnostics

---

## Authoritative references

1. BACKTEST-CHUNK-1 ticket:
   `docs/legacy/tickets/2026-05-23__BACKTEST-CHUNK-1__chunk_capable_replay_runner_v3.md`
2. Approved scenario YAML:
   `configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml`
3. GitHub Release Asset:
   Tag: `history-pre1-2026-05-20`
   Asset: `pre1_history_2026-05-20.tar.gz`
   SHA256: `74f3a6c90d84b9f812320ac9a4f8653b605e190fd6d8aa9655625723333a4bc7`
4. Existing workflow pattern:
   `.github/workflows/run-artifact-download-script.yml`

---

## Workflow file

Create: `.github/workflows/run-historical-replay.yml`

---

## Workflow inputs (`workflow_dispatch`)

```yaml
inputs:
  scenario_path:
    description: "Path to scenario YAML"
    required: false
    default: "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml"
    type: string

  history_release_tag:
    description: "GitHub Release tag for Pre-1 history asset"
    required: false
    default: "history-pre1-2026-05-20"
    type: string

  history_asset_name:
    description: "Asset filename within the release"
    required: false
    default: "pre1_history_2026-05-20.tar.gz"
    type: string

  history_asset_sha256:
    description: "Expected SHA256 of the history asset"
    required: false
    default: "74f3a6c90d84b9f812320ac9a4f8653b605e190fd6d8aa9655625723333a4bc7"
    type: string

  run_mode:
    description: "full_chunked = all monthly chunks; single_chunk = debug mode"
    required: false
    default: "full_chunked"
    type: choice
    options:
      - full_chunked
      - single_chunk

  chunk_start:
    description: "single_chunk mode only: chunk start date YYYY-MM-DD"
    required: false
    default: ""
    type: string

  chunk_end:
    description: "single_chunk mode only: chunk end date YYYY-MM-DD"
    required: false
    default: ""
    type: string

  resume_from_artifact:
    description: "single_chunk mode only: artifact name containing state_final.sqlite to resume from"
    required: false
    default: ""
    type: string

  replay_id:
    description: "Optional: reuse existing replay_id (for single_chunk continuation)"
    required: false
    default: ""
    type: string
```

---

## Permissions

```yaml
permissions:
  contents: read
```

The workflow only reads release assets and the repository. It does not commit.

---

## Job structure

One job: `replay`

```yaml
jobs:
  replay:
    runs-on: ubuntu-latest
    timeout-minutes: 350
```

---

## Step sequence

### Step 1 — Checkout

```yaml
- uses: actions/checkout@v4
```

### Step 2 — Set up Python

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

### Step 3 — Install dependencies

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
```

### Step 4 — Download and verify Pre-1 history asset

```yaml
- name: Download Pre-1 history asset
  run: |
    gh release download ${{ inputs.history_release_tag }} \
      --pattern "${{ inputs.history_asset_name }}" \
      --output "${{ inputs.history_asset_name }}"
    gh release download ${{ inputs.history_release_tag }} \
      --pattern "${{ inputs.history_asset_name }}.sha256" \
      --output "${{ inputs.history_asset_name }}.sha256"
  env:
    GH_TOKEN: ${{ github.token }}

- name: Verify SHA256
  run: |
    sha256sum --check "${{ inputs.history_asset_name }}.sha256"
    echo "SHA256 verified."

- name: Extract history dataset
  run: |
    tar -xzf "${{ inputs.history_asset_name }}"
    echo "History extracted."
    test -d snapshots/history/ohlcv || (echo "ERROR: snapshots/history/ohlcv not found after extraction" && exit 1)
    test -f snapshots/history/manifests/history_manifest.json || (echo "ERROR: history_manifest.json not found" && exit 1)
    test -f snapshots/history/manifests/universe_manifest.json || (echo "ERROR: universe_manifest.json not found" && exit 1)
    test -f snapshots/history/manifests/symbol_completeness.json || (echo "ERROR: symbol_completeness.json not found" && exit 1)
    test -f snapshots/history/regime_labels/regime_labels_btc_weekly_30d_return_vol_v1.json || (echo "ERROR: regime_labels not found" && exit 1)
    ls -lh snapshots/history/ohlcv/ | head -5
    echo "Post-extraction validation passed."
```

SHA256 is verified against the `.sha256` release asset file. Both the history asset
and its `.sha256` file are downloaded under their original names to ensure the
checksum file references the correct filename. The `history_asset_sha256` workflow
input is kept as documentation only and is not used for verification.

### Step 5 — Validate scenario

```yaml
- name: Validate scenario
  run: |
    python scanner/tools/run_historical_daily_replay.py \
      --scenario "${{ inputs.scenario_path }}" \
      --dry-run-validate-scenario
```

### Step 6 — Generate replay_id and chunk plan

```yaml
- name: Generate replay_id and chunk plan
  id: plan
  run: |
    python scripts/generate_replay_chunk_plan.py \
      --scenario "${{ inputs.scenario_path }}" \
      --run-mode "${{ inputs.run_mode }}" \
      --chunk-start "${{ inputs.chunk_start }}" \
      --chunk-end "${{ inputs.chunk_end }}" \
      --resume-from-artifact "${{ inputs.resume_from_artifact }}" \
      --replay-id "${{ inputs.replay_id }}" \
      --output-plan chunk_plan.json
    cat chunk_plan.json
    REPLAY_ID=$(python - <<'PY'
import json
with open("chunk_plan.json", "r", encoding="utf-8") as f:
    print(json.load(f)["replay_id"])
PY
)
    echo "replay_id=$REPLAY_ID" >> "$GITHUB_OUTPUT"
```

The workflow step reads `replay_id` from `chunk_plan.json` using a Python heredoc to
avoid shell quoting issues. The helper script must not write to `$GITHUB_OUTPUT`
itself — GitHub Actions context is the workflow's responsibility.

### Step 7 — Download resume state artifact (single_chunk with resume only)

```yaml
- name: Download resume state artifact
  if: inputs.run_mode == 'single_chunk' && inputs.resume_from_artifact != ''
  uses: actions/download-artifact@v4
  with:
    name: ${{ inputs.resume_from_artifact }}
    path: resume_state/
```

### Step 8 — Run chunks sequentially

```yaml
- name: Run all chunks
  run: |
    mkdir -p resume_state
    python scripts/run_replay_chunks.py \
      --scenario "${{ inputs.scenario_path }}" \
      --chunk-plan chunk_plan.json \
      --output-root evaluation/replay \
      --resume-state-dir resume_state/
```

`mkdir -p resume_state` ensures the directory exists even when no resume artifact
was downloaded. `run_replay_chunks.py` must silently ignore an empty
`--resume-state-dir` for `full_chunked` mode and for the first chunk of
`single_chunk` mode when no resume is needed.

### Step 9 — Upload replay outputs

`run_replay_chunks.py` does not upload artifacts. Artifact upload is handled
exclusively by the workflow using `actions/upload-artifact` with `if: always()`,
so outputs are preserved even on partial failure.

```yaml
- name: Upload replay outputs
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: replay-outputs-${{ steps.plan.outputs.replay_id }}
    path: |
      evaluation/replay/runs/
    retention-days: 90
    if-no-files-found: warn
```

Per-chunk artifact uploads are out of scope for BACKTEST-CHUNK-2.

---

## New helper scripts

### `scripts/generate_replay_chunk_plan.py`

**Purpose:** Read the scenario YAML, generate a list of monthly chunks, write
`chunk_plan.json`, and output `replay_id`.

**Behavior:**

For `full_chunked` mode:
1. Parse `evaluation.start_date` and `evaluation.end_date` from scenario YAML.
2. Generate monthly chunks:
   - First chunk: `[evaluation.start_date, last day of that month]`
   - Middle chunks: `[first day of month, last day of month]`
   - Last chunk: `[first day of last month, evaluation.end_date]`
   - If `evaluation.end_date` is the last day of its month, the last chunk is a
     full month.
3. Generate `replay_id` as UTC timestamp `YYYY-MM-DDTHH:MM:SSZ` unless
   `--replay-id` is provided.
4. Derive `chunk_id` for each chunk as `YYYY-MM-DD_to_YYYY-MM-DD`.

For `single_chunk` mode:
1. Validate that `--chunk-start` and `--chunk-end` are provided. Fail fast if not.
2. Validate chunk boundaries are within scenario evaluation window.
3. If `--chunk-start > evaluation.start_date` and no `--resume-state-dir` is
   provided later, issue a warning (enforcement is in the runner).
4. Generate a plan with one chunk.

**Output `chunk_plan.json`:**

```json
{
  "scenario_id": "hsq_replay_2025_05_to_2026_05_v1",
  "replay_id": "2026-05-24T08:00:00Z",
  "scenario_path": "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml",
  "run_mode": "full_chunked",
  "evaluation_start_date": "2025-05-01",
  "evaluation_end_date": "2026-05-17",
  "chunks": [
    {
      "chunk_id": "2025-05-01_to_2025-05-31",
      "chunk_start": "2025-05-01",
      "chunk_end": "2025-05-31",
      "is_first": true
    },
    {
      "chunk_id": "2025-06-01_to_2025-06-30",
      "chunk_start": "2025-06-01",
      "chunk_end": "2025-06-30",
      "is_first": false
    },
    {
      "chunk_id": "2026-05-01_to_2026-05-17",
      "chunk_start": "2026-05-01",
      "chunk_end": "2026-05-17",
      "is_first": false
    }
  ]
}
```

`scenario_id` is required in `chunk_plan.json` so that `run_replay_chunks.py` can
reconstruct the canonical run directory path:

```python
run_dir = output_root / "runs" / scenario_id / replay_id
```

where `output_root = evaluation/replay` (not `evaluation/replay/runs`).

**`single_chunk` mid-period fail-fast:**

`generate_replay_chunk_plan.py` receives `--resume-from-artifact` as a parameter.
If `run_mode = single_chunk`, `chunk_start > evaluation.start_date`, and
`--resume-from-artifact` is empty, the script must fail fast with:

```
ERROR: resume_from_artifact is required for single_chunk mode when chunk_start > evaluation.start_date
```

Do not defer this check to the runner. Fail before writing `chunk_plan.json`.

**GitHub Actions output:**

The script writes only `chunk_plan.json`. The workflow step reads `replay_id` from
the file and appends to `$GITHUB_OUTPUT` explicitly (see Step 6 above).

---

### `scripts/run_replay_chunks.py`

**Purpose:** Execute all chunks from `chunk_plan.json` sequentially, with automatic
state handoff.

**Behavior:**

1. Load `chunk_plan.json`. Extract `scenario_id`, `replay_id`, `scenario_path`,
   `chunks`.
2. Compute canonical run directory:
   ```python
   run_dir = Path(output_root) / "runs" / scenario_id / replay_id
   ```
   where `output_root = evaluation/replay` (passed via `--output-root`).
3. For each chunk in order:
   a. Determine `--resume-from-state` path:
      - First chunk with `--resume-state-dir`: search for exactly one file named
        `state_final.sqlite` under `resume_state_dir`. If zero or more than one
        found, fail fast with a clear error.
      - First chunk without `--resume-state-dir`: no `--resume-from-state` passed.
      - Subsequent chunks: `run_dir / "chunks" / prev_chunk_id / "state_final.sqlite"`
   b. Call the runner:
      ```
      python scanner/tools/run_historical_daily_replay.py \
        --scenario <scenario_path> \
        --output-root evaluation/replay \
        --replay-id <replay_id> \
        --chunk-start <chunk_start> \
        --chunk-end <chunk_end> \
        --chunk-id <chunk_id> \
        [--resume-from-state <path>]
      ```
   c. Verify `run_dir / "chunks" / chunk_id / "state_final.sqlite"` exists after
      completion. If not, abort with a clear error — do not proceed to next chunk.
   d. Log chunk completion with timing.
4. On completion of all chunks, log total elapsed time and final event count from
   `run_dir / "replay_manifest.json"`.

**`run_replay_chunks.py` does not upload artifacts.** Artifact upload is the
workflow's responsibility exclusively.

**Error behavior:**
- If any chunk fails, log the failure and exit non-zero.
- Do not attempt subsequent chunks after a failure.
- Leave all completed chunk outputs and `state_latest.sqlite` intact for debugging.

---

## Single_chunk mode rules

```
single_chunk without resume_from_artifact:
  Allowed only if chunk_start == scenario.evaluation.start_date.
  Otherwise fail fast in generate_replay_chunk_plan.py before chunk_plan.json is written.

single_chunk with resume_from_artifact:
  After artifact download, exactly one file named state_final.sqlite must exist
  under resume_state/.
  If zero or more than one found: fail fast with clear error.
  That exact path is passed as --resume-from-state to the runner.
```

---

## Validation rules — fail fast before execution

| Condition | Error |
|---|---|
| `run_mode = single_chunk` and `chunk_start` or `chunk_end` missing | `chunk_start and chunk_end are required for single_chunk mode` |
| `run_mode = single_chunk`, `chunk_start > evaluation.start_date`, no `resume_from_artifact` | `resume_from_artifact is required for mid-period single_chunk` |
| SHA256 mismatch | `SHA256 verification failed` |
| Scenario validation fails | propagate runner error |
| Chunk plan produces zero chunks | `chunk plan is empty` |

---

## BTC regime labels

BTC phase labels are used only in Backtest-1 evaluation, not as chunk boundaries.
This workflow does not reference regime labels. Chunking follows calendar months only.

---

## Do not change

- `scanner/tools/run_historical_daily_replay.py` (except bug fixes)
- `scanner/evaluation/historical_replay/` modules
- Scenario YAML format
- `scenario_config_hash` computation
- Pre-1 fetch logic

---

## Tests

Add focused tests:

### `tests/test_generate_replay_chunk_plan.py`

1. Full scenario May 2025 – May 2026: correct number of monthly chunks generated.
2. First chunk starts at `evaluation.start_date`.
3. Last chunk ends at `evaluation.end_date`, not necessarily end of month.
4. No gaps between consecutive chunk boundaries.
5. `replay_id` is generated if not provided; used as-is if provided.
6. `scenario_id` is present in `chunk_plan.json` output.
7. `single_chunk` mode with valid `chunk_start`/`chunk_end` and first-chunk: one chunk in plan.
8. `single_chunk` mode missing `chunk_start`: fail fast.
9. `single_chunk` mid-period without `resume_from_artifact`: fail fast before writing plan.
10. Chunk outside evaluation window: fail fast.

### `tests/test_run_replay_chunks.py`

1. Sequential execution: chunks run in order, state handoff path correct, uses `evaluation/replay` as output_root.
2. First chunk: no `--resume-from-state` passed.
3. Second chunk: `--resume-from-state` set to first chunk's `state_final.sqlite`.
4. Missing `state_final.sqlite` after chunk: abort, next chunk not started.
5. `--resume-state-dir` with exactly one `state_final.sqlite`: passed correctly.
6. `--resume-state-dir` with zero files: fail fast.
7. `--resume-state-dir` with multiple files: fail fast.
8. All chunks complete: final manifest shows correct `is_complete` value.

Use stubs/mocks for the runner call. Do not require real Pre-1 Parquet data.

---

## Acceptance criteria

- AC1: `workflow_dispatch` with default inputs runs all monthly chunks sequentially.
- AC2: Monthly chunks are derived automatically from scenario YAML; no manual input required.
- AC3: All chunks share one `replay_id`.
- AC4: SHA256 verified against `.sha256` release asset file before extraction.
- AC5: Post-extraction validation verifies required history files exist.
- AC6: Scenario is validated before chunk plan is generated.
- AC7: `chunk_plan.json` contains `scenario_id`.
- AC8: `run_replay_chunks.py` uses `evaluation/replay` as output_root, not `evaluation/replay/runs`.
- AC9: State handoff: each chunk (except first) receives prior chunk's `state_final.sqlite`.
- AC10: On chunk failure: workflow exits non-zero, completed outputs remain intact.
- AC11: `single_chunk` mid-period without `resume_from_artifact`: fail fast in plan generator.
- AC12: `single_chunk` with `resume_from_artifact`: exactly one `state_final.sqlite` required.
- AC13: Replay outputs uploaded as artifact even on failure (`if: always()`).
- AC14: `run_replay_chunks.py` does not upload artifacts.
- AC15: All tests pass.
- AC16: No regression in existing replay or chunk runner tests.

---

## Definition of Done

- Workflow file `.github/workflows/run-historical-replay.yml` created.
- Helper scripts `scripts/generate_replay_chunk_plan.py` and
  `scripts/run_replay_chunks.py` created.
- All acceptance criteria met.
- Test files added with all cases passing.
- Codex report includes: files created, example `chunk_plan.json` for the canonical
  scenario, pytest result, manual trigger instructions.
