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

Falls die .bat Dateien nicht funktionieren:

1. **Terminal öffnen** (PowerShell oder CMD)
2. **In den Projektordner wechseln**:

   ```bash
   cd "C:\Users\Frank Soulier\.gemini\antigravity\scratch\custom_char_gen"
   ```

3. **Dependencies installieren**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Programm starten**:
   ```bash
   python src/main.py
   ```

---

## 📝 Was die START.bat Datei macht:

1. Wechselt in den richtigen Ordner
2. Installiert fehlende Pakete (customtkinter, google-generativeai, pillow)
3. Startet `src/main.py`
4. Zeigt Fehler an, falls etwas schiefgeht

---

## ✅ Checkliste vor dem Start:

- [ ] Python ist installiert (Version 3.10+)
- [ ] Sie sind im richtigen Ordner (`custom_char_gen`)
- [ ] Google API Key bereit (von aistudio.google.com/apikey)

**Viel Erfolg!** 🎉
