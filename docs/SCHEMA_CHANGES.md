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

### 2026-02-28 — dataset_schema_version 1.1 → 1.2 — Evaluation Export run_id millisecond uniqueness
**PR:** (branch-local, ticket/exporter_run_id_uniqueness_nanosecond_or_suffix)  
**Typ:** semantisch

#### Was hat sich geändert?
- Evaluation-Dataset-Exporter erhöht `dataset_schema_version` auf `"1.2"`.
- Default-`run_id` wird aus UTC-Startzeit mit Sekunden + Millisekunden abgeleitet (`YYYY-MM-DD_HHMMSSZ_mmm`).
- Meta-Record enthält zusätzlich `export_started_at_ts_ms` (UTC Epoch-Millis des Exportstarts).

#### Warum?
- Verhindert Dateiname- und `record_id`-Namespace-Kollisionen bei mehreren Exports innerhalb derselben Minute.

#### Kompatibilität
- **Rückwärtskompatibel?** Teilweise.
- Consumer mit starrer Regex/Parsing auf altes `run_id`-Muster (`YYYY-MM-DD_HHMMZ`) müssen das neue Suffix-Format akzeptieren.

#### Migration / Vorgehen
- Version via `dataset_schema_version` prüfen.
- Bei `>=1.2` `run_id` als opaken String behandeln (nicht auf Minutenauflösung hart parsen).
- Optional `export_started_at_ts_ms` als präzise Startzeitquelle nutzen.

#### Beispiel (kurz)
```json
{
  "type": "meta",
  "run_id": "2026-02-27_151233Z_482",
  "export_started_at_ts_ms": 1772205153482,
  "dataset_schema_version": "1.2"
}
```

### 2026-02-27 — dataset_schema_version 1.0 → 1.1 — Evaluation Dataset run_id file-scope + nullable Hits
**PR:** (branch-local, ticket/2026-02-27__02_P0__evaluation_dataset_run_id_and_hits_consistency)  
**Typ:** semantisch

#### Was hat sich geändert?
- Evaluation-Dataset-Exporter erhöht `dataset_schema_version` auf `"1.1"`.
- `run_id` wird standardmäßig einmalig aus Exportzeit (`UTC now`) erzeugt und als file-scope Kennung für alle Zeilen verwendet.
- Meta-Record enthält zusätzliche Felder `export_run_id` und `source_snapshot_dates`.
- E2-Hitfelder bleiben nullable (`hit_10`, `hit_20`, `hits[*]`) und werden nicht mehr auf `false` coerced.

#### Warum?
- Mehrtages-Exporte in einer JSONL benötigen einen stabilen, dateiunabhängigen `run_id` für konsistente `record_id`s.
- Unevaluable-Fälle (`insufficient_forward_history`) müssen semantisch `null` statt `false` abbilden.

#### Kompatibilität
- **Rückwärtskompatibel?** Teilweise.
- Consumer mit harter Annahme `dataset_schema_version == "1.0"` oder non-null booleans für `hit_*` müssen angepasst werden.

#### Migration / Vorgehen
- Version via `dataset_schema_version` prüfen.
- Bei `>=1.1`: `hit_10`/`hit_20` als nullable booleans behandeln und `null` als „nicht evaluierbar“ interpretieren.
- `run_id` als file-scope behandeln; optional `export_run_id` als Alias lesen.

#### Beispiel (kurz)
```json
{
  "type": "candidate_setup",
  "hit_10": null,
  "hit_20": null,
  "hits": {"10": null, "20": null}
}
```

### 2026-02-27 — Snapshot-Meta v1.0 → v1.1 — `meta.btc_regime` persistiert
**PR:** (branch-local, ticket/2026-02-27__02_P1__snapshot_persist_btc_regime_version_1_1)  
**Typ:** additiv

#### Was hat sich geändert?
- Snapshot-Metadaten wurden von `meta.version: "1.0"` auf `"1.1"` erhöht.
- Neues optionales Feld in Snapshot-Meta: `meta.btc_regime`.
- Pipeline übergibt das bereits deterministisch berechnete `btc_regime` unverändert in die Snapshot-Persistenz.

#### Warum?
- Offline-Reproduzierbarkeit und nachgelagerte Dataset-Exporte benötigen `btc_regime` direkt im Snapshot, ohne zusätzliche API-Calls oder Re-Computing.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja.
- Alte Snapshots ohne `meta.btc_regime` bleiben gültig und lesbar; Consumer müssen das Feld optional behandeln.

#### Migration / Vorgehen
- Neue Snapshots über `meta.version == "1.1"` erkennen.
- Bei älteren Snapshots (`1.0`) `meta.btc_regime` als `null`/fehlend behandeln.

#### Beispiel (kurz)
```json
{
  "meta": {
    "version": "1.1",
    "btc_regime": {
      "state": "RISK_ON"
    }
  }
}
```

### 2026-02-26 — schema_version v1.8 → v1.9 — Discovery-Outputfelder versioniert + Snapshot-Scoring abgesichert
**PR:** (branch-local, ticket/schema_versioning_and_scoring_snapshot_docs)  
**Typ:** additiv

#### Was hat sich geändert?
- JSON-Reports sind auf `schema_version: v1.9` / `meta.version: 1.9` angehoben.
- Discovery-Felder in Setup-Outputs sind damit explizit versioniert:
  - `discovery`
  - `discovery_age_days`
  - `discovery_source`
- GPT Snapshot Build (`.github/workflows/generate-gpt-snapshot.yml`) inkludiert Canonical-Scoring-Dokumente explizit, damit Snapshot-Scoring-Regeln aus `docs/canonical/*` stammen.

