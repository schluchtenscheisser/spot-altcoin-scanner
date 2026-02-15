## Summary
- [ ] Explain **what** changed (scope limited to one ticket/topic).
- [ ] Explain **why** the change is needed.
- [ ] List key files/functions touched.

## Risk & Transparency Checks (required)
- [ ] No silent behavior drift introduced.
- [ ] Config/feature/scoring semantics changed? If yes, docs updated.
- [ ] Output/schema changed? If yes, schema/version + migration notes included.
- [ ] Runtime degradation behavior is explicit (no hidden fallback).

## Validation
- [ ] Added/updated tests for the changed behavior.
- [ ] Included at least one deterministic regression test.
- [ ] CI-relevant commands run locally and results documented.

## Test Commands
```bash
# Example:
pytest -q
```

## Operational Notes
- [ ] Bot/API quota/outage handling considered.
- [ ] If live data can fail, degraded mode and freshness metadata are documented.
- [ ] If no cache exists in outage path, failure mode is explicit.
