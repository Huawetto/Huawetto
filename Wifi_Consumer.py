import requests
import threading
import time

# === CONFIGURAZIONE ===
THREADS = 150  # Più thread = più traffico
CHUNK = 1024 * 1024  # 1MB
URLS = [
    "http://speed.hetzner.de/1GB.bin",
    "http://mirror.internode.on.net/pub/test/200meg.test",
    "http://speedtest.tele2.net/100MB.zip",
    "http://ipv4.download.thinkbroadband.com/512MB.zip",
    "http://speed.hetzner.de/10GB.bin",
    "http://ipv4.download.thinkbroadband.com/1GB.zip",
    "http://speedtest.tele2.net/1GB.zip",
    "http://speedtest-sgp1.digitalocean.com/1gb.test"
]

# === VARIABILE GLOBALE ===
total_bytes = 0
lock = threading.Lock()

def downloader(url):
    global total_bytes
    headers = {"User-Agent": "Mozilla/5.0"}
    while True:
        try:
            with requests.get(url, stream=True, headers=headers, timeout=10) as r:
                for chunk in r.iter_content(chunk_size=CHUNK):
                    if not chunk:
                        break
                    with lock:
                        total_bytes += len(chunk)
        except:
            continue

def logger():
    global total_bytes
    last_bytes = 0
    while True:
        time.sleep(0.3)
        with lock:
            current = total_bytes
        delta = current - last_bytes
        last_bytes = current
        speed = delta / (1024 * 1024)
        downloaded = current / (1024 * 1024 * 1024)
        print(f"🔥 Speed: {speed:.2f} MB/s | Total: {downloaded:.2f} GB")

def main():
    print("🚀 Avvio flood. Ctrl+C per uscire.\n")
    for i in range(THREADS):
        url = URLS[i % len(URLS)]
        t = threading.Thread(target=downloader, args=(url,), daemon=True)
        t.start()

    logger()

if __name__ == "__main__":
    main()
