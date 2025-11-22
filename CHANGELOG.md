# Changelog

## [Unreleased]
### Added
- Laden und Validieren von API-Keys aus `.env` per `python-dotenv` inklusive Maskierung der Eingaben in der UI.
- Vereinheitlichte `Result(success, data, error)`-Rückgaben für Text-, Bild- und Chat-Operationen mit Retry-/Timeout-Logik.
- Verbesserte Fehlermeldungen für Rate-Limits und Authentifizierungsprobleme.
