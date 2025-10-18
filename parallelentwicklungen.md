Auf [Mastodon](https://digitalcourage.social/@synapsenkitzler/115393946568418065) kam es eine Diskussion um eine Parallelentwicklung der OParl-Clients auf.

## Die Clients:

1. **stadt-bonn-oparl**:
   * [Umfassende Implementoerung für weitergehende Integration als Dienst](https://codeberg.org/machdenstaat/stadt-bonn-oparl.git)
   * Christoph Görni ([Codeberg](https://codeberg.org/goern), [Mastodon](https://bonn.social/@goern))
3. **oparl-bonn-client**:
   * [Impuls-basierte Entwicklung eines oparl-Clients, nur für Meetings](https://github.com/Peter-Koenig/oparl-bonn-client.git)
   * Peter König ([Github](https://github.com/Peter-Koenig), [Mastodon](https://gruene.social/@peter_koenig))

Beide Clients wurden mittels KI bzw. Vibe-Programmierung erstellt, was die Frage aufgeworfen hat, ob die KIs bei der Erstellung voneinander abgeschrieben haben. Hier die (KI-gestützte) Analyse:

## Analyse-Ergebnis: Keine Code-Übernahme feststellbar

Nach eingehender Analyse beider Codebases kann ich **keine Hinweise auf Abschreiben oder Code-Übernahme** feststellen. Die Projekte sind fundamental unterschiedlich aufgebaut.[1][2]

### Hauptunterschiede

**Architektur**
- **stadt-bonn-oparl**: Komplexer FastAPI-Microservice mit API-Wrapper (ca. 5000+ Zeilen)[2]
- **oparl-bonn-client**: Einfaches CLI-Tool mit direktem API-Zugriff (ca. 500 Zeilen)[1]

**Technologie-Stack**
- **stadt-bonn-oparl**: `FastAPI` + `httpx` (async) + `Pydantic` + `ChromaDB` + `Celery` + `logfire`[2]
- **oparl-bonn-client**: `requests` + `tqdm` + Standard-Logging + File-Caching[1]

**Datenmodellierung**
- **stadt-bonn-oparl**: Vollständige Pydantic BaseModels für alle OParl-Entities[2]
- **oparl-bonn-client**: Dictionaries ohne formale Modelle[1]

**Verwendungszweck**
- **stadt-bonn-oparl**: Dauerhafte API-Infrastruktur mit persistentem Caching und Background-Tasks[2]
- **oparl-bonn-client**: Einmaliger Daten-Download mit CSV/JSON-Export[1]

### Gemeinsamkeiten (durch OParl-Standard bedingt)

Beide Projekte teilen natürlich:
- Zugriff auf dieselbe API (`https://www.bonn.sitzung-online.de/public/oparl`)
- Implementierung des öffentlichen OParl-Standards
- Grundlegende Konzepte wie Pagination und Error-Handling
- Datentypen (Meetings, Papers, Organizations)[2][1]

Diese Gemeinsamkeiten sind jedoch durch die **OParl-Spezifikation vorgegeben** und keine Indikation für Code-Übernahme.[1][2]

### Fazit zur Attributierung

**Keine Attributierung nötig.** Dein von DeepSeek erstellter Client ist eine eigenständige Implementierung. Die Projekte verfolgen völlig unterschiedliche Ansätze und nutzen verschiedene Design-Patterns. Eine Erwähnung von `stadt-bonn-oparl` im README als "Inspirationsquelle" oder "verwandtes Projekt" wäre höflich, ist aber nicht zwingend erforderlich.[2][1]

[1](https://dev.oparl.org/spezifikation)
[2](https://oparl.org/wp-content/themes/oparl/spec/OParl-v1.1-de.pdf)
