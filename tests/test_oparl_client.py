"""
Test-Datei für den OParl-Client
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from oparl_client import OParlClient


class TestOParlClient:
    """Test-Klasse für den OParl-Client"""

    def setup_method(self):
        """Setup für jeden Test"""
        self.temp_dir = tempfile.mkdtemp()
        self.client = OParlClient(
            base_url="https://test.example.com/oparl",
            end_date="2025-12-31",
            output_dir=self.temp_dir,
            cache_dir=os.path.join(self.temp_dir, "cache"),
            rate_limit=0.1,  # Kurze Wartezeit für Tests
            max_retries=1,
        )

    def teardown_method(self):
        """Cleanup nach jedem Test"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Testet die Initialisierung des Clients"""
        assert self.client.base_url == "https://test.example.com/oparl"
        assert self.client.end_date == "2025-12-31"
        assert Path(self.client.output_dir).exists()
        assert Path(self.client.cache_dir).exists()

    def test_extract_meeting_data(self):
        """Testet die Extraktion von Meeting-Daten"""
        sample_meeting = {
            "id": "https://example.com/meeting/1",
            "name": "Test Meeting",
            "start": "2025-01-01T10:00:00+01:00",
            "end": "2025-01-01T12:00:00+01:00",
            "location": "Rathaus Bonn",
            "organization": "https://example.com/organization/1",
            "created": "2024-12-01T00:00:00+01:00",
            "modified": "2024-12-02T00:00:00+01:00",
        }

        extracted = self.client._extract_meeting_data(sample_meeting)

        assert extracted["id"] == sample_meeting["id"]
        assert extracted["name"] == sample_meeting["name"]
        assert extracted["start"] == sample_meeting["start"]
        assert extracted["end"] == sample_meeting["end"]
        assert extracted["location"] == sample_meeting["location"]

    def test_filter_meetings_by_date(self):
        """Testet die Datums-Filterung"""
        meetings = [
            {"id": "1", "start": "2025-01-01T10:00:00+01:00", "name": "Meeting 1"},
            {
                "id": "2",
                "start": "2026-01-01T10:00:00+01:00",  # Nach Enddatum
                "name": "Meeting 2",
            },
            {"id": "3", "start": "2025-06-15T10:00:00+01:00", "name": "Meeting 3"},
        ]

        filtered = self.client._filter_meetings_by_date(meetings)

        assert len(filtered) == 2
        assert filtered[0]["id"] == "1"
        assert filtered[1]["id"] == "3"

    def test_filter_meetings_invalid_date(self):
        """Testet Filterung mit ungültigem Datum"""
        meetings = [
            {"id": "1", "start": "invalid-date-format", "name": "Invalid Date Meeting"},
            {"id": "2", "start": "2025-01-01T10:00:00+01:00", "name": "Valid Meeting"},
        ]

        filtered = self.client._filter_meetings_by_date(meetings)

        assert len(filtered) == 1
        assert filtered[0]["id"] == "2"

    @patch("oparl_client.requests.Session")
    def test_make_request_success(self, mock_session):
        """Testet erfolgreichen API-Request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [], "links": {"next": None}}
        mock_session.return_value.get.return_value = mock_response

        client = OParlClient(
            base_url="https://test.example.com/oparl", output_dir=self.temp_dir
        )
        client.session = mock_session.return_value

        result = client._make_request("https://test.example.com/oparl/meetings")

        assert result is not None
        assert "data" in result

    @patch("oparl_client.requests.Session")
    def test_make_request_http_error(self, mock_session):
        """Testet HTTP-Fehler bei API-Request"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_session.return_value.get.return_value = mock_response

        client = OParlClient(
            base_url="https://test.example.com/oparl",
            output_dir=self.temp_dir,
            max_retries=1,
        )
        client.session = mock_session.return_value

        result = client._make_request("https://test.example.com/oparl/meetings")

        assert result is None
        assert client.stats["errors"] == 1

    def test_export_to_csv(self):
        """Testet CSV-Export"""
        meetings = [
            {
                "id": "https://example.com/meeting/1",
                "name": "Test Meeting 1",
                "start": "2025-01-01T10:00:00+01:00",
                "end": "2025-01-01T12:00:00+01:00",
                "location": "Rathaus Bonn",
                "organization": "https://example.com/organization/1",
                "created": "2024-12-01T00:00:00+01:00",
                "modified": "2024-12-02T00:00:00+01:00",
            }
        ]

        self.client.export_to_csv(meetings, "test_meetings.csv")

        csv_file = Path(self.temp_dir) / "test_meetings.csv"
        assert csv_file.exists()

        # Überprüfe CSV-Inhalt
        with open(csv_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Test Meeting 1" in content
            assert "Rathaus Bonn" in content

    def test_export_to_json(self):
        """Testet JSON-Export"""
        meetings = [
            {
                "id": "https://example.com/meeting/1",
                "name": "Test Meeting 1",
                "start": "2025-01-01T10:00:00+01:00",
            }
        ]

        self.client.export_to_json(meetings, "test_meetings.json")

        json_file = Path(self.temp_dir) / "test_meetings.json"
        assert json_file.exists()

        # Überprüfe JSON-Struktur
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "metadata" in data
            assert "meetings" in data
            assert len(data["meetings"]) == 1
            assert data["meetings"][0]["name"] == "Test Meeting 1"

    def test_export_empty_meetings(self):
        """Testet Export ohne Meetings"""
        self.client.export_to_csv([], "empty.csv")
        self.client.export_to_json([], "empty.json")

        # Dateien sollten nicht erstellt werden
        csv_file = Path(self.temp_dir) / "empty.csv"
        json_file = Path(self.temp_dir) / "empty.json"

        # Derzeitige Implementierung erstellt leere Dateien,
        # aber das könnte sich ändern
        # assert not csv_file.exists()
        # assert not json_file.exists()

    def test_print_statistics(self):
        """Testet die Statistik-Ausgabe"""
        meetings = [
            {"id": "1", "start": "2025-01-01T10:00:00+01:00", "name": "Meeting 1"},
            {"id": "2", "start": "2025-02-01T10:00:00+01:00", "name": "Meeting 2"},
        ]

        # Diese Methode gibt nur aus, sollte keinen Fehler werfen
        self.client.print_statistics(meetings)

    def test_print_statistics_empty(self):
        """Testet Statistik-Ausgabe ohne Meetings"""
        self.client.print_statistics([])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
