# AGENTS.md — Spot Altcoin Scanner

## Read first
1. `docs/canonical/AUTHORITY.md`
2. `docs/canonical/INDEX.md`
3. `docs/canonical/WORKFLOW_CODEX.md`

## Precedence
Current repository reality is the primary anchor for implemented scanner behavior. `docs/canonical/AUTHORITY.md` is the central documentation authority and precedence file; `docs/canonical/INDEX.md` is the role/navigation index.

Auto-docs such as `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are generated navigation/context helpers, not authority for implemented behavior.

## Fixed decisions (Phase 1)
- Global Top‑20 tab + Setup tabs (Top‑10 each)
- No trading bot; no TP/exit automation in daily runs
- Potenzialdefinition: +10% bis +20%
- percent_rank population = all midcaps after hard gates with valid history
- Liquidity stage: proxy → orderbook Top‑K (default 200) → re-rank
- Tokenomist optional; Phase 1 must work without
- EMA standard, ATR Wilder
- `run_mode=standard` requires CMC key (Option 1)

## Working style
- One ticket per PR
- Tests first (golden/unit), then code
- Schema changes: bump `schema_version` + update `docs/SCHEMA_CHANGES.md`

## Default- und Edgecase-Regeln (gilt für alle Tickets/PRs)

- **Config Defaults:** Wenn Code Config liest/validiert, muss er die gleiche Default-Semantik verwenden wie `ScannerConfig` (oder zentrale Accessor-Funktionen).  
  **Missing key darf nicht automatisch als invalid gelten**, außer das ist ausdrücklich spezifiziert und getestet.
- **Missing vs Invalid:** Tickets müssen Verhalten für fehlende Keys getrennt von ungültigen Werten definieren.
- **Nullability:** Wenn ein Feld semantisch “nicht evaluierbar” ist, muss `null` erhalten bleiben (kein implizites `bool(...)`/Coercion).
- **Strict/Preflight:** `--strict-*` muss atomar sein: Preflight prüft alles vor Writes; bei Failure **keine Partial Writes**.

## CI must pass
```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```
