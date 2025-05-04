import os
import winreg
import time

FILE_NAME = "winUpdateLogger.exe"
APP_NAME = "WinUpdateLogger"

# Pfade
TARGET_PATH = os.path.join(os.getenv("APPDATA"), FILE_NAME)
TEXT_LOG_PATH = os.path.join(os.getenv("APPDATA"), "system_log.txt")
HTML_LOG_PATH = os.path.join(os.getenv("APPDATA"), "system_log.html")

# Registry-Eintrag löschen
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS) as key:
        winreg.DeleteValue(key, APP_NAME)
    print("Registry-Eintrag entfernt.")
except FileNotFoundError:
    print("Registry-Eintrag nicht gefunden.")
except Exception as e:
    print(f"Fehler beim Entfernen des Registry-Eintrags: {e}")
time.sleep(1)

# Text-Logdatei löschen
try:
    if os.path.exists(TEXT_LOG_PATH):
        os.remove(TEXT_LOG_PATH)
        print("Text-Logdatei gelöscht.")
except FileNotFoundError:
    print("Text-Logdatei nicht gefunden.")
except Exception as e:
    print(f"Fehler beim Löschen der Logdatei: {e}")
time.sleep(1)

# HTML-Logdatei löschen
try:
    if os.path.exists(HTML_LOG_PATH):
        os.remove(HTML_LOG_PATH)
        print("HTML-Logdatei gelöscht.")
except FileNotFoundError:
    print("HTML-Logdatei nicht gefunden.")
except Exception as e:
    print(f"Fehler beim Löschen der HTML-Logdatei: {e}")
time.sleep(1)

# EXE-Datei löschen (funktioniert nicht, wenn man sich selbst löscht!)
try:
    if os.path.exists(TARGET_PATH):
        os.remove(TARGET_PATH)
        print("Kopierte EXE-Datei gelöscht.")
except FileNotFoundError:
    print("EXE-Datei nicht gefunden.")
except Exception as e:
    print(f"Fehler beim Löschen der EXE-Datei: {e}")
time.sleep(1)