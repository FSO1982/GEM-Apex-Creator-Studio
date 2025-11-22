# GEM-Apex Dossier Architect - Quick Start Guide

## 🚀 Schnellstart (Einfachster Weg)

### Option 1: Doppelklick auf die .bat Datei

1. Doppelklicken Sie auf **`GEM-Apex-START.bat`** im Hauptordner
2. Fertig! Das Programm startet automatisch.

### Option 2: Einfache Start-Datei

Doppelklicken Sie auf **`START.bat`**

---

## ⚠️ Wichtig: Warum funktioniert ein direkter Python-Start manchmal nicht?

Sie haben versucht, `main_window.py` direkt zu öffnen. Das funktioniert nicht, weil:

- `main_window.py` ist nur ein Teil des Programms (die Benutzeroberfläche)
- Das **Startprogramm** ist `src/main.py`

**Richtig**: `python src/main.py` ✅
**Falsch**: `python src/gui/main_window.py` ❌

---

## 🔧 Manuelle Installation (falls nötig)

Falls die .bat Dateien nicht funktionieren oder Sie unter Linux/macOS arbeiten, folgen Sie diesen Schritten:

1. **Python 3.10+ installieren** (empfohlen 3.11). Prüfen mit `python --version`.
2. **Virtuelle Umgebung anlegen** (empfohlen):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```

3. **Environment-Variablen setzen**: Legen Sie eine `.env` Datei im Projektwurzelverzeichnis an (wird von `src/ai/client.py` gelesen). Beispiel:

   ```env
   GOOGLE_API_KEY=AIzaSyC...
   LOG_LEVEL=INFO
   ```

4. **Dependencies installieren**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Programm starten**:

   ```bash
   python src/main.py
   ```

6. **Beenden**: virtuelle Umgebung mit `deactivate` verlassen.

---

## 🧪 Checks & Wartung

Führen Sie vor einem Commit oder Release die folgenden Prüfungen aus:

1. **Formatierung**: `black src` (optional für reine GUI-Änderungen, empfohlen für CI-Konformität)
2. **Linting**: `python -m compileall src`
3. **Tests**: `pytest` (falls Tests vorhanden sind)
4. **Security/Dependencies**: `pip-audit` (prüft `requirements.txt`)

Auf Windows können die Befehle innerhalb von PowerShell analog verwendet werden.

---

## 🛠️ Troubleshooting

- **Fehlender API Key**: Stellen Sie sicher, dass `GOOGLE_API_KEY` in `.env` gesetzt ist und der Wert keine Leerzeichen enthält.
- **Module not found / ImportError**: Prüfen Sie, ob die virtuelle Umgebung aktiv ist und `pip install -r requirements.txt` erfolgreich durchlief.
- **Tkinter GUI öffnet nicht**: Unter Linux müssen ggf. zusätzliche Tk-Pakete installiert werden (`sudo apt-get install python3-tk`).
- **Rate Limits erreicht**: Google AI Studio hat Limits pro Minute/Tag. Versuchen Sie es nach kurzer Wartezeit erneut.
- **Logging zu ausführlich**: Passen Sie `LOG_LEVEL` in der `.env` an (`INFO`, `WARNING`, `ERROR`).

---

## 🔐 Sicherheit (API Keys & Logging)

- Speichern Sie Ihren Google API Key **nur** in der `.env` Datei oder in Ihrem Secrets-Manager, niemals im Klartext im Code oder in Versionskontrolle.
- Teilen Sie Logfiles vor dem Versenden mit Dritten nicht, wenn sie API Keys oder personenbezogene Daten enthalten. Nutzen Sie `LOG_LEVEL=INFO` oder höher, um sensible Debug-Ausgaben zu vermeiden.
- Drehen Sie kompromittierte API Keys sofort zurück und erstellen Sie neue Schlüssel über Google AI Studio.

---

## 📝 Was die START.bat Datei macht:

1. Wechselt in den richtigen Ordner
2. Installiert fehlende Pakete (customtkinter, google-generativeai, pillow)
3. Startet `src/main.py`
4. Zeigt Fehler an, falls etwas schiefgeht

---

## ✅ Checkliste vor dem Start:

- [ ] Python ist installiert (Version 3.10+)
- [ ] Virtuelle Umgebung aktiviert und Dependencies installiert
- [ ] `.env` mit `GOOGLE_API_KEY` vorhanden
- [ ] Sie sind im richtigen Ordner (`custom_char_gen`)
- [ ] Google API Key bereit (von aistudio.google.com/apikey)

**Viel Erfolg!** 🎉
