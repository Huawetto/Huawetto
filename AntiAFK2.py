import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import threading
import time
import math

# Costanti Windows per il movimento del mouse e input tastiera
MOUSEEVENTF_MOVE = 0x0001
VK_ESCAPE = 0x1B  # Codice tasto ESC

class MouseSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Motion Pro - Gaming Edition")
        self.root.geometry("400x580")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        # Variabili di stato
        self.is_running = False
        self.distance_var = tk.StringVar(value="300")
        self.speed_var = tk.StringVar(value="1.0")
        self.movement_thread = None

        # Configurazione Stile
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#fab387")
        self.style.configure("Status.TLabel", font=("Segoe UI", 9, "italic"), foreground="#a6adc8")
        self.style.configure("Warning.TLabel", font=("Segoe UI", 9, "bold"), foreground="#f38ba8", background="#1e1e2e")

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(main_frame, text="GAMING MOUSE SIM", style="Header.TLabel")
        header.pack(pady=(0, 10))

        sub_header = ttk.Label(main_frame, text="Ottimizzato per Minecraft e FPS", style="Status.TLabel")
        sub_header.pack(pady=(0, 20))

        # Input Distanza
        ttk.Label(main_frame, text="Ampiezza Movimento (Pixel/Gradi):").pack(anchor=tk.W, pady=(10, 5))
        self.dist_entry = tk.Entry(main_frame, textvariable=self.distance_var, 
                                   bg="#313244", fg="#ffffff", borderwidth=0,
                                   insertbackground="white", font=("Segoe UI", 11), justify='center')
        self.dist_entry.pack(fill=tk.X, ipady=8)

        # Input Velocità
        ttk.Label(main_frame, text="Tempo Ciclo (Secondi):").pack(anchor=tk.W, pady=(15, 5))
        self.speed_entry = tk.Entry(main_frame, textvariable=self.speed_var, 
                                    bg="#313244", fg="#ffffff", borderwidth=0,
                                    insertbackground="white", font=("Segoe UI", 11), justify='center')
        self.speed_entry.pack(fill=tk.X, ipady=8)

        # Spiegazione Tecnica
        desc = "Utilizza l'API Hardware 'mouse_event' per\n bypassare i blocchi dei giochi 3D."
        ttk.Label(main_frame, text=desc, style="Status.TLabel", justify=tk.CENTER).pack(pady=20)

        # Alert ESC
        self.esc_label = ttk.Label(main_frame, text="PREMI 'ESC' PER STOP IMMEDIATO", style="Warning.TLabel")
        self.esc_label.pack(pady=(0, 10))

        # Pulsante Action
        self.btn_text = tk.StringVar(value="AVVIA MODALITÀ GIOCO")
        self.action_btn = tk.Button(main_frame, textvariable=self.btn_text, 
                                    command=self.toggle_simulation,
                                    bg="#fab387", fg="#1e1e2e", font=("Segoe UI", 11, "bold"),
                                    relief=tk.FLAT, cursor="hand2", activebackground="#f9e2af")
        self.action_btn.pack(fill=tk.X, pady=(10, 0), ipady=12)

        # Status
        self.status_var = tk.StringVar(value="Sistema Pronto")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_bar.pack(side=tk.BOTTOM, pady=(20, 0))

    def move_mouse_relative(self, x, y):
        """Invia input relativo a basso livello (Hardware-like)."""
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)

    def is_esc_pressed(self):
        """Controlla se il tasto ESC è premuto globalmente su Windows."""
        return ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000

    def toggle_simulation(self):
        if not self.is_running:
            try:
                dist = int(self.distance_var.get())
                duration = float(self.speed_var.get())
                if duration <= 0.1: duration = 0.1
                
                self.is_running = True
                self.btn_text.set("STOP ATTIVO")
                self.action_btn.configure(bg="#f38ba8")
                self.status_var.set("Simulazione in corso...")
                
                # Avvio thread movimento
                self.movement_thread = threading.Thread(target=self.run_gaming_loop, args=(dist, duration), daemon=True)
                self.movement_thread.start()
                
                # Avvio thread monitoraggio ESC
                threading.Thread(target=self.monitor_esc, daemon=True).start()
                
            except ValueError:
                messagebox.showerror("Errore", "Inserisci numeri validi.")
        else:
            self.stop_simulation()

    def monitor_esc(self):
        """Thread dedicato al controllo del tasto ESC."""
        while self.is_running:
            if self.is_esc_pressed():
                # Usa .after per interagire in sicurezza con la GUI dal thread
                self.root.after(0, self.stop_simulation)
                break
            time.sleep(0.05) # Controllo ogni 50ms per massima reattività

    def stop_simulation(self):
        if not self.is_running: return
        self.is_running = False
        self.btn_text.set("AVVIA MODALITÀ GIOCO")
        self.action_btn.configure(bg="#fab387")
        self.status_var.set("STOPPED via ESC/Manuale")

    def run_gaming_loop(self, total_dist, duration):
        """Loop ottimizzato per motori grafici 3D con controllo interruzione."""
        steps = 100
        sleep_time = (duration / 2) / steps
        
        # Pausa iniziale
        time.sleep(0.5)
        
        while self.is_running:
            # Movimento GIÙ
            for _ in range(steps):
                if not self.is_running: break
                self.move_mouse_relative(0, total_dist / steps)
                time.sleep(sleep_time)
            
            # Movimento SU
            for _ in range(steps):
                if not self.is_running: break
                self.move_mouse_relative(0, -(total_dist / steps))
                time.sleep(sleep_time)

if __name__ == "__main__":
    root = tk.Tk()
    app = MouseSimulatorApp(root)
    root.mainloop()
