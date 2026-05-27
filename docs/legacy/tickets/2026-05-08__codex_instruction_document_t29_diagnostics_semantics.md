# Codex-Anweisung: Dokumentation der T29-Diagnostics-Semantik in `TRADEABILITY_GATE.md`

## Aufgabe

Bitte aktualisiere ausschließlich die Dokumentation.

Zieldatei:

```text
/docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md
```

Keine Code-Änderungen.

---

## Kontext

Mit T29 wurden diese Top-Level-Felder in `symbol_diagnostics.jsonl.gz` eingeführt:

```text
execution_size_class
recommended_position_factor
execution_grade_effective
is_reduced_size_eligible
is_tradeable_candidate
```

Der erste T29-Shadow-Live-Run zeigt, dass die Implementierung grundsätzlich korrekt funktioniert. Es gibt aber zwei Semantikpunkte, die in der Doku klar erklärt werden müssen.

### Punkt 1 — `is_reduced_size_eligible` bei `direct_ok`

`is_reduced_size_eligible` ist auch bei `direct_ok`-Records `true`.

Der Feldname klingt nach „für reduzierte Positionsgröße geeignet“, bedeutet aber tatsächlich:

```text
tradeable at the policy-allowed position size, whether full or reduced
```

Also nicht:

```text
only eligible for reduced-size trading
```

### Punkt 2 — `execution_size_class = "full"` hat zwei mögliche Bedeutungen

`execution_size_class = "full"` kann auftreten bei:

```text
direct_ok + full depth
marginal + full depth
```

Bei `direct_ok` bedeutet es: alle Execution-Metriken bestanden, volle Position möglich.

Bei `marginal + full` bedeutet es: Orderbook-Tiefe reicht für eine volle Position, aber mindestens ein anderes Execution-Qualitätsmerkmal hielt den Record unterhalb von `direct_ok`.

Daher müssen Consumer immer beide Felder gemeinsam lesen:

```text
execution_status_raw
execution_size_class
```

---

## Was zu tun ist

Bitte füge den folgenden Abschnitt nahe am Ende von `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md` ein, bevorzugt nach einem bestehenden Determinism-/Diagnostics-Abschnitt, falls vorhanden.

Formulierungen dürfen minimal an den Stil des Dokuments angepasst werden. Inhalt und Semantik müssen erhalten bleiben.

---

## T29 Diagnostics Field Semantics

T29 introduced five new top-level fields in `symbol_diagnostics.jsonl.gz`.
This section documents their intended meaning to prevent misinterpretation.

### Field overview

| Field | Type | Meaning |
|---|---|---|
| `execution_size_class` | string enum | Depth-derived position size classification |
| `recommended_position_factor` | float or null | Operative position size factor (0.00–1.00) |
| `execution_grade_effective` | float or null | Final execution grade used by decision/ranking |
| `is_reduced_size_eligible` | bool | Tradeable at any policy-allowed position size |
| `is_tradeable_candidate` | bool | In a top bucket and tradeable |

### `execution_size_class` is a depth classification, not a final tradeability verdict

`execution_size_class` reflects only the orderbook depth dimension:

```text
full           depth >= 100% of threshold; full position supportable by depth alone
reduced_75     depth >= 75% of threshold
reduced_50     depth >= 50% of threshold
reduced_25     depth >= 25% of threshold
observe_only   depth < 25% of threshold; not tradeable at minimum size
blocked        execution_status_raw = fail; hard no-trade
not_evaluable  execution attempted but orderbook evidence insufficient
not_evaluated  execution not attempted for this symbol
```

`execution_size_class` does not replace `execution_status_raw`. Both fields must be read together:

- `execution_status_raw` is the canonical execution outcome (`direct_ok`, `tranche_ok`, `marginal`, `fail`, `unknown`).
- `execution_size_class` is the depth-derived position size classification.

Critical: `execution_size_class = "full"` does not imply `execution_status_raw = "direct_ok"`.
A marginal record with sufficient depth can also receive `execution_size_class = "full"`.

| `execution_status_raw` | `execution_size_class` | Meaning |
|---|---|---|
| `direct_ok` | `full` | All execution metrics passed; full position |
| `marginal` | `full` | Depth sufficient; another metric kept execution below `direct_ok` |
| `marginal` | `reduced_25` | Depth at 25–50% of threshold; reduced position |

Always read both fields when making tradeability decisions.

### `is_reduced_size_eligible` covers full and reduced positions

Despite its name, `is_reduced_size_eligible` is true for `direct_ok` records as well as for reduced-size marginal records.

Its intended meaning is:

```text
is_reduced_size_eligible = true
iff execution_size_class in {full, reduced_75, reduced_50, reduced_25}
and execution_status_raw in {direct_ok, tranche_ok, marginal}
and spread/slippage gates pass if evaluated
```

The field answers:

```text
Is this symbol tradeable at the policy-permitted position size, whether full or reduced?
```

It does not mean:

```text
Only suitable for a reduced position.
```

A future rename to `is_execution_eligible` or `is_policy_tradeable` would be more precise, but no rename is implemented in T29.

### `execution_grade_effective` is the ranking input

`execution_grade_effective` is the grade injected into the T12 priority-score formula. It reflects the T29 size-class mapping:

```text
direct_ok                    -> 100.0
tranche_ok                   -> 75.0
marginal + full              -> 75.0
marginal + reduced_75        -> 75.0
marginal + reduced_50        -> 60.0
marginal + reduced_25        -> 40.0
marginal + below_min         -> 0.0
fail                         -> 0.0
unknown / not_evaluable      -> null
```

Do not use `execution_grade_t16` for ranking. That field is a raw T16 audit field and is currently null because T16 does not emit a fine-grained grade.

`execution_grade_effective` is the authoritative execution-grade input for T12 ranking/decision.

### `not_evaluable` vs. `not_evaluated`

These two `execution_size_class` values are semantically distinct and must not be collapsed:

```text
not_evaluated   execution was not attempted (`execution_attempted = false`)
not_evaluable   execution was attempted but required metrics are missing, stale, or invalid
```

---

## Invarianten

- Modify only `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`.
- Do not change code.
- Do not change existing execution semantics.
- Do not rename fields.
- Do not remove existing document content.
- Keep formatting consistent with the existing document.
- Run `python -m pytest -q` after the change and report the result.
