import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ctypes
import threading
import time
import random
import keyboard
import re
import json
from datetime import datetime

# ==========================================
# GESTIONE API DI WINDOWS (HARDWARE LEVEL)
# ==========================================
class WinAPI:
    """Classe per gestire in modo pulito le chiamate a livello hardware tramite ctypes."""
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    VK_ESCAPE = 0x1B
    VK_SPACE = 0x20
    KEYEVENTF_KEYUP = 0x0002

    @staticmethod
    def is_esc_pressed() -> bool:
        return bool(ctypes.windll.user32.GetAsyncKeyState(WinAPI.VK_ESCAPE) & 0x8000)

    @staticmethod
    def move_mouse_relative(x: int, y: int):
        ctypes.windll.user32.mouse_event(WinAPI.MOUSEEVENTF_MOVE, x, y, 0, 0)

    @staticmethod
    def click_mouse():
        ctypes.windll.user32.mouse_event(WinAPI.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        ctypes.windll.user32.mouse_event(WinAPI.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    @staticmethod
    def press_space():
        ctypes.windll.user32.keybd_event(WinAPI.VK_SPACE, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.2))
        ctypes.windll.user32.keybd_event(WinAPI.VK_SPACE, 0, WinAPI.KEYEVENTF_KEYUP, 0)


# ==========================================
# APPLICAZIONE PRINCIPALE
# ==========================================
class UltimateAntiAFK:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Ultimate Anti-AFK Pro - Multi-Tool")
        self.root.geometry("780x700")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        # --- Eventi di Sincronizzazione Thread (Molto più sicuri dei booleani) ---
        self.kb_stop_event = threading.Event()
        self.mouse_stop_event = threading.Event()
        self.monitor_stop_event = threading.Event()
        
        # Di default i thread sono "fermi" (l'evento di stop è settato)
        self.kb_stop_event.set()
        self.mouse_stop_event.set()

        # --- Variabili Modulo Tastiera ---
        self.selected_keys_list = ["w", "s", "a", "d", "space"]
        self.constant_keys_list = ["shift"]
        
        self.all_possible_keys = sorted([
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'shift', 'left shift', 'right shift', 'ctrl', 'left ctrl', 'right ctrl', 
            'alt', 'alt gr', 'windows', 'left windows', 'right windows',
            'up', 'down', 'left', 'right', 'insert', 'home', 'page up', 'delete', 'end', 'page down',
            'space', 'enter', 'esc', 'tab', 'backspace', 'caps lock', 'print screen', 'scroll lock', 'pause',
            'num lock', 'numpad 0', 'numpad 1', 'numpad 2', 'numpad 3', 'numpad 4', 
            'numpad 5', 'numpad 6', 'numpad 7', 'numpad 8', 'numpad 9', 
            'numpad /', 'numpad *', 'numpad -', 'numpad +', 'numpad enter', 'numpad .',
            ',', '.', '/', ';', "'", '[', ']', '\\', '-', '=', '`'
        ])
        
        # --- Variabili Modulo Mouse 3D ---
        self.distance_var = tk.IntVar(value=150)  # Convertito a IntVar per lo slider
        self.use_jump_var = tk.BooleanVar(value=True)
        self.use_click_var = tk.BooleanVar(value=True)
        self.use_random_var = tk.BooleanVar(value=True)
        
        self.delay_min_var = tk.StringVar(value="2.0")
        self.delay_max_var = tk.StringVar(value="5.0")
        self.speed_min_var = tk.StringVar(value="0.5")
        self.speed_max_var = tk.StringVar(value="1.5")

        # --- Validatore per Entry numeriche ---
        self.vcmd_float = (self.root.register(self.validate_float_input), '%P')
        self.vcmd_int = (self.root.register(self.validate_int_input), '%P')

        self.setup_styles()
        self.create_gui()

        # Avvia monitor globale tasto ESC
        threading.Thread(target=self.global_esc_monitor, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # --- Funzioni di Validazione Input Tkinter ---
    def validate_float_input(self, value_if_allowed):
        if value_if_allowed == "" or value_if_allowed == ".": return True
        return bool(re.match(r'^\d*\.?\d*$', value_if_allowed))

    def validate_int_input(self, value_if_allowed):
        if value_if_allowed == "": return True
        return value_if_allowed.isdigit()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color, fg_color, panel_bg = "#1e1e2e", "#cdd6f4", "#313244"
        accent_green, accent_red, accent_blue = "#a6e3a1", "#f38ba8", "#89b4fa"

        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=panel_bg, foreground=fg_color, padding=[10, 5], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", accent_green)], foreground=[("selected", bg_color)])
        
        style.configure("TFrame", background=bg_color)
        style.configure("Panel.TFrame", background=panel_bg)
        
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=panel_bg, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=accent_green, background=bg_color)
        style.configure("Warning.TLabel", font=("Segoe UI", 10, "bold"), foreground=accent_red, background=bg_color)
        style.configure("Countdown.TLabel", font=("Segoe UI", 12, "bold"), foreground=accent_blue, background=bg_color)
        
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", bg_color)])
        
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_blue, font=("Segoe UI", 10, "bold"))

    def create_gui(self):
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="ULTIMATE ANTI-AFK SUITE", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="PREMI 'ESC' PER FERMARE TUTTO", style="Warning.TLabel").pack(side=tk.RIGHT)

        # Barra degli strumenti per Salva/Carica configurazione
        toolbar = tk.Frame(self.root, bg="#313244", pady=5)
        toolbar.pack(fill=tk.X, padx=10)
        tk.Button(toolbar, text="💾 Salva Config.", command=self.save_config, bg="#89b4fa", fg="#1e1e2e", font=("Segoe UI", 9, "bold"), borderwidth=0, cursor="hand2", padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="📂 Carica Config.", command=self.load_config, bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 9, "bold"), borderwidth=0, cursor="hand2", padx=10).pack(side=tk.LEFT, padx=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tab_kb = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.tab_kb, text="⌨️ Simulatore Tastiera (MMO/2D)")
        self.build_keyboard_tab()

        self.tab_mouse = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.tab_mouse, text="🖱️ Mouse 3D & Hardware (MC/FPS)")
        self.build_mouse_tab()

        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.global_status_lbl = ttk.Label(status_frame, text="Stato Globale: In attesa...", font=("Segoe UI", 10, "italic"))
        self.global_status_lbl.pack(side=tk.LEFT)

    def create_entry(self, parent, default_val, width, is_float=True, **kwargs):
        """Helper per creare Entry con validazione integrata"""
        vcmd = self.vcmd_float if is_float else self.vcmd_int
        entry = tk.Entry(parent, width=width, bg="#313244", fg="white", borderwidth=0, validate='key', validatecommand=vcmd, **kwargs)
        entry.insert(0, default_val)
        return entry

    def build_keyboard_tab(self):
        main_container = ttk.Frame(self.tab_kb)
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)

        # -- Sinistra: Tasti Principali --
        left_panel = tk.Frame(main_container, bg="#313244", padx=10, pady=10)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        ttk.Label(left_panel, text="Tasti AFK Principali (Random)", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        ctrl_frame1 = tk.Frame(left_panel, bg="#313244")
        ctrl_frame1.pack(fill=tk.X, pady=5)
        self.kb_dropdown_var = tk.StringVar(value="Seleziona Tasto")
        ttk.OptionMenu(ctrl_frame1, self.kb_dropdown_var, "Seleziona Tasto", *self.all_possible_keys).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(ctrl_frame1, text="Aggiungi", command=lambda: self.add_key(self.selected_keys_list, self.listbox_main, self.kb_dropdown_var), bg="#89b4fa", fg="white", borderwidth=0, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl_frame1, text="Rimuovi", command=lambda: self.remove_key(self.selected_keys_list, self.listbox_main), bg="#f38ba8", fg="white", borderwidth=0, cursor="hand2").pack(side=tk.LEFT)

        self.listbox_main = tk.Listbox(left_panel, height=6, bg="#1e1e2e", fg="white", borderwidth=0, font=("Segoe UI", 10))
        self.listbox_main.pack(fill=tk.BOTH, expand=True, pady=5)
        self.update_listbox(self.selected_keys_list, self.listbox_main)

        # -- Destra: Tasti Costanti --
        right_panel = tk.Frame(main_container, bg="#313244", padx=10, pady=10)
        right_panel.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        ttk.Label(right_panel, text="Tasti Costanti (Ciclici)", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        ctrl_frame2 = tk.Frame(right_panel, bg="#313244")
        ctrl_frame2.pack(fill=tk.X, pady=5)
        self.const_dropdown_var = tk.StringVar(value="Seleziona Tasto")
        ttk.OptionMenu(ctrl_frame2, self.const_dropdown_var, "Seleziona Tasto", *self.all_possible_keys).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(ctrl_frame2, text="Aggiungi", command=lambda: self.add_key(self.constant_keys_list, self.listbox_const, self.const_dropdown_var), bg="#89b4fa", fg="white", borderwidth=0, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl_frame2, text="Rimuovi", command=lambda: self.remove_key(self.constant_keys_list, self.listbox_const), bg="#f38ba8", fg="white", borderwidth=0, cursor="hand2").pack(side=tk.LEFT)

        self.listbox_const = tk.Listbox(right_panel, height=3, bg="#1e1e2e", fg="white", borderwidth=0, font=("Segoe UI", 10))
        self.listbox_const.pack(fill=tk.X, pady=5)
        self.update_listbox(self.constant_keys_list, self.listbox_const)

        ttk.Label(right_panel, text="Intervallo Tasti Costanti (s):", style="Panel.TLabel").pack(anchor=tk.W, pady=(10, 0))
        self.const_interval_entry = self.create_entry(right_panel, "5.0", width=15)
        self.const_interval_entry.pack(fill=tk.X, pady=5, ipady=3)

        # -- Parametri Timing --
        params_frame = ttk.Frame(self.tab_kb)
        params_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(params_frame, text="Ritardo tra i tasti Min/Max (s):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.min_cd_entry = self.create_entry(params_frame, "0.5", width=8)
        self.min_cd_entry.grid(row=0, column=1, padx=5, pady=5, ipady=3)
        self.max_cd_entry = self.create_entry(params_frame, "2.0", width=8)
        self.max_cd_entry.grid(row=0, column=2, padx=5, pady=5, ipady=3)

        ttk.Label(params_frame, text="Durata pressione Min/Max (s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.min_dur_entry = self.create_entry(params_frame, "0.1", width=8)
        self.min_dur_entry.grid(row=1, column=1, padx=5, pady=5, ipady=3)
        self.max_dur_entry = self.create_entry(params_frame, "0.3", width=8)
        self.max_dur_entry.grid(row=1, column=2, padx=5, pady=5, ipady=3)

        self.btn_kb_start = tk.Button(self.tab_kb, text="AVVIA MODULO TASTIERA", command=self.toggle_kb_sim, bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 11, "bold"), borderwidth=0, cursor="hand2")
        self.btn_kb_start.pack(fill=tk.X, pady=10, ipady=8)

    def build_mouse_tab(self):
        desc = "Utilizza API Hardware per muovere il cursore. Include randomizzazione per bypassare controlli euristici."
        ttk.Label(self.tab_mouse, text=desc, font=("Segoe UI", 9, "italic")).pack(pady=(0, 10))

        time_frame = ttk.LabelFrame(self.tab_mouse, text="⌚ Tempi e Velocità (Secondi)")
        time_frame.pack(fill=tk.X, pady=5, ipady=5, ipadx=5)
        
        ttk.Label(time_frame, text="Pausa tra mosse (Min - Max):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.create_entry(time_frame, "2.0", width=8, textvariable=self.delay_min_var, justify='center').grid(row=0, column=1, padx=5, pady=5, ipady=4)
        self.create_entry(time_frame, "5.0", width=8, textvariable=self.delay_max_var, justify='center').grid(row=0, column=2, padx=5, pady=5, ipady=4)

        ttk.Label(time_frame, text="Durata spostamento (Veloce - Lento):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.create_entry(time_frame, "0.5", width=8, textvariable=self.speed_min_var, justify='center').grid(row=1, column=1, padx=5, pady=5, ipady=4)
        self.create_entry(time_frame, "1.5", width=8, textvariable=self.speed_max_var, justify='center').grid(row=1, column=2, padx=5, pady=5, ipady=4)

        move_frame = ttk.LabelFrame(self.tab_mouse, text="🎯 Parametri Movimento")
        move_frame.pack(fill=tk.X, pady=5, ipady=5, ipadx=5)

        ttk.Label(move_frame, text="Ampiezza Max Movimento (Pixel):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        # Sostituito l'Entry con uno Slider (Scale) da 100 a 500
        self.distance_scale = tk.Scale(move_frame, from_=100, to=500, orient=tk.HORIZONTAL, variable=self.distance_var, bg="#313244", fg="white", highlightthickness=0, bd=0, length=200)
        self.distance_scale.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        opts_frame = ttk.LabelFrame(self.tab_mouse, text="⚙️ Azioni Anti-Cheat Casuali")
        opts_frame.pack(fill=tk.X, pady=5, ipady=5, ipadx=10)
        
        ttk.Checkbutton(opts_frame, text="Direzione Casuale 360° (Consigliato)", variable=self.use_random_var).pack(anchor=tk.W, pady=2, padx=10)
        ttk.Checkbutton(opts_frame, text="Auto-Salto occasionale (Spazio - Livello Hardware)", variable=self.use_jump_var).pack(anchor=tk.W, pady=2, padx=10)
        ttk.Checkbutton(opts_frame, text="Auto-Click occasionale (Tasto Sinistro - Livello Hardware)", variable=self.use_click_var).pack(anchor=tk.W, pady=2, padx=10)

        self.mouse_countdown_lbl = ttk.Label(self.tab_mouse, text="In attesa di avvio...", style="Countdown.TLabel")
        self.mouse_countdown_lbl.pack(pady=10)

        self.btn_mouse_start = tk.Button(self.tab_mouse, text="AVVIA MODULO MOUSE 3D", command=self.toggle_mouse_sim, bg="#89b4fa", fg="#1e1e2e", font=("Segoe UI", 11, "bold"), borderwidth=0, cursor="hand2")
        self.btn_mouse_start.pack(fill=tk.X, side=tk.BOTTOM, pady=5, ipady=8)

    # ==========================================
    # UTILITY GUI
    # ==========================================
    def update_listbox(self, lst, listbox):
        listbox.delete(0, tk.END)
        for item in lst:
            listbox.insert(tk.END, item)

    def add_key(self, lst, listbox, dropdown_var):
        val = dropdown_var.get()
        if val != "Seleziona Tasto":
            lst.append(val)
            self.update_listbox(lst, listbox)
            dropdown_var.set("Seleziona Tasto")

    def remove_key(self, lst, listbox):
        sel = listbox.curselection()
        if sel:
            del lst[sel[0]]
        elif lst:
            lst.pop()
        self.update_listbox(lst, listbox)

    def update_global_status(self):
        kb_st = "🔴 FERMO" if self.kb_stop_event.is_set() else "🟢 ATTIVO"
        ms_st = "🔴 FERMO" if self.mouse_stop_event.is_set() else "🟢 ATTIVO"
        # Usare after per aggiornare la GUI dal thread secondario
        self.root.after(0, lambda: self.global_status_lbl.config(text=f"Stato Globale | Tastiera: {kb_st} | Mouse 3D: {ms_st}"))

    # ==========================================
    # GESTIONE CONFIGURAZIONI (JSON)
    # ==========================================
    def save_config(self):
        config = {
            "keyboard": {
                "selected_keys": self.selected_keys_list,
                "constant_keys": self.constant_keys_list,
                "const_interval": self.const_interval_entry.get(),
                "min_cd": self.min_cd_entry.get(),
                "max_cd": self.max_cd_entry.get(),
                "min_dur": self.min_dur_entry.get(),
                "max_dur": self.max_dur_entry.get()
            },
            "mouse": {
                "delay_min": self.delay_min_var.get(),
                "delay_max": self.delay_max_var.get(),
                "speed_min": self.speed_min_var.get(),
                "speed_max": self.speed_max_var.get(),
                "distance": self.distance_var.get(),
                "use_random": self.use_random_var.get(),
                "use_jump": self.use_jump_var.get(),
                "use_click": self.use_click_var.get()
            }
        }
        
        timestamp = datetime.now().strftime("%d.%H.%M.%S")
        default_name = f"config_{timestamp}.json"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=default_name,
            title="Salva Configurazione",
            filetypes=[("JSON files", "*.json"), ("Tutti i file", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Successo", "Configurazione salvata con successo!")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare:\n{str(e)}")

    def load_config(self):
        filepath = filedialog.askopenfilename(
            title="Carica Configurazione",
            filetypes=[("JSON files", "*.json"), ("Tutti i file", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    config = json.load(f)

                # --- Aggiorna Modulo Tastiera ---
                if "keyboard" in config:
                    kb = config["keyboard"]
                    self.selected_keys_list = kb.get("selected_keys", [])
                    self.constant_keys_list = kb.get("constant_keys", [])
                    self.update_listbox(self.selected_keys_list, self.listbox_main)
                    self.update_listbox(self.constant_keys_list, self.listbox_const)

                    self.const_interval_entry.delete(0, tk.END)
                    self.const_interval_entry.insert(0, kb.get("const_interval", "5.0"))
                    
                    self.min_cd_entry.delete(0, tk.END)
                    self.min_cd_entry.insert(0, kb.get("min_cd", "0.5"))
                    self.max_cd_entry.delete(0, tk.END)
                    self.max_cd_entry.insert(0, kb.get("max_cd", "2.0"))
                    
                    self.min_dur_entry.delete(0, tk.END)
                    self.min_dur_entry.insert(0, kb.get("min_dur", "0.1"))
                    self.max_dur_entry.delete(0, tk.END)
                    self.max_dur_entry.insert(0, kb.get("max_dur", "0.3"))

                # --- Aggiorna Modulo Mouse ---
                if "mouse" in config:
                    ms = config["mouse"]
                    self.delay_min_var.set(ms.get("delay_min", "2.0"))
                    self.delay_max_var.set(ms.get("delay_max", "5.0"))
                    self.speed_min_var.set(ms.get("speed_min", "0.5"))
                    self.speed_max_var.set(ms.get("speed_max", "1.5"))
                    
                    # Convertiamo in int nel caso provenga da una vecchia config basata su stringhe
                    self.distance_var.set(int(ms.get("distance", 150)))
                    
                    self.use_random_var.set(ms.get("use_random", True))
                    self.use_jump_var.set(ms.get("use_jump", True))
                    self.use_click_var.set(ms.get("use_click", True))

                messagebox.showinfo("Successo", "Configurazione caricata con successo!")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile caricare la configurazione:\n{str(e)}")

    # ==========================================
    # MODULO TASTIERA
    # ==========================================
    def toggle_kb_sim(self):
        if self.kb_stop_event.is_set():
            if not self.selected_keys_list:
                messagebox.showerror("Errore", "Seleziona almeno un tasto AFK principale.")
                return
            try:
                params = {
                    'min_cd': float(self.min_cd_entry.get() or 0.5),
                    'max_cd': float(self.max_cd_entry.get() or 2.0),
                    'min_dur': float(self.min_dur_entry.get() or 0.1),
                    'max_dur': float(self.max_dur_entry.get() or 0.3),
                    'const_int': float(self.const_interval_entry.get() or 5.0)
                }
            except ValueError:
                messagebox.showerror("Errore", "Controlla di aver inserito numeri validi.")
                return

            self.kb_stop_event.clear()
            self.btn_kb_start.config(text="FERMA MODULO TASTIERA", bg="#f38ba8")
            threading.Thread(target=self.kb_loop, args=(params,), daemon=True).start()
        else:
            self.stop_kb_sim()
        self.update_global_status()

    def stop_kb_sim(self):
        self.kb_stop_event.set()
        self.btn_kb_start.config(text="AVVIA MODULO TASTIERA", bg="#a6e3a1")
        self.update_global_status()

    def kb_loop(self, params):
        const_idx = 0
        const_timer = time.time()
        
        while not self.kb_stop_event.is_set():
            if self.constant_keys_list and (time.time() - const_timer >= params['const_int']):
                key = self.constant_keys_list[const_idx]
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
                const_idx = (const_idx + 1) % len(self.constant_keys_list)
                const_timer = time.time()

            main_key = random.choice(self.selected_keys_list)
            cd_time = random.uniform(params['min_cd'], params['max_cd'])
            
            # Attesa interrompibile
            if self.kb_stop_event.wait(cd_time):
                break # Se l'evento viene settato durante l'attesa, esci

            dur = random.uniform(params['min_dur'], params['max_dur'])
            keyboard.press(main_key)
            time.sleep(dur)
            keyboard.release(main_key)

    # ==========================================
    # MODULO MOUSE 3D
    # ==========================================
    def stoppable_sleep_with_countdown(self, duration):
        """Ottimizzato per non intasare il mainloop di Tkinter"""
        start_time = time.time()
        last_update = 0
        
        while not self.mouse_stop_event.is_set():
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            
            remaining = duration - elapsed
            # Aggiorna la GUI solo ogni 0.1s per non sovraccaricare Tkinter
            if time.time() - last_update > 0.1:
                self.root.after(0, lambda r=remaining: self.mouse_countdown_lbl.config(text=f"⏱️ Prossima mossa in: {r:.1f}s"))
                last_update = time.time()
                
            time.sleep(0.05)
            
        if not self.mouse_stop_event.is_set():
            self.root.after(0, lambda: self.mouse_countdown_lbl.config(text="⚙️ Movimento in corso..."))

    def toggle_mouse_sim(self):
        if self.mouse_stop_event.is_set():
            try:
                params = {
                    'dist': int(self.distance_var.get()),
                    'd_min': float(self.delay_min_var.get() or 2.0),
                    'd_max': float(self.delay_max_var.get() or 5.0),
                    's_min': float(self.speed_min_var.get() or 0.5),
                    's_max': float(self.speed_max_var.get() or 1.5)
                }
            except ValueError:
                messagebox.showerror("Errore", "Verifica che i valori del mouse siano numeri validi.")
                return

            self.mouse_stop_event.clear()
            self.btn_mouse_start.config(text="FERMA MODULO MOUSE 3D", bg="#f38ba8")
            threading.Thread(target=self.mouse_loop, args=(params,), daemon=True).start()
        else:
            self.stop_mouse_sim()
        self.update_global_status()

    def stop_mouse_sim(self):
        self.mouse_stop_event.set()
        self.btn_mouse_start.config(text="AVVIA MODULO MOUSE 3D", bg="#89b4fa")
        self.mouse_countdown_lbl.config(text="Fermo.")
        self.update_global_status()

    def perform_smooth_move(self, dx, dy, move_duration):
        steps = random.randint(30, 60)
        sleep_time = move_duration / steps
        acc_x, acc_y = 0.0, 0.0 
        
        for _ in range(steps):
            if self.mouse_stop_event.is_set(): break
            
            acc_x += dx / steps
            acc_y += dy / steps
            
            move_x, move_y = int(acc_x), int(acc_y)
            
            if move_x != 0 or move_y != 0:
                WinAPI.move_mouse_relative(move_x, move_y)
                acc_x -= move_x
                acc_y -= move_y
                
            time.sleep(sleep_time)

    def mouse_loop(self, p):
        self.stoppable_sleep_with_countdown(3.0) 
        
        while not self.mouse_stop_event.is_set():
            is_random = self.use_random_var.get()
            move_duration = random.uniform(p['s_min'], p['s_max'])
            delay_time = random.uniform(p['d_min'], p['d_max'])

            if is_random:
                dx = random.randint(-p['dist'], p['dist'])
                dy = random.randint(-p['dist'], p['dist'])
            else:
                dx, dy = 0, p['dist']

            self.perform_smooth_move(dx, dy, move_duration)
            if self.mouse_stop_event.is_set(): break

            if self.use_jump_var.get() and random.random() < 0.25:
                WinAPI.press_space()
            if self.use_click_var.get() and random.random() < 0.35:
                WinAPI.click_mouse()

            if not is_random and not self.mouse_stop_event.is_set():
                time.sleep(0.2) 
                self.perform_smooth_move(0, -dy, move_duration)

            if self.mouse_stop_event.is_set(): break
            self.stoppable_sleep_with_countdown(delay_time)

    # ==========================================
    # KILL SWITCH GLOBALE
    # ==========================================
    def global_esc_monitor(self):
        while not self.monitor_stop_event.is_set():
            if WinAPI.is_esc_pressed():
                if not self.kb_stop_event.is_set():
                    self.root.after(0, self.stop_kb_sim)
                if not self.mouse_stop_event.is_set():
                    self.root.after(0, self.stop_mouse_sim)
            time.sleep(0.05)

    def on_closing(self):
        self.monitor_stop_event.set()
        self.kb_stop_event.set()
        self.mouse_stop_event.set()
        keyboard.unhook_all()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateAntiAFK(root)
    root.mainloop()
