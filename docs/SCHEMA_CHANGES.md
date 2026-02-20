# SCHEMA_CHANGES.md – Schema-/Output‑Änderungslog (verbindlich)

Dieses Dokument protokolliert alle Änderungen an:
- Report‑Schema (`reports/*.json` / `.md` / `.xlsx`)
- Snapshot‑Schema (`snapshots/runtime/*.json`, Raw‑Snapshots)
- Feature‑Key‑Semantik (wenn die Bedeutung eines Keys sich ändert)

**Regel:** Jede PR, die Schema oder Semantik ändert, muss hier einen Eintrag hinzufügen.

---

## Wie man dieses Log pflegt
1) In der PR prüfen: Wird ein neues Feld hinzugefügt? Wird ein Feld umbenannt/entfernt? Ändert sich die Bedeutung?
2) Wenn ja:
   - `schema_version` erhöhen (z. B. `v1` → `v2`)
   - Eintrag unten ergänzen
   - Im PR‑Text die Migration kurz beschreiben

---

## Eintrags‑Template (kopieren & ausfüllen)

### YYYY-MM-DD — schema_version vX → vY — <Kurztitel>
**PR:** <Link>  
**Typ:** additiv | breaking | semantisch (Bedeutung geändert)  

#### Was hat sich geändert?
- <z. B. neues Feld `asof_ts_ms` hinzugefügt>
- <z. B. `ohlcv_snapshot` enthält jetzt `close_time`, `quote_volume`>

#### Warum?
- <z. B. Reproduzierbarkeit / closed‑candle determination>

#### Kompatibilität
- **Rückwärtskompatibel?** Ja/Nein  
- Wenn Nein: Welche Consumer/Tools sind betroffen?

#### Migration / Vorgehen
- <Wie liest man alte Daten?>
- <Wie erkennt man Versionen?>
- <Ggf. Script/Anleitung, alte Snapshots zu transformieren>

#### Beispiel (kurz)
```json
{
  "schema_version": "vY",
  "asof_ts_ms": 0,
  "example_field": "..."
}
```

---

## Historie
*(Neue Einträge kommen hier darunter)*

### 2026-02-12 — schema_version v1.1 → v1.2 — QuoteVolume-Features ergänzt
**PR:** (branch-local, Thema 7)  
**Typ:** additiv

#### Was hat sich geändert?
- Feature-Output pro Timeframe ergänzt um:
  - `volume_quote`
  - `volume_quote_sma_14`
  - `volume_quote_spike`
- Semantik:
  - Baseline exklusive aktuelle Kerze (`t-14 .. t-1`)
  - Wenn `quoteVolume` in Klines fehlt, werden diese Keys nicht ausgegeben (kein Crash).

#### Warum?
- Volume-/Liquidity-Signale sollen auf QuoteVolume basieren, wenn vorhanden (Thema 7).

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additive Felder, bestehende Keys unverändert).

#### Migration / Vorgehen
- Consumer können die neuen Keys optional lesen.
- Alte Snapshots/Outputs ohne diese Keys bleiben weiterhin nutzbar.

#### Beispiel (kurz)
```json
{
  "schema_version": "v1.2",
  "1d": {
    "volume_quote": 205905.0,
    "volume_quote_sma_14": 179745.0,
    "volume_quote_spike": 1.1455
  }
}
```

### 2026-02-13 — schema_version v1.2 → v1.3 — Drawdown- und Scoring-Semantik korrigiert (Critical Findings)
**PR:** (branch-local, Critical Findings Remediation)  
**Typ:** semantisch

#### Was hat sich geändert?
- Semantik von `drawdown_from_ath` geändert: ATH wird nun auf ein konfigurierbares Fenster begrenzt (`features.drawdown_lookback_days`, Default 365) statt Full-History.
- Reversal-Base-Bewertung verwendet ausschließlich `base_score` aus der FeatureEngine (keine separate ATR-Bucket-Base-Logik mehr im Scorer).
- Momentum in Breakout/Pullback nutzt kontinuierliche Skalierung `clamp((r_7 / 10) * 100, 0, 100)` statt diskreter Sprünge.
- Relevante Scoring-Schwellen/Penalties wurden in Config-Strukturen überführt.

