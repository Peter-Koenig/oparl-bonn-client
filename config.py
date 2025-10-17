"""
Konfigurationsdatei für den OParl-Client
"""

from datetime import datetime
from typing import Dict, Any

# API-Konfiguration
API_CONFIG: Dict[str, Any] = {
    "BASE_URL": "https://www.bonn.sitzung-online.de/public/oparl",
    "MEETINGS_ENDPOINT": "/meetings?body=1&page=",
    "TIMEOUT": 30,
    "RATE_LIMIT": 1.0,  # Sekunden zwischen Requests
}

# Filter-Konfiguration
FILTER_CONFIG: Dict[str, Any] = {
    "END_DATE": "2025-12-31",  # Format: YYYY-MM-DD
    "CURRENT_DATE": datetime.now().date().isoformat(),  # Heutiges Datum
}

# Ausgabe-Konfiguration
OUTPUT_CONFIG: Dict[str, Any] = {
    "OUTPUT_DIR": "output",
    "CACHE_DIR": "cache",
    "CSV_FILENAME": "meetings.csv",
    "JSON_FILENAME": "meetings.json",
    "LOG_FILENAME": "oparl_client.log",
}

# Fehlerbehandlung
ERROR_HANDLING: Dict[str, Any] = {
    "MAX_RETRIES": 3,
    "RETRY_DELAY_BASE": 5,  # Basis-Wartezeit für Retry in Sekunden
    "RETRY_BACKOFF_FACTOR": 2,  # Exponential Backoff Faktor
    "SKIP_HTTP_ERRORS": [400, 404, 500],  # HTTP-Fehler ohne Wiederholung
}

# Logging-Konfiguration
LOGGING_CONFIG: Dict[str, Any] = {
    "LEVEL": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
    "DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
}

# Validierung
VALIDATION_CONFIG: Dict[str, Any] = {
    "REQUIRED_FIELDS": ["id", "name", "start"],
    "OPTIONAL_FIELDS": ["end", "location", "organization", "created", "modified"],
    "DATE_FORMAT": "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 Format
}

# Erweiterte Features (optional)
ADVANCED_FEATURES: Dict[str, Any] = {
    "ENABLE_CACHING": True,
    "ENABLE_STATISTICS": True,
    "ENABLE_PROGRESS_BAR": False,  # Benötigt tqdm
    "REMOVE_DUPLICATES": True,
    "VALIDATE_DATES": True,
}


def get_full_config() -> Dict[str, Any]:
    """
    Gibt die vollständige Konfiguration zurück

    Returns:
        Dictionary mit allen Konfigurationseinstellungen
    """
    return {
        "api": API_CONFIG,
        "filter": FILTER_CONFIG,
        "output": OUTPUT_CONFIG,
        "error_handling": ERROR_HANDLING,
        "logging": LOGGING_CONFIG,
        "validation": VALIDATION_CONFIG,
        "advanced_features": ADVANCED_FEATURES,
    }


def validate_config() -> bool:
    """
    Validiert die Konfigurationseinstellungen

    Returns:
        True wenn Konfiguration gültig ist, sonst False
    """
    try:
        # Validiere Datumsformat
        datetime.strptime(FILTER_CONFIG["END_DATE"], "%Y-%m-%d")

        # Validiere numerische Werte
        assert API_CONFIG["TIMEOUT"] > 0
        assert API_CONFIG["RATE_LIMIT"] >= 0
        assert ERROR_HANDLING["MAX_RETRIES"] >= 0
        assert ERROR_HANDLING["RETRY_DELAY_BASE"] > 0
        assert ERROR_HANDLING["RETRY_BACKOFF_FACTOR"] >= 1

        return True
    except (ValueError, AssertionError) as e:
        print(f"Konfigurationsfehler: {e}")
        return False


if __name__ == "__main__":
    # Test der Konfiguration
    if validate_config():
        print("Konfiguration ist gültig")
        print("Vollständige Konfiguration:")
        for section, config in get_full_config().items():
            print(f"\n{section.upper()}:")
            for key, value in config.items():
                print(f"  {key}: {value}")
    else:
        print("Konfiguration ist ungültig")
