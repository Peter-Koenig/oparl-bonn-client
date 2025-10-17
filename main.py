"""
Hauptskript für den OParl-Client des Bonner Ratsinformationssystems

Dieses Skript bietet eine einfache Kommandozeilenschnittstelle für den Abruf
von Meetings aus der OParl-API.
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

# Import der Client-Klassen
try:
    from src.oparl_client import OParlClient
    from src.oparl_client_advanced import OParlClientAdvanced
except ImportError:
    # Fallback für direkte Ausführung
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.oparl_client import OParlClient
    from src.oparl_client_advanced import OParlClientAdvanced


def parse_arguments():
    """Parst die Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(
        description="OParl-Client für das Bonner Ratsinformationssystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py                         # Standard-Ausführung
  python main.py --advanced              # Erweiterte Version mit Progress Bar
  python main.py --end-date 2025-06-30   # Anderes Enddatum
  python main.py --no-cache              # Deaktiviere Caching
  python main.py --output ./data         # Anderes Ausgabeverzeichnis
        """,
    )

    parser.add_argument(
        "--base-url",
        default="https://www.bonn.sitzung-online.de/public/oparl",
        help="Basis-URL der OParl-API (Standard: %(default)s)",
    )

    parser.add_argument(
        "--end-date",
        default="2025-12-31",
        help="Enddatum für den Filter im Format YYYY-MM-DD (Standard: %(default)s)",
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Ausgabeverzeichnis für Dateien (Standard: %(default)s)",
    )

    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Cache-Verzeichnis für API-Antworten (Standard: %(default)s)",
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Wartezeit zwischen Requests in Sekunden (Standard: %(default)s)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximale Anzahl Wiederholungsversuche (Standard: %(default)s)",
    )

    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Verwende erweiterte Version mit Progress Bar",
    )

    parser.add_argument(
        "--no-cache", action="store_true", help="Deaktiviere Caching von API-Antworten"
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Deaktiviere Progress Bar (nur bei --advanced)",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Aktiviere detaillierte Log-Ausgabe"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Testmodus: Führt nur einen begrenzten Abruf durch",
    )

    return parser.parse_args()


def validate_arguments(args):
    """Validiert die Kommandozeilenargumente"""

    # Validiere Enddatum
    try:
        datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        print(
            f"Fehler: Ungültiges Datumsformat '{args.end_date}'. Erwartet: YYYY-MM-DD"
        )
        return False

    # Validiere numerische Werte
    if args.rate_limit < 0:
        print("Fehler: Rate-Limit muss >= 0 sein")
        return False

    if args.max_retries < 0:
        print("Fehler: Max-Retries muss >= 0 sein")
        return False

    # Validiere Verzeichnisse
    try:
        output_path = Path(args.output_dir)
        cache_path = Path(args.cache_dir)

        # Versuche Verzeichnisse zu erstellen
        output_path.mkdir(exist_ok=True, parents=True)
        cache_path.mkdir(exist_ok=True, parents=True)

    except (OSError, PermissionError) as e:
        print(f"Fehler beim Erstellen der Verzeichnisse: {e}")
        return False

    return True


def print_banner():
    """Gibt einen Willkommens-Banner aus"""
    print("\n" + "=" * 60)
    print("OPARL-CLIENT - BONNER RATSINFORMATIONSSYSTEM")
    print("=" * 60)
    print(f"Ausführungszeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


def run_standard_client(args):
    """Führt den Standard-Client aus"""
    print("🚀 Starte Standard-Client...")

    client = OParlClient(
        base_url=args.base_url,
        end_date=args.end_date,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        rate_limit=args.rate_limit,
        max_retries=args.max_retries,
    )

    return client.run()


def run_advanced_client(args):
    """Führt den erweiterten Client aus"""
    print("🚀 Starte Erweiterten Client...")

    client = OParlClientAdvanced(
        base_url=args.base_url,
        end_date=args.end_date,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        rate_limit=args.rate_limit,
        max_retries=args.max_retries,
        enable_progress_bar=not args.no_progress,
        enable_caching=not args.no_cache,
        enable_statistics=True,
    )

    return client.run()


def test_mode(args):
    """Führt einen Test-Abruf durch"""
    print("🧪 TESTMODUS - Begrenzter Abruf")

    # Verwende erweiterten Client für bessere Kontrolle
    client = OParlClientAdvanced(
        base_url=args.base_url,
        end_date=args.end_date,
        output_dir=args.output_dir + "_test",
        cache_dir=args.cache_dir + "_test",
        rate_limit=args.rate_limit,
        max_retries=args.max_retries,
        enable_progress_bar=True,
        enable_caching=False,  # Kein Caching im Testmodus
        enable_statistics=True,
    )

    # Rufe nur erste Seite ab
    print("Test: Rufe erste Seite der Meetings ab...")
    try:
        test_url = f"{args.base_url}/meetings?body=1&page=1"
        response = client.session.get(test_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        meetings_count = len(data.get("data", []))

        print(f"✅ Test erfolgreich: {meetings_count} Meetings auf Seite 1 gefunden")
        print(f"📊 API-Response-Struktur: {list(data.keys())}")

        if meetings_count > 0:
            sample_meeting = data["data"][0]
            print(f"📅 Beispiel-Meeting: {sample_meeting.get('name', 'Unbekannt')}")
            print(f"🕐 Start: {sample_meeting.get('start', 'Unbekannt')}")

        return True

    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        return False


def main():
    """Hauptfunktion"""
    args = parse_arguments()

    # Validiere Argumente
    if not validate_arguments(args):
        sys.exit(1)

    # Banner anzeigen
    print_banner()

    # Testmodus
    if args.test:
        success = test_mode(args)
        sys.exit(0 if success else 1)

    # Hauptausführung
    try:
        start_time = time.time()

        if args.advanced:
            success = run_advanced_client(args)
        else:
            success = run_standard_client(args)

        duration = time.time() - start_time
        print(f"\n⏱️  Gesamtdauer: {duration:.2f} Sekunden")

        if success:
            print("\n✅ Abruf erfolgreich abgeschlossen!")
        else:
            print("\n⚠️  Abruf mit Warnungen abgeschlossen")

    except KeyboardInterrupt:
        print("\n\n⏹️  Abruf durch Benutzer abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unbehandelter Fehler: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