#### Warum?
- Behebung der dokumentierten Critical Findings für mathematische Konsistenz und konfigurierbares Verhalten.

#### Kompatibilität
- **Rückwärtskompatibel?** Teilweise (Feldnamen gleich, aber Werte/Interpretation ändern sich semantisch).
- Betroffen: Alle Consumer, die `drawdown_from_ath`, Reversal-Base-Scoring oder Momentum-Komponenten historisch vergleichen.

#### Migration / Vorgehen
- Für Zeitreihenvergleiche alte Läufe als `schema_version=v1.2` behandeln.
- Neue Läufe als `schema_version=v1.3` kennzeichnen; Metriken nicht direkt über Versionen mischen.

#### Beispiel (kurz)
```json
{
  "schema_version": "v1.3",
  "features": {
    "drawdown_from_ath": -12.4,
    "base_score": 67.8
  }
}
```


### 2026-02-19 — schema_version v1.3 → v1.4 — Global Top20 + Liquidity-Metriken im Report
**PR:** (branch-local, v2 Ticketfolge T1/T2/T3 Cleanup)  
**Typ:** additiv

#### Was hat sich geändert?
- Report-Schema in JSON erweitert um:
  - `summary.global_top20_count`
  - `setups.global_top20[]`
- Setup-Einträge enthalten zusätzliche Liquidity-Felder:
  - `proxy_liquidity_score`
  - `spread_bps`
  - `slippage_bps`
  - `liquidity_grade`
  - `liquidity_insufficient`
- Meta-Version für JSON-Reports angehoben auf `1.4`.

#### Warum?
- Globales Ranking und Liquidity/Tradeability-Transparenz sind zentrale v2-Anforderungen und müssen schema-seitig nachvollziehbar versioniert sein.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additive Felder).
- Bestehende Consumer bleiben funktionsfähig, sofern unbekannte Felder toleriert werden.

#### Migration / Vorgehen
- Consumer können über `meta.version` zwischen alten/newen Reports unterscheiden.
- Für ältere Reports (<=`1.3`) sind `global_top20` und Liquidity-Felder ggf. nicht vorhanden und sollten optional gelesen werden.

#### Beispiel (kurz)
```json
{
  "meta": {"version": "1.4"},
  "summary": {"global_top20_count": 20},
  "setups": {
    "global_top20": [{"symbol": "ABCUSDT", "rank": 1}],
    "breakouts": [{"symbol": "XYZUSDT", "slippage_bps": 18.2}]
  }
}
```

### 2026-02-20 — schema_version v1.4 → v1.5 — Trade Levels Output je Setup
**PR:** (branch-local, v2 Ticket T5.1)  
**Typ:** additiv

#### Was hat sich geändert?
- Setup-Outputs (`reversals`, `breakouts`, `pullbacks`, damit implizit auch `global_top20` wenn der best-setup Eintrag gewählt wird) enthalten nun:
  - `analysis.trade_levels`
- Deterministische Inhalte je Setup:
  - Breakout: `breakout_level_20`, `entry_trigger`, `invalidation`, `targets`
  - Pullback: `entry_zone` (center/lower/upper/tolerance), `invalidation`, `targets`
  - Reversal: `entry_trigger`, `invalidation`, `targets`
- JSON-Report `meta.version` wurde auf `1.5` erhöht.

#### Warum?
- Canonical-v2 Ticket T5.1 fordert deterministische Trade Levels als reinen Output ohne Ranking-/Score-Auswirkung.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additive Felder).

#### Migration / Vorgehen
- Consumer sollen `analysis` als optionales Objekt behandeln.
- Alte Reports (`<=1.4`) können `analysis.trade_levels` fehlen lassen.

#### Beispiel (kurz)
```json
{
  "meta": {"version": "1.5"},
  "setups": {
    "breakouts": [
      {
        "symbol": "ABCUSDT",
        "analysis": {
          "trade_levels": {
            "breakout_level_20": 1.234,
            "targets": [1.26, 1.29, 1.31]
          }
        }
      }
    ]
  }
}
```
