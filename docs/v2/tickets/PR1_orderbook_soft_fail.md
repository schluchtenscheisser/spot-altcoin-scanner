# PR1 — Orderbook Top-K: pro Symbol soft-fail (kein Pipeline-Crash)

## Problem
Aktuell ruft `scanner/pipeline/liquidity.py:fetch_orderbooks_for_top_k()` für jedes Top-K Symbol `mexc_client.get_orderbook(symbol)` auf.
`mexc_client.get_orderbook()` kann nach Retries eine Exception werfen.
Dadurch kann EIN kaputtes Symbol den gesamten Run abbrechen.

## Ziel
- Pipeline darf NICHT crashen, wenn einzelne Orderbook-Calls fehlschlagen.
- Für betroffene Symbole soll `orderbooks[symbol]` auf `None` bleiben.
- Es soll ein `logger.warning(...)` pro betroffenem Symbol geben (mit Exception-Info).
- Format bleibt unverändert: `orderbooks` enthält Keys für alle candidates; nur Top-K wird versucht zu fetchen; Non-Top-K bleibt `None`.

## Nicht-Ziele
- Keine Änderung am Budget-Verhalten (max. K Calls).
- Keine Änderung an der Struktur/Keys von `orderbooks`.
- Keine Änderung an mexc_client Retry-Strategie (nur Call-Site absichern).

## Fundstellen
- scanner/pipeline/liquidity.py
  - fetch_orderbooks_for_top_k(...)
- scanner/clients/mexc_client.py
  - get_orderbook(...)

## Implementationshinweise
- Umhülle den get_orderbook Call pro Symbol mit try/except Exception.
- Bei Exception:
  - logger.warning("Orderbook fetch failed for %s: %s", symbol, exc, exc_info=True)
  - `orderbooks[symbol]` bleibt None (nicht überschreiben)
- Achte darauf, dass die Anzahl der Calls weiterhin genau K ist (für Symbole, die versucht werden; auch wenn sie fehlschlagen).

## Neue Tests (Test-first)
Erweitere/ergänze Tests in `tests/test_t82_topk_budget.py` oder neuer Testfile:
- Arrange:
  - Dummy mexc_client, dessen `get_orderbook()` für ein bestimmtes Symbol Exception wirft, für ein anderes erfolgreich ist.
  - candidates >= top_k
- Assert:
  - Funktion gibt dict mit Keys für alle candidates zurück.
  - Für das fehlschlagende Top-K Symbol ist value None.
  - Für das erfolgreiche Top-K Symbol ist value nicht None.
  - Non-Top-K Symbole bleiben None.
  - Anzahl `get_orderbook()` Calls == top_k (die Versuche zählen, auch wenn Exception).

## Akzeptanzkriterien
- Alle Tests grün: `python -m pytest -q`
- Kein Crash bei Exception in Orderbook-Fetch.
- Keine Änderung an Output-Formaten außer Logging.
