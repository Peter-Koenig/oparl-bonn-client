"""
Erweiterte Version des OParl-Clients mit Progress Bar und erweiterten Features
"""

import requests
import logging
import json
import csv
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warnung: tqdm nicht verfügbar. Installiere mit: pip install tqdm")


class OParlClientAdvanced:
    """
    Erweiterter Client für die OParl-API mit Progress Bar und erweiterten Features
    """

    def __init__(
        self,
        base_url: str = "https://www.bonn.sitzung-online.de/public/oparl",
        end_date: str = "2025-12-31",
        output_dir: str = "output",
        cache_dir: str = "cache",
        rate_limit: float = 1.0,
        max_retries: int = 3,
        enable_progress_bar: bool = True,
        enable_caching: bool = True,
        enable_statistics: bool = True,
    ):
        """
        Initialisiert den erweiterten OParl-Client

        Args:
            base_url: Basis-URL der OParl-API
            end_date: Enddatum für den Filter (YYYY-MM-DD)
            output_dir: Verzeichnis für Ausgabedateien
            cache_dir: Verzeichnis für Cache-Dateien
            rate_limit: Wartezeit zwischen Requests in Sekunden
            max_retries: Maximale Anzahl Wiederholungsversuche bei Fehlern
            enable_progress_bar: Aktiviert Progress Bar (falls tqdm verfügbar)
            enable_caching: Aktiviert Caching von API-Antworten
            enable_statistics: Aktiviert detaillierte Statistiken
        """
        self.base_url = base_url
        self.end_date = end_date
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.enable_progress_bar = enable_progress_bar and TQDM_AVAILABLE
        self.enable_caching = enable_caching
        self.enable_statistics = enable_statistics

        # Erstelle Verzeichnisse falls nicht vorhanden
        self.output_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # Setup Logging
        self._setup_logging()

        # Session für persistente Verbindung
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "OParl-Advanced-Client/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            }
        )

        # Erweiterte Statistik-Zähler
        self.stats = {
            "total_meetings": 0,
            "total_pages": 0,
            "api_requests": 0,
            "cached_requests": 0,
            "errors": 0,
            "filtered_meetings": 0,
            "duplicates_removed": 0,
            "start_time": None,
            "end_time": None,
        }

        self.logger.info(f"Erweiterter OParl-Client initialisiert für {base_url}")
        self.logger.info(f"Filtere Meetings bis {end_date}")
        if self.enable_progress_bar:
            self.logger.info("Progress Bar aktiviert")
        if self.enable_caching:
            self.logger.info("Caching aktiviert")

    def _setup_logging(self):
        """Konfiguriert das erweiterte Logging-System"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.output_dir / "oparl_client_advanced.log"),
            ],
        )
        self.logger = logging.getLogger("OParlClientAdvanced")

    def _make_request_with_progress(
        self, url: str, page: int = 1, pbar: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Führt einen HTTP-Request mit Progress Bar Support durch

        Args:
            url: Die angefragte URL
            page: Seitenzahl für Logging
            pbar: Progress Bar Objekt (optional)

        Returns:
            JSON-Daten oder None bei Fehler
        """
        cache_file = self.cache_dir / f"page_{page}.json"

        # Cache-Prüfung
        if self.enable_caching and cache_file.exists():
            self.logger.debug(f"Lade Seite {page} aus Cache")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.stats["cached_requests"] += 1
                if pbar:
                    pbar.set_description(f"Seite {page} (Cache)")
                return data
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Cache-Fehler Seite {page}: {e}")

        # Rate Limiting für echte Requests
        if self.stats["api_requests"] > 0:
            time.sleep(self.rate_limit)

        for attempt in range(self.max_retries):
            try:
                if pbar:
                    pbar.set_description(f"Seite {page} (Versuch {attempt + 1})")

                self.logger.debug(f"Request an {url} (Versuch {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                data = response.json()
                self.stats["api_requests"] += 1

                # Speichere im Cache
                if self.enable_caching:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    except IOError as e:
                        self.logger.warning(f"Konnte Seite {page} nicht cachen: {e}")

                if pbar:
                    pbar.set_description(f"Seite {page} (Erfolg)")

                return data

            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout bei Seite {page}, Versuch {attempt + 1}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(
                    f"Verbindungsfehler bei Seite {page}, Versuch {attempt + 1}"
                )
            except requests.exceptions.HTTPError as e:
                status_code = getattr(response, "status_code", "Unknown")
                self.logger.error(f"HTTP-Fehler {status_code} bei Seite {page}: {e}")
                if status_code in [400, 404, 500]:
                    break
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request-Fehler bei Seite {page}: {e}")
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON-Parsing-Fehler bei Seite {page}: {e}")
                break

            # Exponential Backoff
            if attempt < self.max_retries - 1:
                wait_time = (2**attempt) * 5
                self.logger.info(f"Warte {wait_time}s vor Wiederholung...")
                time.sleep(wait_time)

        self.stats["errors"] += 1
        if pbar:
            pbar.set_description(f"Seite {page} (Fehler)")
        return None

    def _estimate_total_pages(self) -> Tuple[int, int]:
        """
        Schätzt die Gesamtanzahl der Seiten für die Progress Bar

        Returns:
            Tuple (geschätzte Seiten, geschätzte Meetings)
        """
        try:
            first_page_url = f"{self.base_url}/meetings?body=1&page=1"
            data = self._make_request_with_progress(first_page_url, 1)

            if data and "data" in data:
                meetings_per_page = len(data.get("data", []))
                # Typische OParl-APIs haben 25-100 Meetings pro Seite
                estimated_pages = (
                    50 if meetings_per_page == 0 else max(10, 1000 // meetings_per_page)
                )
                estimated_meetings = estimated_pages * meetings_per_page
                return estimated_pages, estimated_meetings
        except Exception as e:
            self.logger.debug(f"Konnte Seiten nicht schätzen: {e}")

        # Fallback-Schätzungen
        return 50, 1000

    def _filter_meetings_by_date(self, meetings: List[Dict]) -> List[Dict]:
        """
        Filtert Meetings basierend auf dem Enddatum mit erweiterter Validierung

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
                # Normalisiere ISO 8601 String
                normalized_start = start_str.replace("Z", "+00:00")
                meeting_date = datetime.fromisoformat(normalized_start).date()

                if meeting_date <= end_date_obj:
                    filtered_meetings.append(meeting)
                else:
                    # Meeting ist nach Enddatum - könnte Pagination stoppen
                    pass

            except (ValueError, AttributeError) as e:
                self.logger.warning(f"Ungültiges Datum-Format '{start_str}': {e}")
                continue

        return filtered_meetings

    def _extract_meeting_data(self, meeting: Dict) -> Dict[str, Any]:
        """
        Extrahiert relevante Daten aus einem Meeting-Objekt mit erweiterten Feldern

        Args:
            meeting: Roh-Meeting-Daten

        Returns:
            Bereinigte Meeting-Daten
        """
        # Berechne Dauer falls Start und Ende vorhanden
        duration = None
        if meeting.get("start") and meeting.get("end"):
            try:
                start_dt = datetime.fromisoformat(
                    meeting["start"].replace("Z", "+00:00")
                )
                end_dt = datetime.fromisoformat(meeting["end"].replace("Z", "+00:00"))
                duration = int((end_dt - start_dt).total_seconds() // 60)  # Minuten
            except (ValueError, AttributeError):
                pass

        return {
            "id": meeting.get("id", ""),
            "name": meeting.get("name", ""),
            "start": meeting.get("start", ""),
            "end": meeting.get("end", ""),
            "duration_minutes": duration,
            "location": meeting.get("location", ""),
            "organization": meeting.get("organization", ""),
            "created": meeting.get("created", ""),
            "modified": meeting.get("modified", ""),
            "agenda_item_count": len(meeting.get("agendaItem", [])),
            "auxiliary_file_count": len(meeting.get("auxiliaryFile", [])),
        }

    def get_all_meetings(self) -> List[Dict[str, Any]]:
        """
        Ruft alle Meetings bis zum Enddatum ab mit Progress Bar

        Returns:
            Liste aller gefundenen Meetings
        """
        self.logger.info(f"Starte Abruf von Meetings bis {self.end_date}")
        self.stats["start_time"] = time.time()

        all_meetings = []
        page = 1
        next_url = f"{self.base_url}/meetings?body=1&page={page}"

        # Schätze Gesamtumfang für Progress Bar
        estimated_pages, estimated_meetings = self._estimate_total_pages()

        # Progress Bar Setup
        if self.enable_progress_bar:
            pbar = tqdm(
                total=estimated_meetings,
                desc="Lade Meetings",
                unit="Meeting",
                ncols=100,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            )
        else:
            pbar = None

        while next_url:
            # Update Progress Bar Beschreibung
            if pbar:
                pbar.set_description(f"Seite {page}")

            data = self._make_request_with_progress(next_url, page, pbar)

            if data is None:
                self.logger.warning(f"Konnte Seite {page} nicht laden")
                break

            if "data" not in data:
                self.logger.error(f"Ungültige Antwort-Struktur auf Seite {page}")
                break

            meetings = data["data"]
            filtered_meetings = self._filter_meetings_by_date(meetings)

            all_meetings.extend(filtered_meetings)
            self.stats["total_pages"] = page
            self.stats["total_meetings"] = len(all_meetings)
            self.stats["filtered_meetings"] += len(filtered_meetings)

            # Update Progress Bar
            if pbar:
                pbar.update(
                    len(meetings)
                )  # Zeige alle geladenen Meetings, nicht nur gefilterte
                pbar.set_postfix(
                    {
                        "Seiten": page,
                        "Meetings": len(all_meetings),
                        "Filter": len(filtered_meetings),
                    }
                )

            self.logger.debug(
                f"Seite {page}: {len(meetings)} Meetings, {len(filtered_meetings)} passen zum Filter"
            )

            # Nächste Seite prüfen
            links = data.get("links", {})
            next_url = links.get("next")
            page += 1

            # Abbruch wenn keine weiteren Seiten oder alle Meetings nach Enddatum
            if not next_url:
                self.logger.info("Keine weiteren Seiten verfügbar")
                break

        # Schließe Progress Bar
        if pbar:
            pbar.close()

        # Entferne Duplikate basierend auf ID
        unique_meetings = []
        seen_ids = set()
        duplicates = 0

        for meeting in all_meetings:
            meeting_id = meeting.get("id")
            if meeting_id and meeting_id not in seen_ids:
                seen_ids.add(meeting_id)
                unique_meetings.append(meeting)
            else:
                duplicates += 1

        self.stats["duplicates_removed"] = duplicates
        self.stats["end_time"] = time.time()

        self.logger.info(
            f"Abruf abgeschlossen: {len(unique_meetings)} eindeutige Meetings "
            f"({duplicates} Duplikate entfernt)"
        )

        return unique_meetings

    def export_to_csv(
        self, meetings: List[Dict], filename: str = "meetings_advanced.csv"
    ):
        """
        Exportiert Meetings als CSV-Datei mit erweiterten Feldern

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
            "duration_minutes",
            "location",
            "organization",
            "created",
            "modified",
            "agenda_item_count",
            "auxiliary_file_count",
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

    def export_to_json(
        self, meetings: List[Dict], filename: str = "meetings_advanced.json"
    ):
        """
        Exportiert Meetings als JSON-Datei mit Metadaten

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
                    "client_version": "OParlClientAdvanced/1.0",
                    "export_duration_seconds": self.stats.get("end_time", 0)
                    - self.stats.get("start_time", 0),
                },
                "statistics": self.stats if self.enable_statistics else {},
                "meetings": extracted_meetings,
            }

            with open(filepath, "w", encoding="utf-8") as jsonfile:
                json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)

            self.logger.info(f"JSON-Export abgeschlossen: {filepath}")
        except Exception as e:
            self.logger.error(f"Fehler beim JSON-Export: {e}")

    def print_detailed_statistics(self, meetings: List[Dict]):
        """
        Gibt detaillierte Statistiken zum Abruf aus

        Args:
            meetings: Liste der Meetings
        """
        if not meetings:
            self.logger.info("Keine Meetings für Statistik vorhanden")
            return

        # Erweiterte Statistiken
        dates = []
        durations = []
        agenda_items_total = 0

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

            # Berechne Dauer falls verfügbar
            if meeting.get("start") and meeting.get("end"):
                try:
                    start_dt = datetime.fromisoformat(
                        meeting["start"].replace("Z", "+00:00")
                    )
                    end_dt = datetime.fromisoformat(
                        meeting["end"].replace("Z", "+00:00")
                    )
                    duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
                    durations.append(duration_minutes)
                except (ValueError, AttributeError):
                    pass

            # Zähle Agenda-Items
            agenda_items = meeting.get("agendaItem", [])
            agenda_items_total += len(agenda_items)

        # Berechne Statistiken
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            time_range = f"{min_date} bis {max_date}"
            total_days = (max_date - min_date).days + 1
            meetings_per_day = len(meetings) / total_days if total_days > 0 else 0
        else:
            time_range = "Unbekannt"
            meetings_per_day = 0

        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0

        avg_agenda_items = agenda_items_total / len(meetings) if meetings else 0

        # Ausgabe der detaillierten Statistiken
        self.logger.info("=" * 60)
        self.logger.info("DETAILLIERTE STATISTIKEN")
        self.logger.info("=" * 60)
        self.logger.info(f"Abgerufene Meetings: {len(meetings)}")
        self.logger.info(f"Seiten durchsucht: {self.stats['total_pages']}")
        self.logger.info(f"API-Requests: {self.stats['api_requests']}")
        self.logger.info(f"Cached Requests: {self.stats['cached_requests']}")
        self.logger.info(f"Fehler: {self.stats['errors']}")
        self.logger.info(f"Duplikate entfernt: {self.stats['duplicates_removed']}")
        self.logger.info(f"Gefilterte Meetings: {self.stats['filtered_meetings']}")
        self.logger.info("")
        self.logger.info(f"Zeitraum: {time_range}")
        self.logger.info(f"Meetings pro Tag: {meetings_per_day:.2f}")
        self.logger.info("")
        self.logger.info(f"Durchschnittliche Dauer: {avg_duration:.1f} Minuten")
        self.logger.info(f"Kürzeste Sitzung: {min_duration} Minuten")
        self.logger.info(f"Längste Sitzung: {max_duration} Minuten")
        self.logger.info("")
        self.logger.info(f"Durchschn. Tagesordnungspunkte: {avg_agenda_items:.1f}")
        self.logger.info(f"Gesamte Tagesordnungspunkte: {agenda_items_total}")
        self.logger.info("=" * 60)

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

            # Detaillierte Statistik
            if self.enable_statistics:
                self.print_detailed_statistics(meetings)

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
    client = OParlClientAdvanced()
    client.run()


if __name__ == "__main__":
    main()
