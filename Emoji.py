#!/usr/bin/env python3
"""
Script: emoji_by_year_html.py

Descrizione:
Scarica l’ultima versione di “emoji-test.txt” dal sito ufficiale Unicode,
analizza ogni riga per estrarre tutte le emoji (fully-qualified, minimally-qualified e unqualified),
le raggruppa in base all’anno di introduzione, rilevando automaticamente soltanto gli anni
per cui esistono emoji. Offre inoltre due categorie speciali:
  • "removed" — emoji il cui token di versione non è mappato (ipoteticamente rimosse o non più standard)
  • "hidden"  — emoji presenti nel test ma non “fully-qualified” (minimally-qualified o unqualified), spesso nascoste sui social
  • "9999"    — code point Unicode casuali non presenti nelle emoji ufficiali
All’avvio, mostra tutte le categorie disponibili (anni reali, "hidden", "removed" e "9999").
L’utente digita l’anno (o "hidden", "removed" o "9999") per generare un file HTML temporaneo
con l’elenco delle emoji della categoria scelta (aperto direttamente nel browser predefinito).
Per uscire, digitare `exit`.

Dipendenze:
- Solo librerie standard di Python 3.

Uso:
    $ python3 emoji_by_year_html.py
    (attendere download e parsing)
    Categorie disponibili:
      2010
      2014
      2015
      2016
      2017
      2018
      2019
      2020
      2021
      2022
      2023
      2024
      hidden
      removed
      9999

    Inserisci un comando ('<categoria>' o 'exit'): 2024
    (si apre il browser con tutte le emoji del 2024)

    Inserisci un comando ('<categoria>' o 'exit'): hidden
    (si apre il browser con tutte le emoji presenti ma non fully-qualified)

    Inserisci un comando ('<categoria>' o 'exit'): removed
    (si apre il browser con tutte le emoji la cui versione non è mappata)

    Inserisci un comando ('<categoria>' o 'exit'): 9999
    (si apre il browser con emoji casuali “sconosciute”)

    Inserisci un comando ('<categoria>' o 'exit'): exit
    Arrivederci!
"""

import sys
import urllib.request
import tempfile
import os
import webbrowser
import random

# ----------------------------
# Mappatura versione Emoji → Anno
# ----------------------------
EMOJI_VERSION_TO_YEAR = {
    "E0.6": 2010,   # Unicode 6.0, 2010-10-11
    "E0.7": 2014,   # Unicode 7.0, 2014-06-16
    "E1.0": 2015,   # Emoji 1.0 / Unicode 8.0, 2015-06-09
    "E2.0": 2015,   # Emoji 2.0 / Unicode 8.0, 2015-11-12
    "E3.0": 2016,   # Emoji 3.0 / Unicode 9.0, 2016-06-03
    "E4.0": 2016,   # Emoji 4.0 / Unicode 9.0, 2016-11-22
    "E5.0": 2017,   # Emoji 5.0 / Unicode 10.0, 2017-06-20
    "E11.0": 2018,  # Emoji 11.0 / Unicode 11.0, 2018-05-21
    "E12.0": 2019,  # Emoji 12.0 / Unicode 12.0, 2019-03-05
    "E12.1": 2019,  # Emoji 12.1 / Unicode 12.1, 2019-10-21
    "E13.0": 2020,  # Emoji 13.0 / Unicode 13.0, 2020-03-10
    "E13.1": 2020,  # Emoji 13.1 / Unicode 13.0, 2020-09-15
    "E14.0": 2021,  # Emoji 14.0 / Unicode 14.0, 2021-09-14
    "E15.0": 2022,  # Emoji 15.0 / Unicode 15.0, 2022-09-13
    "E15.1": 2023,  # Emoji 15.1 / Unicode 15.1, 2023-09-12
    "E16.0": 2024,  # Emoji 16.0 / Unicode 16.0, 2024-09-10
    "E17.0": 2025,  # Emoji 17.0 (anticipato nel 2025)
    "E18.0": 2026,  # Emoji 18.0 (ipotetico nel 2026)
}

# Anni validi in stringa (2009–2026)
YEARS = [str(y) for y in range(2009, 2027)]

# ----------------------------
# Funzioni di parsing
# ----------------------------

def scarica_emoji_test(url="https://unicode.org/Public/emoji/latest/emoji-test.txt"):
    """
    Scarica il file emoji-test.txt e restituisce la lista di righe.
    """
    try:
        with urllib.request.urlopen(url) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return raw.splitlines()
    except Exception as e:
        print(f"Errore nel download di emoji-test.txt:\n  {e}")
        sys.exit(1)

