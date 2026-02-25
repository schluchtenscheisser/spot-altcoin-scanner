ARCHIVED: Superseded by `docs/canonical/MAPPING.md`.

Start here: `docs/canonical/INDEX.md`

# Mapping Layer Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

The Mapping Layer links **exchange assets** (MEXC symbols) to **market cap assets** (CMC or equivalent).

This component is critical because:
- scoring depends on OHLCV from MEXC,
- filtering depends on market cap data from CMC,
- incorrect linking produces **false signals** or **missing assets**,
- backtests require stable deterministic mapping.

The Mapping Layer is one of the most failure-sensitive components in the system.

---

## 2. Mapping Entities

### 2.1 Exchange Asset (MEXC)

Example:
- `symbol`: `HUSDT`
- `base_asset`: `H`
- `quote_asset`: `USDT`

Exchange assets define **tradeability**.

### 2.2 Market Cap Asset (CMC)

Fields (min):
- `id`
- `symbol`
- `slug`
- `name`
- `market_cap_usd`
- `rank`
- `supply`

Market cap assets define **valuation filters**.

---

## 3. Mapping Relationship

Mapping is a function:

```
MEXC.base_asset → CMC.asset
```

Output:
- target CMC asset or null (no match)
- confidence level
- mapping method
- collision context

This relationship must be:
- deterministic
- reproducible
- fixable via overrides

---

## 4. Mapping Strategies

The mapping uses layered strategies:

### 4.1 Strategy S1: Symbol Exact Match

Example:

```
base_asset = "H"
CMC.symbol = "H"
```

Success only if:
- symbol match is 1:1
- no collisions (multiple CMC assets with same symbol)

### 4.2 Strategy S2: Normalized Symbol Match

Normalize:
- uppercase
- whitespace strip
- suffix strip (optional)
- case-insensitive compare

Example:

```
"MPLX" == "mplx"
```

### 4.3 Strategy S3: Override Table

Manual mapping via file:

```
mapping_overrides.json
```

Useful for:
- collisions
- ambiguous assets
- symbol reuse cases
- renamed assets

### 4.4 Strategy S4: Disable / Exclusion

If no reliable mapping exists:
- asset excluded from pipeline

---

## 5. Collisions

A **collision** occurs if:

```
N > 1 CMC assets match base_asset
```

Example:

```
"MPLX" → [AssetA, AssetB]
```

System must:
1. detect collision
2. log collision record
3. surface in report
4. allow override resolution
5. reject asset if unresolved

Collisions cannot be silently resolved.

---

## 6. Confidence Levels

Mapping must assign confidence:

| Confidence | Meaning |
|---|---|
| high | deterministic, collision-free, no override required |
| medium | deterministic after override |
| low | ambiguous or fallback |
| none | no mapping, asset ignored |

Configuration may enforce:

```
require_high_confidence = true
```

---

## 7. Override File

Override file format:

```
mapping_overrides.json
```

Example shape:
```json
{
  "H": {
    "cmc_id": 12345,
    "method": "manual_symbol_match",
    "notes": "Ticker collision resolved"
  }
}
```

Overrides must support:
- resolution to CMC id
- metadata for audit
- notes for future review

---

## 8. Reporting Requirements

Mapping module must generate:

- collision_report.csv
- missing_mapping_report.csv
- override_report.csv

These are crucial for debugging, review, and iterative improvement.

---

## 9. Mapping Effect on Filtering

Mapping occurs before filters because:

- market cap filter depends on mapping
- tradeability filter depends on MEXC alone

Flow:

```
MEXC → Mapping → MarketCap → Filtering
```

Assets without valid market cap are excluded.

---

## 10. Determinism

Mapping must be consistent across runs for:

- reproducible outputs
- backtests
- snapshot compatibility

Overrides must be version-controlled.

---

## 11. Anti-Goals (Common Pitfalls)

The mapping layer must not:

- perform fuzzy matching (string similarity)
- guess mappings automatically
- match on name fields exclusively
- consume multiple MCAP providers
- fallback to CoinGecko when CMC unavailable (v1)
- change mapping logic between runs without versioning

These behaviors lead to silent corruption of outputs.

---

## 12. Testing Criteria

A mapping implementation is valid if:

- same input → same output
- collisions correctly surfaced
- overrides correctly applied
- unmapped assets consistently filtered
- confidence behaves as spec’d
- mapping does not drift across versions

Snapshot-based tests can verify stability.

---

## 13. Integration Points

Mapping feeds:

- Filter Gate (market cap)
- Feature Engine (OHLCV context)
- Scoring (valuation-based penalties optional future)
- Backtests (deterministic asset IDs)

Mapping does not interact with setup scoring logic directly.

---

## 14. Summary

Mapping is a foundational component.  
Tradeability + valuation must both pass.  
Failures must be explicit, not silent.

---

## End of `mapping.md`
