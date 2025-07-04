import keyboard
import time
import random
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class AntiAFKApp:
    def __init__(self, master):
        self.master = master
        master.title("Anti-AFK Tool Pro")
        master.geometry("550x650") # Slightly larger for new elements
        master.resizable(False, False)

        self.is_running = False
        self.simulation_thread = None
        self.selected_keys = set() # To store currently selected keys

        self.create_widgets()

        keyboard.add_hotkey('esc', self.stop_simulation_hotkey)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))
        style.configure('TEntry', font=('Arial', 10))
        style.configure('TCheckbutton', background='#f0f0f0', font=('Arial', 10))

        main_frame = ttk.Frame(self.master, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Anti-AFK Settings", font=('Arial', 18, 'bold'))
        title_label.pack(pady=15)

        # --- Key Selection Section ---
        keys_frame = ttk.LabelFrame(main_frame, text="Select Keys to Simulate", padding="10")
        keys_frame.pack(pady=10, fill=tk.X)

        self.all_possible_keys = [
            'w', 'a', 's', 'd', 'space', 'left shift', 'right shift',
            'tab', 'enter', 'esc', 'ctrl', 'alt', 'f1', 'f2', 'f3', 'f4', 'f5',
            'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', '1', '2', '3', '4', '5',
            '6', '7', '8', '9', '0', 'q', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'g', 'h', 'j', 'k', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm'
        ]
        self.all_possible_keys.sort() # Alphabetical order

        ttk.Label(keys_frame, text="Choose a key:").pack(side=tk.LEFT, padx=(0, 5))
        self.key_dropdown_var = tk.StringVar(self.master)
        self.key_dropdown_var.set("Select Key") # Default text
        self.key_dropdown = ttk.OptionMenu(keys_frame, self.key_dropdown_var, "Select Key", *self.all_possible_keys)
        self.key_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        add_key_button = ttk.Button(keys_frame, text="Add Key", command=self.add_selected_key)
        add_key_button.pack(side=tk.LEFT, padx=(0, 5))

        remove_key_button = ttk.Button(keys_frame, text="Remove Key", command=self.remove_selected_key)
        remove_key_button.pack(side=tk.LEFT)

        ttk.Label(main_frame, text="Selected Keys:").pack(anchor='w', pady=(10, 2))
        self.selected_keys_listbox = tk.Listbox(main_frame, height=4, selectmode=tk.SINGLE, width=50, font=('Arial', 10))
        self.selected_keys_listbox.pack(pady=5)
        # Populate with default keys if desired
        for key in ["w", "s", "a", "d", "space"]:
            self.selected_keys.add(key)
            self.selected_keys_listbox.insert(tk.END, key)

        # --- Simulation Parameters Section ---
        params_frame = ttk.LabelFrame(main_frame, text="Simulation Parameters", padding="10")
        params_frame.pack(pady=10, fill=tk.X)

        ttk.Label(params_frame, text="Min/Max Countdown (s):").grid(row=0, column=0, sticky='w', pady=2, padx=5)
        self.countdown_min_entry = ttk.Entry(params_frame, width=10)
        self.countdown_min_entry.insert(0, "0.3")
        self.countdown_min_entry.grid(row=0, column=1, sticky='ew', pady=2, padx=2)
        self.countdown_max_entry = ttk.Entry(params_frame, width=10)
        self.countdown_max_entry.insert(0, "1.5")
        self.countdown_max_entry.grid(row=0, column=2, sticky='ew', pady=2, padx=2)

        ttk.Label(params_frame, text="Min/Max Press Duration (s):").grid(row=1, column=0, sticky='w', pady=2, padx=5)
        self.duration_min_entry = ttk.Entry(params_frame, width=10)
        self.duration_min_entry.insert(0, "0.05")
        self.duration_min_entry.grid(row=1, column=1, sticky='ew', pady=2, padx=2)
        self.duration_max_entry = ttk.Entry(params_frame, width=10)
        self.duration_max_entry.insert(0, "0.25")
        self.duration_max_entry.grid(row=1, column=2, sticky='ew', pady=2, padx=2)

        ttk.Label(params_frame, text="Space Key Skip Chance (0.0-1.0):").grid(row=2, column=0, sticky='w', pady=2, padx=5)
        self.space_skip_entry = ttk.Entry(params_frame, width=10)
        self.space_skip_entry.insert(0, "0.7")
        self.space_skip_entry.grid(row=2, column=1, columnspan=2, sticky='ew', pady=2, padx=2)

        # --- Shift Key Specific Section ---
        shift_frame = ttk.LabelFrame(main_frame, text="Shift Key Behavior", padding="10")
        shift_frame.pack(pady=10, fill=tk.X)

        ttk.Label(shift_frame, text="Shift Key Probability (0.0-1.0):").grid(row=0, column=0, sticky='w', pady=2, padx=5)
        self.shift_prob_entry = ttk.Entry(shift_frame, width=10)
        self.shift_prob_entry.insert(0, "0.1")
        self.shift_prob_entry.grid(row=0, column=1, columnspan=2, sticky='ew', pady=2, padx=2)

        ttk.Label(shift_frame, text="Shift Key Duration (s):").grid(row=1, column=0, sticky='w', pady=2, padx=5)
        self.shift_duration_entry = ttk.Entry(shift_frame, width=10)
        self.shift_duration_entry.insert(0, "2.0")
        self.shift_duration_entry.grid(row=1, column=1, columnspan=2, sticky='ew', pady=2, padx=2)
        
        # --- Control Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)

        self.start_button = ttk.Button(button_frame, text="Start Anti-AFK", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=15)

        self.stop_button = ttk.Button(button_frame, text="Stop Anti-AFK", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=15)

        # --- Status & Instructions ---
        self.status_label = ttk.Label(main_frame, text="Status: Idle", font=('Arial', 10, 'italic'), foreground="blue")
        self.status_label.pack(pady=5)

        ttk.Label(main_frame, text="Press 'ESC' key at any time to forcefully stop the simulation.", font=('Arial', 9), foreground="gray").pack(pady=5)

    def add_selected_key(self):
        key = self.key_dropdown_var.get()
        if key and key != "Select Key" and key not in self.selected_keys:
            self.selected_keys.add(key)
            self.selected_keys_listbox.insert(tk.END, key)
            self.key_dropdown_var.set("Select Key") # Reset dropdown

    def remove_selected_key(self):
        selected_index = self.selected_keys_listbox.curselection()
        if selected_index:
            key_to_remove = self.selected_keys_listbox.get(selected_index[0])
            self.selected_keys.discard(key_to_remove)
            self.selected_keys_listbox.delete(selected_index[0])

    def parse_inputs(self):
        try:
            keys_to_simulate = list(self.selected_keys)
            if not keys_to_simulate:
                raise ValueError("Please select at least one key to simulate.")
            
            min_countdown = float(self.countdown_min_entry.get())
            max_countdown = float(self.countdown_max_entry.get())
            if not (0 < min_countdown <= max_countdown):
                raise ValueError("Countdown times must be positive and min <= max.")

            min_duration = float(self.duration_min_entry.get())
            max_duration = float(self.duration_max_entry.get())
            if not (0 < min_duration <= max_duration):
                raise ValueError("Press durations must be positive and min <= max.")
            
            space_skip_chance = float(self.space_skip_entry.get())
            if not (0.0 <= space_skip_chance <= 1.0):
                raise ValueError("Space skip chance must be between 0.0 and 1.0.")
            
            shift_prob = float(self.shift_prob_entry.get())
            if not (0.0 <= shift_prob <= 1.0):
                raise ValueError("Shift probability must be between 0.0 and 1.0.")
            
            shift_duration = float(self.shift_duration_entry.get())
            if not (shift_duration > 0):
                raise ValueError("Shift duration must be positive.")

            return keys_to_simulate, min_countdown, max_countdown, min_duration, max_duration, space_skip_chance, shift_prob, shift_duration
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please check your input values: {e}")
            return None

    def simulate_keys(self, keys_to_simulate, min_countdown, max_countdown, min_duration, max_duration, space_skip_chance, shift_prob, shift_duration):
        while self.is_running:
            if not self.is_running:
                break

            action_type_choices = ['movement']
            action_type_weights = [1 - shift_prob]
            if shift_prob > 0: # Only add shift if probability > 0
                action_type_choices.append('shift')
                action_type_weights.append(shift_prob)

            action_type = random.choices(action_type_choices, weights=action_type_weights, k=1)[0]

            if action_type == 'shift':
                self.update_status(f"Action: Pressing SHIFT for {shift_duration:.2f}s...")
                keyboard.press('shift')
                time.sleep(shift_duration)
                keyboard.release('shift')
                time.sleep(random.uniform(0.8, 2.5))
            else:
                selected_key = random.choice(keys_to_simulate)
                
                if selected_key == 'space' and random.random() < space_skip_chance:
                    self.update_status("Action: Skipping Space key...")
                    time.sleep(random.uniform(0.1, 0.5))
                    continue
                
                countdown_time = random.uniform(min_countdown, max_countdown)
                self.update_status(f"Next in {countdown_time:.2f}s. Key: {selected_key.upper()}")
                time.sleep(countdown_time)

                press_duration = random.uniform(min_duration, max_duration)
                self.update_status(f"Action: Pressing {selected_key.upper()} for {press_duration:.3f}s...")
                keyboard.press(selected_key)
                time.sleep(press_duration)
                keyboard.release(selected_key)
            
            time.sleep(random.uniform(0.1, 0.5))

        self.update_status("Status: Simulation Stopped.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def start_simulation(self):
        if self.is_running:
            return

        params = self.parse_inputs()
        if params is None:
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(foreground="green")
        
        self.simulation_thread = threading.Thread(target=self.simulate_keys, args=params, daemon=True)
        self.simulation_thread.start()
        self.update_status("Status: Simulation Running...")

    def stop_simulation(self):
        if not self.is_running:
            return
        self.is_running = False
        self.update_status("Status: Stopping simulation...")

    def stop_simulation_hotkey(self):
        if self.is_running:
            self.stop_simulation()
            self.update_status("Status: Simulation stopped by ESC key.")

    def update_status(self, message):
        self.master.after(0, lambda: self.status_label.config(text=message))

    def on_closing(self):
        self.stop_simulation()
        if self.simulation_thread and self.simulation_thread.is_alive():
            time.sleep(0.1) 
        self.master.destroy()
        keyboard.unhook_all()

if __name__ == "__main__":
    root = tk.Tk()
    app = AntiAFKApp(root)
    root.mainloop()