def estrai_emoji_da_riga(line):
    """
    Se la riga di emoji-test.txt contiene una definizione di emoji, restituisce:
    (emoji_char, codepoints_list, version_token, name, status)
    Altrimenti None.
    """
    r = line.strip()
    if not r or r.startswith("#") or ";" not in r or "#" not in r:
        return None
    left, right = r.split("#", 1)
    left = left.strip()
    right = right.strip()
    parts_left = left.split(";")
    if len(parts_left) < 2:
        return None
    codepoints_str = parts_left[0].strip()      # es. "1F600" o "1F469 200D 1F467 200D 1F466"
    status = parts_left[1].strip()              # es. "fully-qualified", "minimally-qualified", "unqualified"
    tokens = right.split()
    if len(tokens) < 2:
        return None
    emoji_char = tokens[0]       # la rappresentazione testuale (singolo grapheme)
    version_token = tokens[1]    # es. "E1.0"
    name = " ".join(tokens[2:]).strip()
    codepoints_list = codepoints_str.split()
    return (emoji_char, codepoints_list, version_token, name, status)

def mappa_versione_a_anno(version_token):
    """
    Restituisce l'anno intero corrispondente alla versione Emoji,
    oppure None se non nel mapping.
    """
    return EMOJI_VERSION_TO_YEAR.get(version_token)

# ----------------------------
# Costruzione delle categorie
# ----------------------------

def costruisci_categorie_per_anno():
    """
    Scarica e analizza emoji-test.txt. Raggruppa le emoji per anno di introduzione.
    Le emoji con status diverso da 'fully-qualified' vanno in 'hidden'.
    Quelle con version_token non mappato vanno in 'removed'.
    Restituisce dict:
      {
        '2010': [ (char, codepoints, versione, nome, status), ... ],
        ...
        'hidden': [ ... ],
        'removed': [ ... ]
      }
    """
    righe = scarica_emoji_test()
    categories = {anno: [] for anno in YEARS}
    categories["hidden"] = []
    categories["removed"] = []

    for line in righe:
        dati = estrai_emoji_da_riga(line)
        if dati is None:
            continue
        emoji_char, codepoints_list, version_token, name, status = dati
        anno = mappa_versione_a_anno(version_token)
        if anno is None:
            # Versione non mappata → consideriamo "removed"
            categories["removed"].append((emoji_char, codepoints_list, version_token, name, status))
        else:
            anno_str = str(anno)
            if status == "fully-qualified":
                categories[anno_str].append((emoji_char, codepoints_list, version_token, name, status))
            else:
                # Minimally-qualified o unqualified → "hidden"
                categories["hidden"].append((emoji_char, codepoints_list, version_token, name, status))

    return categories

# ----------------------------
# Funzione per generare emoji “9999” (random sconosciute)
# ----------------------------

def genera_random_sconosciute(used_codepoints_set, count=100):
    """
    Genera una lista di 'count' code point Unicode casuali NON inclusi in used_codepoints_set,
    evitando la fascia riservata ai surrogate (0xD800–0xDFFF). Ritorna lista di tuple:
      [ (char, hex_code) , ... ]
    Alcuni potranno non essere visualizzati, ma fanno parte di code point "random/non-emoji".
    """
    sconosciute = []
    max_cp = 0x10FFFF
    attempts = 0
    while len(sconosciute) < count and attempts < count * 10:
        cp = random.randint(0, max_cp)
        if 0xD800 <= cp <= 0xDFFF or cp in used_codepoints_set:
            attempts += 1
            continue
        try:
            char = chr(cp)
            hex_code = f"{cp:04X}"
            sconosciute.append((char, hex_code))
        except ValueError:
            attempts += 1
            continue
        attempts += 1
    return sconosciute

# ----------------------------
# Funzioni HTML
# ----------------------------

