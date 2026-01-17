# GPT Snapshot - 2026-01-17

## Status
**Type:** Automatic  
**Generated:** 16:38 UTC  
**Trigger:** Automatic (push to main)
**Session:** Automatic GitHub Actions workflow

---

## Recent Changes

### Last 5 Commits
- Update generate-gpt-snapshot.yml (ef233d9)
- docs: auto-update code map [skip ci] (e9ce815)
- Update update-code-map.yml (c68c399)
- snapshots: add GPT snapshot for 2026-01-17 [skip ci] (b90ee19)
- Add files via upload (1b0e059)
### Changed Files
```
.github/workflows/generate-gpt-snapshot.yml
```

---

## Current Project State

### Development Status
- **Phase:** 6 Complete (MVP)
- **MVP Status:** Complete ✅
- **Code Map:** `docs/code_map.md` (auto-updated)
- **Documentation:** Up to date
- **Total Modules:** 23 Python files

### Key Metrics
- **Universe:** 1837 MEXC USDT pairs
- **Mapping Success:** 88.4% (1624/1837)
- **Pipeline Steps:** 10
- **Scoring Modules:** 3 (Reversal, Breakout, Pullback)
- **Execution Time:** ~4-5 minutes (with cache)

### Architecture Overview
- **Entry Point:** `scanner/main.py`
- **Pipeline:** `scanner/pipeline/__init__.py` (10-step orchestration)
- **API Clients:** MEXC (free) + CoinMarketCap (free tier)
- **Caching:** File-based (`data/raw/YYYY-MM-DD/`)
- **Reports:** Markdown + JSON (`reports/`)
- **Snapshots:** Runtime data (`snapshots/runtime/`)

---

## Completed Phases (MVP)

### ✅ Phase 1: Foundation
- Utils: logging, time, I/O
- Config: YAML loading + validation

### ✅ Phase 2: Data Clients
- MEXC API client (1837 pairs)
- CoinMarketCap client (5000 listings)

### ✅ Phase 3: Mapping Layer
- Symbol mapper (88.4% success)
- Collision detection
- Manual overrides support

### ✅ Phase 4: Pipeline Components
- Filters (MidCap 100M-3B)
- Shortlist (top 100 by volume)
- OHLCV fetcher (1d + 4h)
- Feature engine (EMAs, ATR, returns, etc.)

### ✅ Phase 5: Scoring Modules
- Reversal (Priority: Downtrend → Base → Reclaim)
- Breakout (Range break + volume)
- Pullback (Trend continuation)

### ✅ Phase 6: Output & Automation
- Report generator (Markdown + JSON)
- Snapshot manager (backtesting data)
- GitHub Actions (daily 6:00 AM UTC)

---

## Notable Changes This Session

### 🔧 Workflow Changes
- `.github/workflows/generate-gpt-snapshot.yml`

---

## Open Tasks

- [ ] Review changes in latest commit
- [ ] Run scanner to validate: `python -m scanner.main --mode fast`
- [ ] Check logs: `cat logs/scanner_$(date +%Y-%m-%d).log`
- [ ] Update documentation if needed
- [ ] Monitor GitHub Actions runs

---

## For Next GPT Session

### Context to Remember
1. **Last Changes:** See commits above
2. **Current Focus:** MVP maintenance and monitoring
3. **Code Map Location:** `docs/code_map.md` (auto-updated)
4. **Specifications:** `docs/spec.md` (authoritative)
5. **Latest Snapshot:** This file

### Before Making Changes
1. ✅ Read `docs/code_map.md` - Complete structural overview
2. ✅ Read `docs/dev_guide.md` - Development workflow
3. ✅ Check latest snapshot (this file) - Recent changes
4. ✅ Review `docs/spec.md` - Design constraints
5. ✅ Check `README.md` - User-facing docs

### Quick Commands
```bash
# Run scanner (fast mode with cache)
python -m scanner.main --mode fast

# Run scanner (standard mode, fresh API calls)
python -m scanner.main --mode standard

# View latest report
cat reports/$(date +%Y-%m-%d).md

# Check logs
tail -50 logs/scanner_$(date +%Y-%m-%d).log

# Manual workflow triggers
gh workflow run "Update Code Map"
gh workflow run "Generate GPT Snapshot"
gh workflow run "Daily Scanner Run"
```

### Key Files Reference
- **Entry Point:** `scanner/main.py`
- **Config:** `config/config.yml`
- **Code Map:** `docs/code_map.md`
- **Specifications:** `docs/spec.md`
- **Latest Reports:** `reports/$(date +%Y-%m-%d).{md,json}`
- **Snapshots:** `snapshots/runtime/$(date +%Y-%m-%d).json`

---

## Important Notes

### API Keys & Secrets
- **CMC_API_KEY:** Set in GitHub Secrets + Codespaces Secrets
- **Free Tier:** 333 calls/month (using ~1/day)

### GitHub Actions Workflows
- **Daily Scanner Run:** 6:00 AM UTC daily
- **Update Code Map:** On Python file changes
- **Generate GPT Snapshot:** On push to main (this workflow)

### Known Limitations
- Some MEXC pairs have limited history (<60 days) → ~2-5% excluded
- Logging primarily to file (minimal console output)
- 213 symbols unmapped (low-volume/new tokens)

### Not Implemented (By Design)
- Global/combined scores (intentionally separate)
- ML/AI predictions (v1 scope)
- Auto-trading/execution (research tool only)

---

## Next Steps

### If Continuing Development:
1. Check this snapshot for recent changes
2. Review latest scanner reports in `reports/`
3. Verify GitHub Actions are running correctly
4. Decide: Implement Phase 7 (Backtesting) or refine existing features?

### If Monitoring Only:
1. Check daily reports: `reports/YYYY-MM-DD.md`
2. Look for high-scoring Reversal setups
3. Monitor GitHub Actions runs
4. Adjust config thresholds if needed: `config/config.yml`

### If Issues Arise:
1. Check logs: `logs/scanner_YYYY-MM-DD.log`
2. Verify CMC_API_KEY in GitHub/Codespaces Secrets
3. Check cache freshness: `data/raw/$(date +%Y-%m-%d)/`
4. Review GitHub Actions workflow logs

---

## End of Snapshot

**Generated:** 2026-01-17 16:38:34 UTC  
**Next Review:** Before next development session  
**Status:** ✅ 6 Complete (MVP) - Stable
