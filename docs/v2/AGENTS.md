# AGENTS.md — Spot Altcoin Scanner (Canonical v2)

## Read first
1) `docs/v2/AUTHORITY.md`
2) `docs/v2/20_FEATURE_SPEC.md`
3) `docs/v2/30_IMPLEMENTATION_TICKETS.md`

## Precedence
v2 > auto-docs > legacy.
- Auto-docs: `docs/code_map.md`, `docs/GPT_SNAPSHOT.md` (do not edit; keep under docs/)

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

## CI must pass
```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```