def crea_html_per_categoria(cat_key, categories, temp_filepath):
    """
    Crea un file HTML in temp_filepath contenente tutte le emoji della categoria cat_key.
    Se cat_key == "9999", genera emoji random sconosciute.
    """
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='it'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        f"  <title>Emoji Categoria {cat_key}</title>",
        "  <style>",
        "    body { font-family: sans-serif; padding: 20px; }",
        "    table { border-collapse: collapse; width: 100%; }",
        "    th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
        "    th { background: #f0f0f0; }",
        "    td.char { font-size: 32px; text-align: center; width: 80px; }",
        "    td.name { width: 60%; }",
        "    td.code { font-family: monospace; }",
        "  </style>",
        "</head>",
        "<body>",
        f"  <h1>Emoji Categoria {cat_key}</h1>",
    ]

    if cat_key == "9999":
        # Costruisco l'insieme dei codepoint usati nelle emoji "fully-qualified"
        used_cp = set()
        for year, lista in categories.items():
            if year in ("hidden", "removed"):
                continue
            for (_char, cps, _ver, _name, _status) in lista:
                for cp_hex in cps:
                    used_cp.add(int(cp_hex, 16))
        # Genero 100 codepoint random sconosciuti
        scon = genera_random_sconosciute(used_cp, count=100)
        html_lines.append("  <p>Elenco di 100 code point Unicode random NON presenti nelle emoji ufficiali:</p>")
        html_lines.append("  <table>")
        html_lines.append("    <tr><th>Char</th><th>Code point (hex)</th><th>Descrizione</th></tr>")
        for char, hex_code in scon:
            html_lines.append(f"    <tr><td class='char'>{char}</td><td class='code'>U+{hex_code}</td><td>Random non-emoji</td></tr>")
        html_lines.append("  </table>")

    else:
        lista = categories.get(cat_key, [])
        if not lista:
            html_lines.append(f"  <p>Nessuna emoji per la categoria {cat_key}.</p>")
        else:
            lista_ordinata = sorted(lista, key=lambda x: x[3].lower())
            html_lines.append("  <table>")
            html_lines.append("    <tr><th>Emoji</th><th>Nome</th><th>Code point (hex)</th><th>Versione</th><th>Status</th></tr>")
            for emoji_char, codepoints_list, version_token, name, status in lista_ordinata:
                codici_hex = " ".join(f"U+{cp}" for cp in codepoints_list)
                html_lines.append(
                    f"    <tr>"
                    f"<td class='char'>{emoji_char}</td>"
                    f"<td class='name'>{name}</td>"
                    f"<td class='code'>{codici_hex}</td>"
                    f"<td>{version_token}</td>"
                    f"<td>{status}</td>"
                    f"</tr>"
                )
            html_lines.append("  </table>")

    html_lines.extend([
        "</body>",
        "</html>"
    ])

    with open(temp_filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

# ----------------------------
# Funzioni di interfaccia utente
# ----------------------------

def mostra_categorie_disponibili(categories):
    """
    Stampa gli anni per cui esistono emoji (len>0), la categoria 'hidden' se contiene,
    la categoria 'removed' se contiene, e sempre '9999'.
    """
    available = []
    for anno, lista in categories.items():
        if anno not in ("hidden", "removed") and len(lista) > 0:
            available.append(anno)
    if categories.get("hidden"):
        available.append("hidden")
    if categories.get("removed"):
        available.append("removed")
    available.append("9999")
    available.sort(key=lambda x: (x not in YEARS, int(x) if x.isdigit() else float("inf")))
    print("\nCategorie disponibili:")
    for cat in available:
        if cat == "9999":
            print("  9999       (random Unicode fuori dalle emoji ufficiali)")
        elif cat == "hidden":
            print(f"  hidden     ({len(categories['hidden'])} emoji presenti ma non fully-qualified)")
        elif cat == "removed":
            print(f"  removed    ({len(categories['removed'])} emoji con versione non mappata)")
        else:
            cnt = len(categories[cat])
            print(f"  {cat}       ({cnt} emoji)")
    return available

# ----------------------------
# Main
# ----------------------------

def main():
    print("\nScaricamento e analisi delle emoji in corso. Attendere, per favore...\n")
    categories = costruisci_categorie_per_anno()
    print("Elaborazione completata.")

    while True:
        available = mostra_categorie_disponibili(categories)
        try:
            cmd = input("\nInserisci un comando ('<categoria>' o 'exit'): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nArrivederci!")
            break

        if cmd.lower() in ("exit", "esci", "quit"):
            print("\nArrivederci!")
            break

        if cmd in available:
            scelta = cmd
            # Creo file HTML temporaneo
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", prefix=f"emoji_{scelta}_") as tmp:
                temp_path = tmp.name
            crea_html_per_categoria(scelta, categories, temp_path)
            webbrowser.open("file://" + os.path.abspath(temp_path))
            print(f"[*] Aperto nel browser: {temp_path}\n")
        else:
            print(f"Categoria '{cmd}' non valida. Scegli tra: {', '.join(available)}\n")

if __name__ == "__main__":
    main()