#### Warum?
- Neue Discovery-Outputfelder benötigen einen klaren Schema-Bump inkl. Changelog.
- Snapshot-Workflows sollen keine fachlichen Scoring-Inhalte verlieren.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additive Felder; bestehende Felder bleiben erhalten).
- Consumer sollten `schema_version` für Contract-Gating verwenden.

#### Migration / Vorgehen
- Bei Versionserkennung `schema_version >= v1.9` als Discovery-contract-stabil behandeln.
- Snapshot-Consumer können Scoring-Regeln weiterhin aus `docs/GPT_SNAPSHOT.md` extrahieren.

#### Beispiel (kurz)
```json
{
  "schema_version": "v1.9",
  "meta": {"version": "1.9"},
  "setups": {
    "reversals": [
      {
        "symbol": "ABCUSDT",
        "discovery": true,
        "discovery_age_days": 30,
        "discovery_source": "cmc_date_added"
      }
    ]
  }
}
```

### 2026-02-22 — schema_version v1.7 → v1.8 — `btc_regime` dokumentiert + Top-N-Limits für Breakout-Listen vereinheitlicht
**PR:** (branch-local, v2 Ticket PR7)  
**Typ:** additiv

#### Was hat sich geändert?
- JSON-Reports sind jetzt auf `schema_version: v1.8` / `meta.version: 1.8` angehoben.
- Top-Level-Feld `btc_regime` ist als Report-Vertrag explizit dokumentiert (`state`, `multiplier_risk_on`, `multiplier_risk_off`, `checks.close_gt_ema50`, `checks.ema20_gt_ema50`).
- Setup-Listen `setups.breakout_immediate_1_5d[]` und `setups.breakout_retest_1_5d[]` respektieren nun konsistent `output.top_n_per_setup` statt eines Hardcodes auf 20.

#### Warum?
- `btc_regime` wurde als neues Top-Level-Feld eingeführt und benötigt einen klar versionierten Contract.
- Konfigurationsvertrag für Reports (`top_n_per_setup`) muss für alle Setup-Listen einheitlich gelten.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additive Versionserhöhung; Feldstruktur bleibt stabil).
- Consumer sollten Version `v1.8` erkennen und die Breakout-Listenlänge nicht mehr als implizit 20 annehmen.

#### Migration / Vorgehen
- Für Legacy-Consumer mit fester Erwartung `==20` die Auswertung auf `<= configured top_n_per_setup` umstellen.
- Für Contract-Gating `schema_version` verwenden.

#### Beispiel (kurz)
```json
{
  "schema_version": "v1.8",
  "meta": {"version": "1.8"},
  "btc_regime": {
    "state": "RISK_OFF",
    "multiplier_risk_on": 1.0,
    "multiplier_risk_off": 0.85,
    "checks": {"close_gt_ema50": false, "ema20_gt_ema50": true}
  }
}
```

### 2026-02-22 — schema_version v1.6 → v1.7 — Breakout 1–5D Reporting erweitert (Immediate/Retest)
**PR:** (branch-local, v2 Ticket PR5)  
**Typ:** additiv

#### Was hat sich geändert?
- JSON-Report erweitert um zwei explizite Setup-Listen:
  - `setups.breakout_immediate_1_5d[]`
  - `setups.breakout_retest_1_5d[]`
- Markdown-Report ergänzt um zwei separate Breakout-Abschnitte:
  - `Top 20 Immediate (1–5D)`
  - `Top 20 Retest (1–5D)`
- Excel-Workbook ergänzt um separates Retest-Sheet (`Breakout Retest 1-5D`) und Immediate-Sheet-Ausweisung (`Breakout Immediate 1-5D`).
- Meta-Version für JSON-Reports angehoben auf `1.7`.

#### Warum?
- PR5 fordert die explizite Trennung der Breakout-Varianten im Reporting sowie die Schema-Versionierung dieser Erweiterung.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additive Felder/Sheets; bestehende Schlüssel bleiben erhalten).

#### Migration / Vorgehen
- Consumer können weiterhin `setups.breakouts` lesen; für v2-Breakout-Analysen sollten bevorzugt die neuen Setup-IDs gelesen werden.

#### Beispiel (kurz)
```json
{
  "schema_version": "v1.7",
  "meta": {"version": "1.7"},
  "setups": {
    "breakout_immediate_1_5d": [{"symbol": "AAAUSDT", "rank": 1}],
    "breakout_retest_1_5d": [{"symbol": "BBBUSDT", "rank": 1}]
  }
}
```

### 2026-02-20 — schema_version v1.5 → v1.6 — Explizites Top-Level-Feld `schema_version` im JSON-Report
**PR:** (branch-local, v2 Ticket C8 / PR8)  
**Typ:** additiv

#### Was hat sich geändert?
- JSON-Report enthält jetzt ein explizites Top-Level-Feld `schema_version`.
- `meta.version` wurde von `1.5` auf `1.6` erhöht.
- Versionswerte werden zentral über `scanner/schema.py` gepflegt.

#### Warum?
- Canonical-v2 fordert ein klar sichtbares, explizites `schema_version`-Feld im finalen Output für Governance und Consumer-Kompatibilität.

#### Kompatibilität
- **Rückwärtskompatibel?** Ja (additives Feld; bestehende Felder bleiben erhalten).

#### Migration / Vorgehen
- Consumer sollten bevorzugt `schema_version` für Format-Gating verwenden.
- Ältere Reports (`<=v1.5`) können ohne `schema_version` vorliegen und sollten defensiv behandelt werden.

#### Beispiel (kurz)
```json
{
  "schema_version": "v1.6",
  "meta": {"version": "1.6"}
}
```

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
