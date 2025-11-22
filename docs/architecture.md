# Architekturüberblick

## Modulübersicht

- **src/main.py**: Einstiegspunkt, initialisiert die Anwendung und verdrahtet GUI, Models und AI-Client.
- **src/gui/main_window.py**: Enthält das CustomTkinter-basierte GUI-Fenster, Eingaben für Charaktereigenschaften und Trigger für API-Aufrufe.
- **src/models/character.py**: Datenmodell für Charaktere (z. B. Name, Attribute, Hintergrund). Dient als Austauschformat zwischen GUI, AI-Client und Exportern.
- **src/models/options_data.py**: Stellt statische Optionswerte (z. B. Klassen, Spezialisierungen) bereit, die im UI angezeigt werden.
- **src/ai/client.py**: Kapselt die Kommunikation mit Google Generative AI. Liest API Key aus `.env`, übernimmt Prompting und Fehlermanagement.
- **src/exporters/markdown_exporter.py**: Exportiert generierte Charaktere in Markdown, z. B. zur Weitergabe oder Dokumentation.

## Datenflüsse (Kurzfassung)

1. Benutzer gibt Daten im GUI ein (`main_window.py`).
2. Eingaben werden in ein `Character`-Objekt überführt (`models/character.py`).
3. Der `ai/client.py` sendet den Prompt und erhält generierten Text.
4. Ergebnisse werden in der GUI angezeigt und können über `markdown_exporter.py` gespeichert werden.

## Erweiterungshinweise

- **Neue Modelle**: In `src/models/` hinzufügen und über die GUI referenzieren.
- **Neue Exportformate**: Zusätzliche Exporter unter `src/exporters/` anlegen und im UI anbieten.
- **Konfiguration**: Sensible Einstellungen via `.env`; globale Defaults können in einem dedizierten Config-Modul ergänzt werden.
