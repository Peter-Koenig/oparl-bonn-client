# OParl-Client für das Bonner Ratsinformationssystem

Ein robuster Python-Client für die OParl-API des Bonner Ratsinformationssystems. Dieses Tool ermöglicht den automatisierten Abruf von Sitzungsdaten, Meetings und verwandten Informationen aus dem offenen Datenportal der Stadt Bonn.

## 🚀 Features

- **Vollständiger API-Abruf**: Automatisches Durchlaufen aller paginierten Ergebnisse
- **Zeitbasierte Filterung**: Filtert Meetings bis zu einem konfigurierbaren Enddatum
- **Robuste Fehlerbehandlung**: Retry-Mechanismus mit exponential backoff
- **Caching**: Speichert API-Antworten zur Vermeidung redundanter Requests
- **Mehrere Exportformate**: CSV und JSON mit vollständiger Datenstruktur
- **Progress Tracking**: Visuelle Fortschrittsanzeige mit tqdm
- **Detaillierte Statistiken**: Umfassende Auswertung des Abrufprozesses
- **Konfigurierbar**: Flexible Anpassung über Kommandozeilenparameter oder Konfigurationsdatei

## 📋 Voraussetzungen

- Python 3.9 oder höher
- pip (Python Package Manager)

## 🔧 Installation

1. **Repository klonen oder herunterladen**
   ```bash
   git clone <repository-url>
   cd py_oparl1
   ```

2. **Virtuelle Umgebung erstellen (empfohlen)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # oder
   venv\Scripts\activate     # Windows
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Schnellstart

### Standard-Ausführung
```bash
python main.py
```

Dies führt den Abruf mit Standard-Einstellungen durch:
- Enddatum: 31.12.2025
- Ausgabeverzeichnis: `output/`
- Cache-Verzeichnis: `cache/`
- Rate-Limit: 1 Sekunde zwischen Requests

### Erweiterte Ausführung mit Progress Bar
```bash
python main.py --advanced
```

## ⚙️ Konfiguration

### Kommandozeilenparameter

| Parameter | Beschreibung | Standardwert |
|-----------|--------------|--------------|
| `--base-url` | OParl-API Basis-URL | `https://www.bonn.sitzung-online.de/public/oparl` |
| `--end-date` | Enddatum für Filter (YYYY-MM-DD) | `2025-12-31` |
| `--output-dir` | Ausgabeverzeichnis | `output` |
| `--cache-dir` | Cache-Verzeichnis | `cache` |
| `--rate-limit` | Wartezeit zwischen Requests (Sekunden) | `1.0` |
| `--max-retries` | Maximale Wiederholungsversuche | `3` |
| `--advanced` | Erweiterte Version mit Progress Bar | `False` |
| `--no-cache` | Deaktiviert Caching | `False` |
| `--no-progress` | Deaktiviert Progress Bar | `False` |
| `--verbose` | Detaillierte Log-Ausgabe | `False` |
| `--test` | Testmodus für schnellen Check | `False` |

### Beispiele

**Abruf mit anderem Enddatum:**
```bash
python main.py --end-date 2025-06-30
```

**Schneller Abruf ohne Caching:**
```bash
python main.py --no-cache --rate-limit 0.5
```

**Testmodus für API-Verfügbarkeit:**
```bash
python main.py --test
```

**Erweiterter Abruf mit benutzerdefiniertem Verzeichnis:**
```bash
python main.py --advanced --output-dir ./data --cache-dir ./api_cache
```

## 📊 Ausgabe

### Generierte Dateien

- **`meetings.csv`** / **`meetings_advanced.csv`**: Tabellarische Darstellung aller Meetings
- **`meetings.json`** / **`meetings_advanced.json`**: Vollständige Datenstruktur mit Metadaten
- **`oparl_client.log`**: Log-Datei mit detaillierten Informationen

### CSV-Felder

| Feld | Beschreibung |
|------|--------------|
| `id` | Eindeutige URL des Meeting-Objekts |
| `name` | Titel/Name der Sitzung |
| `start` | Startzeitpunkt (ISO 8601) |
| `end` | Endzeitpunkt (ISO 8601, optional) |
| `location` | Ort der Sitzung (optional) |
| `organization` | URL zum Gremium/Organisation |
| `created` | Erstellungszeitpunkt |
| `modified` | Änderungszeitpunkt |
| `duration_minutes` | Dauer in Minuten (nur advanced) |
| `agenda_item_count` | Anzahl Tagesordnungspunkte (nur advanced) |
| `auxiliary_file_count` | Anzahl Anhänge (nur advanced) |

