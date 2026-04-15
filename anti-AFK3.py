import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import threading
import time
import random
import keyboard

# --- Costanti Windows per input Hardware ---
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
KEYEVENTF_KEYUP = 0x0002

class UltimateAntiAFK:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Anti-AFK Pro - Multi-Tool")
        self.root.geometry("780x700")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        # --- Variabili di Stato Globali ---
        self.kb_running = False
        self.mouse_running = False
        self.kb_thread = None
        self.mouse_thread = None
        self.monitor_thread_active = True

        # --- Variabili Modulo Tastiera ---
        self.selected_keys_list = ["w", "s", "a", "d", "space"]
        self.constant_keys_list = ["shift"]
        
        # Lista completa di tutti i tasti supportati
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
        self.distance_var = tk.StringVar(value="150")
        self.use_jump_var = tk.BooleanVar(value=True)
        self.use_click_var = tk.BooleanVar(value=True)
        self.use_random_var = tk.BooleanVar(value=True)
        
        # Nuove variabili per Delay e Velocità
        self.delay_min_var = tk.StringVar(value="2.0")
        self.delay_max_var = tk.StringVar(value="5.0")
        self.speed_min_var = tk.StringVar(value="0.5")
        self.speed_max_var = tk.StringVar(value="1.5")

        self.setup_styles()
        self.create_gui()

        # Avvia monitor globale tasto ESC
        threading.Thread(target=self.global_esc_monitor, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colori base Catppuccin-like
        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        accent_green = "#a6e3a1"
        accent_red = "#f38ba8"
        panel_bg = "#313244"
        accent_blue = "#89b4fa"

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
        # Header globale
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="ULTIMATE ANTI-AFK SUITE", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="PREMI 'ESC' PER FERMARE TUTTO", style="Warning.TLabel").pack(side=tk.RIGHT)

        # Creazione Notebook (Schede)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- SCHEDA 1: TASTIERA ---
        self.tab_kb = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.tab_kb, text="⌨️ Simulatore Tastiera (MMO/2D)")
        self.build_keyboard_tab()

        # --- SCHEDA 2: MOUSE & 3D ---
        self.tab_mouse = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.tab_mouse, text="🖱️ Mouse 3D & Hardware (MC/FPS)")
        self.build_mouse_tab()

        # --- BARRA DI STATO GLOBALE ---
        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.global_status_lbl = ttk.Label(status_frame, text="Stato Globale: In attesa...", font=("Segoe UI", 10, "italic"))
        self.global_status_lbl.pack(side=tk.LEFT)

    # ==========================================
    # COSTRUZIONE INTERFACCIA: MODULO TASTIERA
    # ==========================================
    def build_keyboard_tab(self):
        main_container = ttk.Frame(self.tab_kb)
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)

        # -- Sinistra: Tasti AFK Principali --
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

        # -- Destra: Tasti Costanti & Parametri --
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
        self.const_interval_entry = tk.Entry(right_panel, bg="#1e1e2e", fg="white", borderwidth=0, insertbackground="white")
        self.const_interval_entry.insert(0, "5.0")
        self.const_interval_entry.pack(fill=tk.X, pady=5, ipady=3)

        # -- Parametri Timing (Sotto) --
        params_frame = ttk.Frame(self.tab_kb)
        params_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(params_frame, text="Ritardo tra i tasti Min/Max (s):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.min_cd_entry = tk.Entry(params_frame, width=8, bg="#313244", fg="white", borderwidth=0)
        self.min_cd_entry.insert(0, "0.5")
        self.min_cd_entry.grid(row=0, column=1, padx=5, pady=5, ipady=3)
        self.max_cd_entry = tk.Entry(params_frame, width=8, bg="#313244", fg="white", borderwidth=0)
        self.max_cd_entry.insert(0, "2.0")
        self.max_cd_entry.grid(row=0, column=2, padx=5, pady=5, ipady=3)

        ttk.Label(params_frame, text="Durata pressione Min/Max (s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.min_dur_entry = tk.Entry(params_frame, width=8, bg="#313244", fg="white", borderwidth=0)
        self.min_dur_entry.insert(0, "0.1")
        self.min_dur_entry.grid(row=1, column=1, padx=5, pady=5, ipady=3)
        self.max_dur_entry = tk.Entry(params_frame, width=8, bg="#313244", fg="white", borderwidth=0)
        self.max_dur_entry.insert(0, "0.3")
        self.max_dur_entry.grid(row=1, column=2, padx=5, pady=5, ipady=3)

        # Pulsanti Controllo Tastiera
        self.btn_kb_start = tk.Button(self.tab_kb, text="AVVIA MODULO TASTIERA", command=self.toggle_kb_sim, bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 11, "bold"), borderwidth=0, cursor="hand2")
        self.btn_kb_start.pack(fill=tk.X, pady=10, ipady=8)

    # ==========================================
    # COSTRUZIONE INTERFACCIA: MODULO MOUSE 3D
    # ==========================================
    def build_mouse_tab(self):
        desc = "Utilizza API Hardware per muovere il cursore. Include randomizzazione per bypassare controlli euristici."
        ttk.Label(self.tab_mouse, text=desc, font=("Segoe UI", 9, "italic")).pack(pady=(0, 10))

        # --- SEZIONE 1: TEMPI E VELOCITÀ ---
        time_frame = ttk.LabelFrame(self.tab_mouse, text="⌚ Tempi e Velocità (Secondi)")
        time_frame.pack(fill=tk.X, pady=5, ipady=5, ipadx=5)
        
        # Pausa tra movimenti
        ttk.Label(time_frame, text="Pausa tra mosse (Min - Max):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(time_frame, textvariable=self.delay_min_var, width=8, bg="#313244", fg="white", borderwidth=0, justify='center').grid(row=0, column=1, padx=5, pady=5, ipady=4)
        tk.Entry(time_frame, textvariable=self.delay_max_var, width=8, bg="#313244", fg="white", borderwidth=0, justify='center').grid(row=0, column=2, padx=5, pady=5, ipady=4)

        # Velocità movimento cursore
        ttk.Label(time_frame, text="Durata spostamento (Veloce - Lento):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(time_frame, textvariable=self.speed_min_var, width=8, bg="#313244", fg="white", borderwidth=0, justify='center').grid(row=1, column=1, padx=5, pady=5, ipady=4)
        tk.Entry(time_frame, textvariable=self.speed_max_var, width=8, bg="#313244", fg="white", borderwidth=0, justify='center').grid(row=1, column=2, padx=5, pady=5, ipady=4)

        # --- SEZIONE 2: MOVIMENTO ---
        move_frame = ttk.LabelFrame(self.tab_mouse, text="🎯 Parametri Movimento")
        move_frame.pack(fill=tk.X, pady=5, ipady=5, ipadx=5)

        ttk.Label(move_frame, text="Ampiezza Max Movimento (Pixel):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(move_frame, textvariable=self.distance_var, width=15, bg="#313244", fg="white", borderwidth=0, justify='center').grid(row=0, column=1, padx=5, pady=5, ipady=4)

        # --- SEZIONE 3: AZIONI EXTRA ---
        opts_frame = ttk.LabelFrame(self.tab_mouse, text="⚙️ Azioni Anti-Cheat Casuali")
        opts_frame.pack(fill=tk.X, pady=5, ipady=5, ipadx=10)
        
        ttk.Checkbutton(opts_frame, text="Direzione Casuale 360° (Consigliato)", variable=self.use_random_var).pack(anchor=tk.W, pady=2, padx=10)
        ttk.Checkbutton(opts_frame, text="Auto-Salto occasionale (Spazio - Livello Hardware)", variable=self.use_jump_var).pack(anchor=tk.W, pady=2, padx=10)
        ttk.Checkbutton(opts_frame, text="Auto-Click occasionale (Tasto Sinistro - Livello Hardware)", variable=self.use_click_var).pack(anchor=tk.W, pady=2, padx=10)

        # --- COUNTDOWN DISPLAY ---
        self.mouse_countdown_lbl = ttk.Label(self.tab_mouse, text="In attesa di avvio...", style="Countdown.TLabel")
        self.mouse_countdown_lbl.pack(pady=10)

        # Pulsante Controllo Mouse
        self.btn_mouse_start = tk.Button(self.tab_mouse, text="AVVIA MODULO MOUSE 3D", command=self.toggle_mouse_sim, bg="#89b4fa", fg="#1e1e2e", font=("Segoe UI", 11, "bold"), borderwidth=0, cursor="hand2")
        self.btn_mouse_start.pack(fill=tk.X, side=tk.BOTTOM, pady=5, ipady=8)

    # ==========================================
    # FUNZIONI LOGICA GUI (Liste e Utility)
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
        kb_st = "🟢 ATTIVO" if self.kb_running else "🔴 FERMO"
        ms_st = "🟢 ATTIVO" if self.mouse_running else "🔴 FERMO"
        self.root.after(0, lambda: self.global_status_lbl.config(text=f"Stato Globale | Tastiera: {kb_st} | Mouse 3D: {ms_st}"))

    # ==========================================
    # LOGICA HARDWARE / API WINDOWS
    # ==========================================
    def is_esc_pressed(self):
        return ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000

    def move_mouse_relative(self, x, y):
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)

    def hw_mouse_click(self):
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def hw_press_space(self):
        ctypes.windll.user32.keybd_event(VK_SPACE, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.2))
        ctypes.windll.user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)

    # ==========================================
    # THREAD 1: SIMULATORE TASTIERA
    # ==========================================
    def toggle_kb_sim(self):
        if not self.kb_running:
            try:
                if not self.selected_keys_list:
                    raise ValueError("Seleziona almeno un tasto AFK principale.")
                params = {
                    'min_cd': float(self.min_cd_entry.get()),
                    'max_cd': float(self.max_cd_entry.get()),
                    'min_dur': float(self.min_dur_entry.get()),
                    'max_dur': float(self.max_dur_entry.get()),
                    'const_int': float(self.const_interval_entry.get())
                }
                self.kb_running = True
                self.btn_kb_start.config(text="FERMA MODULO TASTIERA", bg="#f38ba8")
                self.kb_thread = threading.Thread(target=self.kb_loop, args=(params,), daemon=True)
                self.kb_thread.start()
            except ValueError as e:
                messagebox.showerror("Errore", str(e))
        else:
            self.stop_kb_sim()
        self.update_global_status()

    def stop_kb_sim(self):
        self.kb_running = False
        self.btn_kb_start.config(text="AVVIA MODULO TASTIERA", bg="#a6e3a1")
        self.update_global_status()

    def kb_loop(self, params):
        const_idx = 0
        const_timer = time.time()
        
        while self.kb_running:
            if self.constant_keys_list and (time.time() - const_timer >= params['const_int']):
                key = self.constant_keys_list[const_idx]
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
                const_idx = (const_idx + 1) % len(self.constant_keys_list)
                const_timer = time.time()

            main_key = random.choice(self.selected_keys_list)
            cd_time = random.uniform(params['min_cd'], params['max_cd'])
            
            start_wait = time.time()
            while time.time() - start_wait < cd_time and self.kb_running:
                time.sleep(0.05)
            
            if not self.kb_running: break

            dur = random.uniform(params['min_dur'], params['max_dur'])
            keyboard.press(main_key)
            time.sleep(dur)
            keyboard.release(main_key)

    # ==========================================
    # THREAD 2: SIMULATORE MOUSE 3D & HARDWARE
    # ==========================================
    def stoppable_sleep_with_countdown(self, duration):
        """Pausa che aggiorna la GUI e può essere interrotta immediatamente."""
        start_time = time.time()
        while time.time() - start_time < duration and self.mouse_running:
            remaining = duration - (time.time() - start_time)
            # Aggiorna label in modo sicuro per Tkinter
            self.root.after(0, lambda r=remaining: self.mouse_countdown_lbl.config(text=f"⏱️ Prossima mossa in: {r:.1f}s"))
            time.sleep(0.05)
        self.root.after(0, lambda: self.mouse_countdown_lbl.config(text="⚙️ Movimento in corso..."))

    def toggle_mouse_sim(self):
        if not self.mouse_running:
            try:
                params = {
                    'dist': int(self.distance_var.get()),
                    'd_min': float(self.delay_min_var.get()),
                    'd_max': float(self.delay_max_var.get()),
                    's_min': float(self.speed_min_var.get()),
                    's_max': float(self.speed_max_var.get())
                }
                self.mouse_running = True
                self.btn_mouse_start.config(text="FERMA MODULO MOUSE 3D", bg="#f38ba8")
                self.mouse_thread = threading.Thread(target=self.mouse_loop, args=(params,), daemon=True)
                self.mouse_thread.start()
            except ValueError:
                messagebox.showerror("Errore", "Verifica che i valori del mouse siano numeri validi.")
        else:
            self.stop_mouse_sim()
        self.update_global_status()

    def stop_mouse_sim(self):
        self.mouse_running = False
        self.btn_mouse_start.config(text="AVVIA MODULO MOUSE 3D", bg="#89b4fa")
        self.mouse_countdown_lbl.config(text="Fermo.")
        self.update_global_status()

    def perform_smooth_move(self, dx, dy, move_duration):
        """Esegue un movimento fluido accumulando i decimali per non perdere precisione"""
        steps = random.randint(30, 60)
        sleep_time = move_duration / steps
        
        # Accumulatori per i pixel frazionari
        acc_x, acc_y = 0.0, 0.0 
        
        for _ in range(steps):
            if not self.mouse_running: break
            
            acc_x += dx / steps
            acc_y += dy / steps
            
            move_x, move_y = int(acc_x), int(acc_y)
            
            if move_x != 0 or move_y != 0:
                self.move_mouse_relative(move_x, move_y)
                acc_x -= move_x
                acc_y -= move_y
                
            time.sleep(sleep_time)

    def mouse_loop(self, p):
        # Countdown iniziale per dare tempo all'utente di tornare in gioco
        self.stoppable_sleep_with_countdown(3.0) 
        
        while self.mouse_running:
            is_random = self.use_random_var.get()
            
            # Calcola velocità del movimento e pausa
            move_duration = random.uniform(p['s_min'], p['s_max'])
            delay_time = random.uniform(p['d_min'], p['d_max'])

            if is_random:
                dx = random.randint(-p['dist'], p['dist'])
                dy = random.randint(-p['dist'], p['dist'])
            else:
                dx, dy = 0, p['dist']

            # Movimento andata
            self.perform_smooth_move(dx, dy, move_duration)
            if not self.mouse_running: break

            # Azioni casuali Hardware (click / salto)
            if self.use_jump_var.get() and random.random() < 0.25:
                self.hw_press_space()
            if self.use_click_var.get() and random.random() < 0.35:
                self.hw_mouse_click()

            # Movimento ritorno (se non è random, per riposizionare la telecamera)
            if not is_random and self.mouse_running:
                time.sleep(0.2) # Piccola pausa al culmine del movimento
                self.perform_smooth_move(0, -dy, move_duration)

            if not self.mouse_running: break

            # Attesa prima del prossimo ciclo (con aggiornamento UI)
            self.stoppable_sleep_with_countdown(delay_time)

    # ==========================================
    # THREAD GLOBALE: EMERGENZA (KILL SWITCH)
    # ==========================================
    def global_esc_monitor(self):
        while self.monitor_thread_active:
            if self.is_esc_pressed():
                if self.kb_running:
                    self.root.after(0, self.stop_kb_sim)
                if self.mouse_running:
                    self.root.after(0, self.stop_mouse_sim)
            time.sleep(0.05)

    def on_closing(self):
        self.monitor_thread_active = False
        self.kb_running = False
        self.mouse_running = False
        self.root.destroy()
        keyboard.unhook_all()

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateAntiAFK(root)
    root.mainloop()