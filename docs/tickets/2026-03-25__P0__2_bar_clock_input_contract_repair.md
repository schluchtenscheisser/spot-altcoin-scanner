# Title
[P0] Repair bar-clock input contract for millisecond timestamps and naive-datetime rejection

## Context / Source
The deployed bar-clock foundation ticket correctly established canonical UTC closed-bar semantics, but the current implementation contract still leaves two critical input-handling defects:

1. numeric timestamp inputs are unsafe if the implementation treats all numerics as epoch seconds even though repo/runtime conventions already use millisecond timestamps heavily and `intraday_bar_id` itself is defined in epoch milliseconds;
2. naive `datetime` inputs are unsafe if they are silently reinterpreted as UTC instead of being rejected explicitly.

This follow-up ticket repairs the `bar_clock` public input contract so later tickets can reuse it safely for cache IDs, run metadata, and `bars_since_*` deltas.

**Primary authoritative references for this ticket**
- `2026-03-23__P0__bar_clock_sqlite_config_foundation.md`
- `independence_release_gesamtkonzept_final.md` §2.1, §18.2, §19
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` §12.2, §15

`depends_on: [2026-03-23__P0__bar_clock_sqlite_config_foundation]`

## Goal
After this ticket is completed, the public `bar_clock` API must have a deterministic, explicit, and repo-safe input contract:

1. millisecond Unix timestamps are accepted consistently for numeric timestamp inputs;
2. naive `datetime` inputs are rejected explicitly instead of being silently relabeled as UTC;
3. accepted input forms, rejected input forms, and exception behavior are canonicalized in docs and tests;
4. no ambiguity remains about seconds vs milliseconds or naive vs timezone-aware datetimes.

## Scope
Allowed changes for this ticket:

- `scanner/data/bar_clock.py`
- `scanner/data/__init__.py` if needed
- `tests/**` for bar-clock input-contract tests
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md` if needed for timestamp-unit clarity
- `docs/canonical/DATA_MODEL.md` if needed for timestamp field wording consistency
- `docs/canonical/ARCHITECTURE.md` only if a bar-clock public contract summary is needed
- `docs/tickets/**` only as required by `docs/canonical/WORKFLOW_CODEX.md`

## Out of Scope
- Changing daily/4h boundary semantics
- Changing `daily_bar_id`, `intraday_bar_id`, or `delta_closed_4h_bars` definitions
- Changing SQLite schema or config scaffolding
- Introducing local-time support
- Introducing heuristic timezone inference
- Accepting ambiguous string formats beyond what the existing bar-clock contract already allows
- Implementing state machine or cache logic
- Manually editing `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

## Canonical References (important)
- `2026-03-23__P0__bar_clock_sqlite_config_foundation.md`
- `independence_release_gesamtkonzept_final.md` §18.2, §19
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` §12.2, §15
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/tickets/_TEMPLATE.md`

> If the current authoritative reference, Canonical, and existing code conflict, the authoritative reference wins. If additional clarification is needed, extend the ticket or ask the user rather than interpret.

## Proposed change (high-level)

### Before
- The bar-clock semantics for closed bars are canonicalized.
- The public input contract for numeric timestamps and naive datetimes is still underspecified or incorrectly implemented.
- Callers may pass repository-standard millisecond timestamps and get incorrect results or errors if the implementation interprets numerics as seconds only.
- Callers may pass naive datetimes and get silent UTC reinterpretation.

### After
- Numeric inputs are handled deterministically and safely for repo-standard millisecond timestamps.
- Naive datetimes are rejected explicitly.
- Canonical docs and tests define accepted/rejected inputs with concrete examples.
- Future callers do not need to guess timestamp units.

### Edge cases
- `0`, negative values, and pre-1970 timestamps are not automatically invalid; their validity depends on whether they are finite numeric timestamps that can be converted deterministically. If the implementation intentionally disallows certain ranges, that rule must be explicit and tested.
- `None`, `NaN`, `inf`, and `-inf` remain invalid exactly as already defined unless this ticket explicitly tightens behavior further.
- Timezone-aware datetimes with non-UTC offsets are allowed only if they are converted to the same instant in UTC deterministically.
- Strings without timezone information must not be silently treated as UTC unless the existing bar-clock contract already explicitly allows that exact format and the docs keep it explicit.

### Backward compatibility impact
This ticket intentionally tightens the bar-clock API. Callers that previously passed naive datetimes must now fail fast with a clear error. Numeric callers using millisecond timestamps must now succeed deterministically.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Do not change bar semantics:** The already-defined closed-bar schedules and boundary rules remain exactly as specified in the foundation ticket.
- **Milliseconds are the numeric contract:** For raw `int`/`float` timestamp inputs, the canonical numeric unit for this ticket is Unix epoch milliseconds.
- **No silent timezone relabeling:** A naive `datetime` must not be converted via `replace(tzinfo=UTC)` or equivalent silent reinterpretation.
- **Reject ambiguity:** If an input form is ambiguous, reject it with a clear error rather than guessing.
- **One contract only:** Do not leave mixed docs or mixed tests that imply both “numeric seconds” and “numeric milliseconds” as equally canonical.
- **Reuse existing helpers carefully:** Existing repo timestamp helpers may be reused only if their unit semantics match this ticket exactly.
- **Determinism:** Identical accepted inputs must produce identical outputs; identical invalid inputs must raise the same exception type and stable error wording class.

## Implementation Notes

### Public input contract to enforce
The bar-clock functions covered by this ticket are, at minimum:
- `daily_bar_id(...)`
- `intraday_bar_id(...)`
- `delta_closed_4h_bars(...)`

If the module exposes a shared coercion helper used by additional bar-clock public functions, the same contract must be applied consistently there too.

### Numeric timestamp rule (mandatory)
For raw numeric timestamp inputs (`int` and finite `float`):

- canonical interpretation in this ticket: **Unix epoch milliseconds**
- examples:
  - `1774324800000` represents `2026-03-24T04:00:00Z`
  - `1774310400000` represents `2026-03-24T00:00:00Z`

Behavior requirements:
- finite numeric millisecond inputs that map to a valid instant must be accepted;
- `None` must raise `TypeError`;
- `NaN`, `inf`, `-inf` must raise `ValueError`;
- if the implementation chooses to reject fractional milliseconds, that must be explicit and tested;
- if the implementation accepts finite float milliseconds, conversion/rounding behavior must be explicit and tested.

### Naive datetime rule (mandatory)
For `datetime` inputs:

- timezone-aware `datetime` values are accepted;
- aware datetimes in non-UTC offsets must be normalized by instant to UTC;
- naive datetimes are invalid and must raise `TypeError` or `ValueError` consistently across all public bar-clock functions;
- silent reinterpretation of naive datetimes as UTC is forbidden.

### Missing vs invalid semantics
This ticket must make the distinction explicit:

- **missing input** (`None`) → invalid type error, not fallback;
- **invalid numeric** (`NaN`, `inf`, `-inf`) → invalid value error;
- **naive datetime** → invalid temporal form error;
- **valid aware datetime / valid numeric ms** → accepted and deterministic.

There is no fallback path that guesses timezone or timestamp unit.

### Canonical docs to update
At minimum, touched docs must state clearly:

- accepted numeric unit for bar-clock raw numeric inputs = epoch milliseconds;
- `intraday_bar_id` output unit remains epoch milliseconds;
- naive datetimes are rejected;
- examples for accepted and rejected forms.

### Concrete example matrix (must be implemented in docs and tests)
At minimum, include deterministic examples equivalent to these:

#### Accepted
- `daily_bar_id(1774324800000)` -> `"2026-03-23"`
- `intraday_bar_id(1774324800000)` -> `1774324800000`
- `delta_closed_4h_bars(1774310400000, 1774324800000)` -> `1`
- `daily_bar_id(datetime(2026, 3, 24, 5, 0, tzinfo=timezone.utc))` -> `"2026-03-23"`
- `intraday_bar_id(datetime(2026, 3, 24, 6, 0, tzinfo=timezone(timedelta(hours=2))))` -> same result as the equivalent UTC instant

#### Rejected
- `daily_bar_id(datetime(2026, 3, 24, 5, 0))` -> error (naive datetime)
- `intraday_bar_id(None)` -> `TypeError`
- `daily_bar_id(float("nan"))` -> `ValueError`
- `delta_closed_4h_bars(float("inf"), 1774324800000)` -> `ValueError`

If any exact example needs a different expected value because of the canonical closed-bar boundary definitions, adjust the example carefully and keep it consistent across docs and tests.

## Acceptance Criteria (deterministic)

1. `scanner/data/bar_clock.py` accepts raw numeric timestamp inputs in Unix epoch milliseconds for all touched public bar-clock functions.
2. No touched doc or test implies that raw numeric timestamp inputs are canonically interpreted as Unix epoch seconds.
3. Naive `datetime` inputs are rejected explicitly for all touched public bar-clock functions.
4. No touched code path uses silent timezone relabeling (`replace(tzinfo=UTC)` or equivalent) as acceptance behavior for naive datetimes.
5. `None`, `NaN`, `inf`, and `-inf` remain explicitly rejected with deterministic exception behavior.
6. At least one deterministic test covers:
   - valid millisecond numeric input,
   - naive datetime rejection,
   - `None` rejection,
   - non-finite numeric rejection,
   - equality of results for equivalent instants expressed in different aware timezones.
7. Canonical docs touched by this ticket explicitly state:
   - raw numeric input unit,
   - output unit where relevant,
   - naive-datetime rejection behavior.
8. The PR archives the ticket in the same PR according to `docs/canonical/WORKFLOW_CODEX.md`.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ N/A — this ticket does not read config
- **Config Invalid Value Handling:** ✅ N/A — this ticket does not validate config keys
- **Nullability / kein bool()-Coercion:** ✅ covered — `None` is invalid input, not coerced
- **Not-evaluated vs failed getrennt:** ✅ covered — invalid input is explicit failure; there is no fallback/guess path
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A — no write pipeline introduced
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A
- **Deterministische Sortierung/Tie-breaker:** ✅ N/A — function determinism specified instead

## Tests (required if logic changes)

### Unit
Add/update deterministic unit tests for each touched public bar-clock function covering:
- valid integer millisecond timestamp input;
- valid aware `datetime` input in UTC;
- valid aware `datetime` input with non-UTC offset representing the same instant;
- rejection of naive `datetime`;
- rejection of `None`;
- rejection of `NaN`, `inf`, `-inf`;
- `delta_closed_4h_bars` with millisecond numerics across an exact 4h close boundary.

### Integration
If the repo already has a higher-level time utility or runtime metadata flow that consumes bar-clock outputs, add one lightweight integration assertion that millisecond timestamps from repo-standard fields can pass through the bar-clock API without unit reinterpretation.

### Golden fixture / verification
Not required. Deterministic unit tests with fixed UTC examples are sufficient.

## Constraints / Invariants (must not change)

- [ ] Daily close remains `00:00 UTC`
- [ ] 4h close schedule remains `00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC`
- [ ] Exact-close boundary remains closed/included
- [ ] `intraday_bar_id` output unit remains epoch milliseconds
- [ ] `bars_since_*` canonical 4h-bar semantics are unchanged
- [ ] No local-time support is introduced
- [ ] No silent timezone guessing is introduced
- [ ] One PR, one bar-clock input-contract repair only

## Preflight self-check
- [x] Current sole reference identified
- [x] Canonical collision check performed
- [x] Timestamp-unit ambiguity removed
- [x] Missing vs invalid semantics made explicit
- [x] Deterministic acceptance criteria defined
- [x] Tests stated for new edge cases