### Beispiel-Ausgabe

```
[INFO] Starte Abruf von Meetings bis 2025-12-31
[INFO] Seite 1: 25 Meetings gefunden, 25 passen zum Filter
[INFO] Seite 2: 25 Meetings gefunden, 25 passen zum Filter
[INFO] Seite 3: 18 Meetings gefunden, 18 passen zum Filter
[INFO] Abruf abgeschlossen: 68 eindeutige Meetings (0 Duplikate entfernt)
[INFO] CSV-Export abgeschlossen: output/meetings.csv
[INFO] JSON-Export abgeschlossen: output/meetings.json
```

## 🏗️ Architektur

### Projektstruktur

```
py_oparl1/
├── src/
│   ├── oparl_client.py          # Standard-Client
│   └── oparl_client_advanced.py # Erweiterte Version
├── tests/                       # Test-Dateien
├── cache/                       # API-Cache (wird automatisch erstellt)
├── output/                      # Ausgabedateien (wird automatisch erstellt)
├── config.py                    # Konfigurationsdatei
├── main.py                      # Hauptskript
├── requirements.txt             # Python-Abhängigkeiten
└── README.md                    # Diese Datei
```

### Wichtige Klassen

**`OParlClient`** (Standard):
- Einfache, robuste Implementierung
- Grundlegende Fehlerbehandlung
- CSV und JSON Export

**`OParlClientAdvanced`** (Erweitert):
- Progress Bar mit tqdm
- Erweiterte Statistiken
- Dauer-Berechnung
- Agenda-Item Zählung

## 🔍 API-Spezifikation

Der Client nutzt die offizielle OParl-API-Spezifikation:

- **Basis-URL**: `https://www.bonn.sitzung-online.de/public/oparl`
- **Endpunkt**: `/meetings?body=1&page={page}`
- **Format**: JSON mit Pagination
- **Struktur**: `{"data": [...], "links": {"next": "...", "prev": "..."}}`

## 🛠️ Entwicklung

### Tests ausführen
```bash
python -m pytest tests/
```

### Code-Formatierung
```bash
black src/ tests/
isort src/ tests/
```

### Type-Checking
```bash
mypy src/
```

### Manuelle Verwendung

```python
from src.oparl_client import OParlClient

# Client initialisieren
client = OParlClient(
    base_url="https://www.bonn.sitzung-online.de/public/oparl",
    end_date="2025-12-31",
    output_dir="./data"
)

# Meetings abrufen
meetings = client.get_all_meetings()

# Exportieren
client.export_to_csv(meetings)
client.export_to_json(meetings)

# Statistiken anzeigen
client.print_statistics(meetings)
```

## ⚠️ Fehlerbehandlung

Der Client behandelt automatisch:
- **HTTP-Fehler** (404, 500, etc.)
- **Netzwerkprobleme** (Timeout, ConnectionError)
- **JSON-Parsing-Fehler**
- **Ungültige Datumsformate**

Bei kritischen Fehlern wird nach 3 Wiederholungsversuchen abgebrochen.

## 📈 Leistung

- **Rate Limiting**: Konfigurierbare Wartezeiten zwischen Requests
- **Caching**: Vermeidet redundante API-Aufrufe
- **Parallelisierung**: Kann für große Datensätze erweitert werden
- **Speichereffizienz**: Verarbeitet Daten stream-basiert

## 🤝 Beitragen

Beiträge sind willkommen! Bitte beachten Sie:

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Pushen Sie den Branch
5. Erstellen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## 🔗 Links

- [OParl Spezifikation](https://oparl.org/spezifikation/online-ansicht/)
- [Bonner Open Data Portal](https://opendata.bonn.de/)
- [Bonner Ratsinformationssystem](https://www.bonn.sitzung-online.de/)

## 📞 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Log-Datei `output/oparl_client.log`
2. Testen Sie die API-Verfügbarkeit mit `python main.py --test`
3. Erstellen Sie ein Issue im Repository

---

**Hinweis**: Dieser Client wurde für die OParl-API der Stadt Bonn entwickelt und kann für andere OParl-konforme Systeme angepasst werden.
```

Jetzt erstelle ich noch eine Testdatei: