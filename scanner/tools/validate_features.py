import json
import os

def validate_features(report_path: str):
    """
    Prüft, ob die im JSON-Report gespeicherten Feature- und Scoring-Werte
    numerisch, plausibel und nicht konstant sind.
    Unterstützt Reports mit 'setups', 'data' oder 'results' als Hauptsektion.
    """

    if not os.path.exists(report_path):
        print(f"❌ Report-Datei nicht gefunden: {report_path}")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dynamisch den richtigen Abschnitt im Report finden
    if "setups" in data:
        section_key = "setups"
    elif "data" in data:
        section_key = "data"
    elif "results" in data:
        section_key = "results"
    else:
        print("❌ Ungültiges Report-Format – keine 'setups', 'data' oder 'results'-Sektion gefunden.")
        return

    results = data[section_key]
    if not results:
        print("⚠️ Keine Ergebnisse im Report.")
        return

    anomalies = []

    for setup_type, setups in results.items():
        for s in setups:
            comps = s.get("components", {})
            for key, value in comps.items():
                # Prüfe auf None oder nicht-numerische Werte
                if value is None or not isinstance(value, (int, float)):
                    anomalies.append((setup_type, s.get("symbol"), key, value))
                # Prüfe auf unrealistische Werte
                elif not (0 <= value <= 150):
                    anomalies.append((setup_type, s.get("symbol"), key, value))

    if anomalies:
        print("⚠️ Anomalien gefunden:")
        for setup_type, symbol, key, value in anomalies:
            print(f"  [{setup_type}] {symbol}: {key} = {value}")
    else:
        print("✅ Alle Feature-Komponenten numerisch und plausibel.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("⚠️  Bitte Report-Dateipfad angeben, z. B.:")
        print("    python -m scanner.tools.validate_features reports/2026-01-22.json")
        sys.exit(1)

    report_path = sys.argv[1]
    validate_features(report_path)

