> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

\# \[P1] Harden raw MarketCap parquet export against oversized object-integer fields



\## Context / Source (optional)

\- A routine daily scan failed during raw MarketCap snapshot export with:

&nbsp; - `Integer value 155579987314341800 is outside of the range exactly representable by a IEEE 754 double precision value`

&nbsp; - `Conversion failed for column minted\_market\_cap with type object`

\- Current implementation in `scanner/utils/raw\_collector.py` flattens CMC listings via `pd.json\_normalize(...)` and only converts `dict` / `list` object values to JSON strings before calling `save\_raw\_snapshot(..., require\_parquet=True)`.

\- `pyarrow` is already a declared dependency in `requirements.txt`, so this failure is not primarily “missing parquet backend”, but a dataframe typing / parquet-serialization issue.

\- Relevant code path:

&nbsp; - `scanner/utils/raw\_collector.py`

&nbsp; - `scanner/utils/save\_raw.py` (behavioral dependency; exact write path must remain compatible)



\## Goal

Raw MarketCap snapshots must write successfully to Parquet even when upstream listing payloads contain very large integer-like values in `object`-typed columns (for example `minted\_market\_cap`), without precision loss and without disabling the required Parquet snapshot for this stage.



\## Scope

Allowed changes:

\- `scanner/utils/raw\_collector.py`

\- `scanner/utils/save\_raw.py` only if strictly required for shared parquet-sanitization behavior

\- Tests under existing test locations for raw snapshot / collector behavior



\## Out of Scope

\- Changing upstream MarketCap API payload semantics

\- Changing business logic, ranking, scanner decisions, or downstream score calculations

\- Making raw MarketCap parquet optional for this ticket

\- Broad refactors unrelated to raw snapshot serialization

\- Schema/field renames unless strictly required and documented



\## Canonical References (important)

\- `docs/AGENTS.md`

\- `docs/canonical/AUTHORITY.md`

\- `docs/canonical/INDEX.md`

\- `docs/tickets/\_TICKET\_PREFLIGHT\_CHECKLIST.md`

\- `docs/tickets/\_TEMPLATE.md`



\## Proposed change (high-level)

Describe intended behavior:



\- Before:

&nbsp; - `collect\_raw\_marketcap(...)` uses `pd.json\_normalize(data, sep="\_\_")`.

&nbsp; - Only `dict` / `list` values inside `object` columns are converted to JSON strings.

&nbsp; - Other `object` columns are passed through unchanged.

&nbsp; - If a column such as `minted\_market\_cap` contains very large Python integers or mixed object values, Parquet export can fail.



\- After:

&nbsp; - Before Parquet export, raw MarketCap snapshots are sanitized for parquet-safe typing.

&nbsp; - `dict` / `list` values continue to be JSON-serialized.

&nbsp; - `object` columns that contain integer-like values beyond safe float-style representation, or mixed large numeric/object payloads that are not parquet-safe, are converted deterministically to string representation for raw snapshot storage.

&nbsp; - No precision may be lost for affected raw values.

&nbsp; - Parquet export for MarketCap raw snapshots succeeds for the known failure case.



\- Edge cases:

&nbsp; - Empty payload still produces existing warning/early-return behavior.

&nbsp; - `None` values in affected columns remain semantically missing and must not be converted into fake booleans.

&nbsp; - Mixed `object` columns with `dict` / `list` / scalar values must be serialized deterministically.

&nbsp; - Non-finite numeric values (`NaN`, `inf`, `-inf`) must not silently turn into misleading numeric-looking outputs if a sanitization path touches them.



\- Backward compatibility impact:

&nbsp; - Raw snapshot parquet schema for affected columns may change from loosely inferred numeric/object to string for serialization safety.

&nbsp; - CSV raw snapshot behavior remains unchanged unless shared sanitization intentionally aligns both outputs.



\## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> Diese Sektion ist eine Ausführungsanweisung für Codex. Wenn hier etwas nicht eindeutig ist, muss das Ticket angepasst werden (kein Raten).



\- \*\*Config/Defaults:\*\* Dieses Ticket liest keine neue Config und ändert keine Config-Validierung. Es dürfen keine neuen Config-Keys eingeführt werden.

\- \*\*Nullability:\*\* Keine implizite `bool(...)`-Coercion für betroffene Werte. `None` / fehlende Werte bleiben semantisch fehlend.

\- \*\*Strict/Preflight:\*\* Dieses Ticket betrifft keinen `--strict-\*`-Pfad und definiert keine neue Preflight-Atomizität.

\- \*\*Not-evaluated vs failed:\*\* Dieses Ticket ändert keine fachlichen Statuspfade. Es behandelt ausschließlich technische Snapshot-Serialisierung.

\- \*\*Determinismus:\*\* Sanitization muss deterministisch sein. Gleiche Inputs erzeugen gleiche Datentyp-/String-Ausgaben.

\- \*\*No precision loss:\*\* Sehr große Integer-Werte aus Raw-MarketCap-Payloads dürfen nicht über Float-Konvertierung “gerettet” werden.

