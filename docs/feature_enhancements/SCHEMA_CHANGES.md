# SCHEMA_CHANGES.md – Schema-/Output‑Änderungslog (verbindlich)

Dieses Dokument protokolliert alle Änderungen an:
- Report‑Schema (`reports/*.json` / `.md`)
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
