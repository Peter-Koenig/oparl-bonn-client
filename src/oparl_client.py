"""
Robuster Python-Client für die OParl-API des Bonner Ratsinformationssystems
"""

import requests
import logging
import json
import csv
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path


class OParlClient:
    """
    Client für die OParl-API des Bonner Ratsinformationssystems
    """

    def __init__(
        self,
        base_url: str = "https://www.bonn.sitzung-online.de/public/oparl",
        end_date: str = "2025-12-31",
        output_dir: str = "output",
        cache_dir: str = "cache",
        rate_limit: float = 1.0,
        max_retries: int = 3,
    ):
        """
        Initialisiert den OParl-Client

        Args:
            base_url: Basis-URL der OParl-API
            end_date: Enddatum für den Filter (YYYY-MM-DD)
            output_dir: Verzeichnis für Ausgabedateien
            cache_dir: Verzeichnis für Cache-Dateien
            rate_limit: Wartezeit zwischen Requests in Sekunden
            max_retries: Maximale Anzahl Wiederholungsversuche bei Fehlern
        """
        self.base_url = base_url
        self.end_date = end_date
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.rate_limit = rate_limit
        self.max_retries = max_retries

        # Erstelle Verzeichnisse falls nicht vorhanden
        self.output_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # Setup Logging
        self._setup_logging()

        # Session für persistente Verbindung
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "OParl-Client/1.0", "Accept": "application/json"}
        )

        # Statistik-Zähler
        self.stats = {
            "total_meetings": 0,
            "total_pages": 0,
            "api_requests": 0,
            "errors": 0,
        }

        self.logger.info(f"OParl-Client initialisiert für {base_url}")
        self.logger.info(f"Filtere Meetings bis {end_date}")

    def _setup_logging(self):
        """Konfiguriert das Logging-System"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.output_dir / "oparl_client.log"),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def _make_request(self, url: str, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Führt einen HTTP-Request mit Retry-Mechanismus durch

        Args:
            url: Die angefragte URL
            page: Seitenzahl für Logging

        Returns:
            JSON-Daten oder None bei Fehler
        """
        for attempt in range(self.max_retries):
            try:
                # Rate Limiting
                if self.stats["api_requests"] > 0:
                    time.sleep(self.rate_limit)

                self.logger.debug(f"Request an {url} (Versuch {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                self.stats["api_requests"] += 1
                return response.json()

            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout bei Seite {page}, Versuch {attempt + 1}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(
                    f"Verbindungsfehler bei Seite {page}, Versuch {attempt + 1}"
                )
            except requests.exceptions.HTTPError as e:
                self.logger.error(
                    f"HTTP-Fehler {response.status_code} bei Seite {page}: {e}"
                )
                if response.status_code in [400, 404, 500]:
                    break  # Keine Wiederholung bei diesen Fehlern
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request-Fehler bei Seite {page}: {e}")
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON-Parsing-Fehler bei Seite {page}: {e}")
                break  # Keine Wiederholung bei JSON-Fehlern

            # Exponential Backoff
            if attempt < self.max_retries - 1:
                wait_time = (2**attempt) * 5
                self.logger.info(f"Warte {wait_time}s vor Wiederholung...")
                time.sleep(wait_time)

        self.stats["errors"] += 1
        return None

    def _filter_meetings_by_date(self, meetings: List[Dict]) -> List[Dict]:
        """
        Filtert Meetings basierend auf dem Enddatum

        Args:
            meetings: Liste der Meetings

        Returns:
            Gefilterte Liste der Meetings
        """
        filtered_meetings = []
        end_date_obj = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        for meeting in meetings:
            start_str = meeting.get("start")
            if not start_str:
                continue

            try:
                # Extrahiere Datum aus ISO 8601 String
                meeting_date = datetime.fromisoformat(
                    start_str.replace("Z", "+00:00")
                ).date()
                if meeting_date <= end_date_obj:
                    filtered_meetings.append(meeting)
            except (ValueError, AttributeError) as e:
                self.logger.warning(f"Ungültiges Datum-Format '{start_str}': {e}")
                continue

        return filtered_meetings

    def _extract_meeting_data(self, meeting: Dict) -> Dict[str, Any]:
        """
        Extrahiert relevante Daten aus einem Meeting-Objekt

        Args:
            meeting: Roh-Meeting-Daten

        Returns:
            Bereinigte Meeting-Daten
        """
        return {
            "id": meeting.get("id", ""),
            "name": meeting.get("name", ""),
            "start": meeting.get("start", ""),
            "end": meeting.get("end", ""),
            "location": meeting.get("location", ""),
            "organization": meeting.get("organization", ""),
            "created": meeting.get("created", ""),
            "modified": meeting.get("modified", ""),
        }

    def get_all_meetings(self) -> List[Dict[str, Any]]:
        """
        Ruft alle Meetings bis zum Enddatum ab

        Returns:
            Liste aller gefundenen Meetings
        """
        self.logger.info(f"Starte Abruf von Meetings bis {self.end_date}")

        all_meetings = []
        page = 1
        next_url = f"{self.base_url}/meetings?body=1&page={page}"

        while next_url:
            self.logger.info(f"Lade Seite {page}...")

            # Cache-Prüfung
            cache_file = self.cache_dir / f"page_{page}.json"
            if cache_file.exists():
                self.logger.info(f"Lade Seite {page} aus Cache")
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = self._make_request(next_url, page)
                if data is None:
                    break

                # Speichere im Cache
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            if not data or "data" not in data:
                self.logger.error(f"Ungültige Antwort-Struktur auf Seite {page}")
                break

            meetings = data["data"]
            filtered_meetings = self._filter_meetings_by_date(meetings)

            all_meetings.extend(filtered_meetings)
            self.stats["total_pages"] = page
            self.stats["total_meetings"] = len(all_meetings)

            self.logger.info(
                f"Seite {page}: {len(meetings)} Meetings gefunden, {len(filtered_meetings)} passen zum Filter"
            )

            # Nächste Seite prüfen
            links = data.get("links", {})
            next_url = links.get("next")
            page += 1

            # Abbruch wenn keine weiteren Seiten oder alle Meetings nach Enddatum
            if not next_url or not filtered_meetings:
                break

        # Entferne Duplikate basierend auf ID
        unique_meetings = []
        seen_ids = set()
        for meeting in all_meetings:
            meeting_id = meeting.get("id")
            if meeting_id and meeting_id not in seen_ids:
                seen_ids.add(meeting_id)
                unique_meetings.append(meeting)

        self.logger.info(
            f"Abruf abgeschlossen: {len(unique_meetings)} eindeutige Meetings gefunden"
        )
        return unique_meetings

    def export_to_csv(self, meetings: List[Dict], filename: str = "meetings.csv"):
        """
        Exportiert Meetings als CSV-Datei

        Args:
            meetings: Liste der Meetings
            filename: Name der CSV-Datei
        """
        filepath = self.output_dir / filename

        if not meetings:
            self.logger.warning("Keine Meetings zum Exportieren vorhanden")
            return

        fieldnames = [
            "id",
            "name",
            "start",
            "end",
            "location",
            "organization",
            "created",
            "modified",
        ]

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for meeting in meetings:
                    extracted = self._extract_meeting_data(meeting)
                    writer.writerow(extracted)

            self.logger.info(f"CSV-Export abgeschlossen: {filepath}")
        except Exception as e:
            self.logger.error(f"Fehler beim CSV-Export: {e}")

    def export_to_json(self, meetings: List[Dict], filename: str = "meetings.json"):
        """
        Exportiert Meetings als JSON-Datei

        Args:
            meetings: Liste der Meetings
            filename: Name der JSON-Datei
        """
        filepath = self.output_dir / filename

        if not meetings:
            self.logger.warning("Keine Meetings zum Exportieren vorhanden")
            return

        try:
            extracted_meetings = [
                self._extract_meeting_data(meeting) for meeting in meetings
            ]

            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "source": self.base_url,
                    "end_date_filter": self.end_date,
                    "total_meetings": len(meetings),
                },
                "meetings": extracted_meetings,
            }

            with open(filepath, "w", encoding="utf-8") as jsonfile:
                json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)

            self.logger.info(f"JSON-Export abgeschlossen: {filepath}")
        except Exception as e:
            self.logger.error(f"Fehler beim JSON-Export: {e}")

    def print_statistics(self, meetings: List[Dict]):
        """
        Gibt Statistiken zum Abruf aus

        Args:
            meetings: Liste der Meetings
        """
        if not meetings:
            self.logger.info("Keine Meetings für Statistik vorhanden")
            return

        # Finde Zeitraum
        dates = []
        for meeting in meetings:
            start_str = meeting.get("start")
            if start_str:
                try:
                    meeting_date = datetime.fromisoformat(
                        start_str.replace("Z", "+00:00")
                    ).date()
                    dates.append(meeting_date)
                except (ValueError, AttributeError):
                    continue

        if dates:
            min_date = min(dates)
            max_date = max(dates)
            time_range = f"{min_date} bis {max_date}"
        else:
            time_range = "Unbekannt"

        self.logger.info("=" * 50)
        self.logger.info("STATISTIKEN")
        self.logger.info("=" * 50)
        self.logger.info(f"Abgerufene Meetings: {len(meetings)}")
        self.logger.info(f"Seiten durchsucht: {self.stats['total_pages']}")
        self.logger.info(f"API-Requests: {self.stats['api_requests']}")
        self.logger.info(f"Fehler: {self.stats['errors']}")
        self.logger.info(f"Zeitraum: {time_range}")
        self.logger.info("=" * 50)

    def run(self):
        """
        Führt den kompletten Abruf und Export durch
        """
        start_time = time.time()

        try:
            # Abruf der Meetings
            meetings = self.get_all_meetings()

            # Export
            self.export_to_csv(meetings)
            self.export_to_json(meetings)

            # Statistik
            self.print_statistics(meetings)

            # Gesamtdauer
            duration = time.time() - start_time
            self.logger.info(f"Gesamtdauer: {duration:.2f} Sekunden")

        except Exception as e:
            self.logger.error(f"Unbehandelter Fehler während der Ausführung: {e}")
            raise


def main():
    """
    Hauptfunktion für direkte Ausführung
    """
    client = OParlClient()
    client.run()


if __name__ == "__main__":
    main()