\- \*\*Field semantics:\*\* Raw-Feldnamen bleiben unverändert. Es werden keine Alias-Feldnamen eingeführt.

\- \*\*Serialization rule:\*\* Für parquet-unsafe `object`-Spalten mit oversized integer-like Werten ist String-Serialisierung die bevorzugte Sicherungsregel für den Raw-Snapshot.



\## Implementation Notes (optional but useful)

\- Current failure happens in `collect\_raw\_marketcap(...)` after `pd.json\_normalize(...)` and before / during `save\_raw\_snapshot(...)`.

\- The known problematic field is `minted\_market\_cap`, but the implementation should avoid hard-coding only this single field if a small generic sanitizer can safely cover the same class of failure.

\- Prefer a local helper or shared sanitizer with narrow scope instead of a broad dataframe-wide behavioral rewrite.

\- Avoid converting clean numeric columns unnecessarily.

\- If schema-impacting behavior is observable for raw outputs, document it in the appropriate canonical changelog/doc if required by repo workflow.



\## Acceptance Criteria (deterministic)

1\) A raw MarketCap payload containing `minted\_market\_cap=155579987314341800` no longer causes Parquet export failure during `collect\_raw\_marketcap(...)`.

2\) Affected oversized integer-like values are preserved without precision loss in the raw snapshot output path.

3\) Existing `dict` / `list` serialization behavior for nested raw payload values remains functional and deterministic.

4\) No field rename is introduced; `minted\_market\_cap` remains `minted\_market\_cap` in the flattened raw snapshot.

5\) `None` / missing values in affected columns are not coerced into `False`, `0`, or non-null placeholder strings unless explicitly required by existing raw snapshot conventions.

6\) A regression test covers the reported failure class with Parquet export required.

7\) At least one test covers a mixed/object edge case beyond the exact reported value, so the fix is not brittle to only one literal input.



\## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

\- \*\*Config Defaults (Missing key → Default):\*\* ✅ (N/A – Ticket liest keine Config)

\- \*\*Config Invalid Value Handling:\*\* ✅ (N/A – Ticket validiert keine Config)

\- \*\*Nullability / kein bool()-Coercion:\*\* ✅ (AC: #5 ; Test: null/None preservation in affected column)

\- \*\*Not-evaluated vs failed getrennt:\*\* ✅ (N/A – Ticket ändert keine fachlichen Evaluationsstatus)

\- \*\*Strict/Preflight Atomizität (0 Partial Writes):\*\* ✅ (N/A – kein strict/preflight scope)

\- \*\*ID/Dateiname Namespace-Kollisionen (falls relevant):\*\* ✅ (N/A – Ticket ändert keine Snapshot-Namenslogik)

\- \*\*Deterministische Sortierung/Tie-breaker:\*\* ✅ (N/A – kein Ranking/Sorting scope; deterministische Serialisierung covered by AC #3)



\## Tests (required if logic changes)

\- Unit:

&nbsp; - `collect\_raw\_marketcap(...)` with payload containing oversized integer-like `minted\_market\_cap` in an `object` column → Parquet path succeeds.

&nbsp; - Sanitization preserves exact value semantics (string-preserved or explicit safe target type with no precision loss).

&nbsp; - `None` in same/similar column remains semantically missing.

\- Integration:

&nbsp; - End-to-end raw snapshot write for MarketCap with `require\_parquet=True` succeeds and produces expected raw artifacts.

\- Golden fixture / verification:

&nbsp; - Fixture with representative mixed MarketCap listing payload including nested `quote` fields plus `minted\_market\_cap`.

&nbsp; - Verify field presence and exact preserved raw value.

\- If scoring/threshold/curve changes: not applicable.



\## Constraints / Invariants (must not change)

\- \[ ] Raw MarketCap snapshot remains enabled with `require\_parquet=True`

\- \[ ] No change to scanner decision logic or ranking outputs

\- \[ ] No field rename for existing flattened raw fields

\- \[ ] No float-based precision loss for oversized integer raw values

\- \[ ] Existing nested `dict` / `list` raw serialization remains supported

\- \[ ] Deterministic serialization for equal inputs



\## Definition of Done (Codex must satisfy)

(Reference: `docs/canonical/WORKFLOW\_CODEX.md`)

\- \[ ] Implemented code changes per Acceptance Criteria

\- \[ ] Updated canonical docs under `docs/canonical/` (if logic/params/outputs changed)

\- \[ ] Updated `docs/canonical/VERIFICATION\_FOR\_AI.md` if any scoring/threshold/curve behavior changed

\- \[ ] PR created: exactly \*\*1 ticket → 1 PR\*\*

\- \[ ] Ticket moved to `docs/legacy/tickets/` after PR is created



\## Metadata (optional)

```yaml

created\_utc: "2026-03-09T00:00:00Z"

priority: P1

type: bugfix

owner: codex

related\_issues: \[]

