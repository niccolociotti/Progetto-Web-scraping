import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Lista delle parole chiave da cercare
keywords = ["blockchain","big data","realtà aumentata","intelligenza artificiale",]
prova_file = "prova.xlsx"
colonna_siti = "Website"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'}

# === LEGGI FILE EXCEL ===
df = pd.read_excel(prova_file)
if colonna_siti not in df.columns:
    raise ValueError(f"La colonna '{colonna_siti}' non esiste nel file Excel.")
df = df[[colonna_siti]].dropna()
df[colonna_siti] = df[colonna_siti].astype(str)

# === FUNZIONI ===
def normalizza_url(url):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def estrai_link(soup, base_url):
    links = set()
    lingua_valide = {"it-it", "us-en"}
    estensioni_valide = ('.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.jspx', '.js', '')  # Vuoto = path senza estensione

    estensioni_escluse = (
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.mp3', '.wav', '.mp4', '.avi', '.mov', '.zip', '.rar'
    )

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Solo link interni
        if parsed.netloc != urlparse(base_url).netloc:
            continue

        # Escludi risorse con estensioni non HTML
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in estensioni_escluse):
            continue

        if not path.endswith(estensioni_valide) and '.' in path.split('/')[-1]:
            # Se ha un'estensione non valida (es: .zip, .mp4, .exe, ecc.)
            continue

        path_parts = parsed.path.strip("/").split("/")

        # Se include una lingua valida
        if len(path_parts) >= 1 and path_parts[0].lower() in lingua_valide:
            if len(path_parts) <= 2:
                links.add(full_url)
        elif len(path_parts) <= 1:
            links.add(full_url)

    return links

def contiene(text):
    text_lower = text.lower()
    trovate = [keyword for keyword in keywords if keyword.lower() in text_lower]
    return trovate  # lista di parole trovate (vuota se nessuna)

def cerca(sito):
    try:
        url = normalizza_url(sito)
        print(f"➡️ [MAIN] Richiesta a: {url}")
        response = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        trovate_home = contiene(text)
        trovate_totali = set(trovate_home)

        risultati_trovati = []
        if trovate_home:
            print(f"✅ [FOUND] Parole chiave trovate nella homepage di {url}: {trovate_home}")
            risultati_trovati.append(f"Homepage: {', '.join(trovate_home)}")

        # Cerca anche nei link interni
        links = estrai_link(soup, url)
        for link in links:
            try:
                print(f"➡️ [LINK] Richiesta a: {link}")
                r = requests.get(link, headers=headers, timeout=3)
                r_text = BeautifulSoup(r.text, "html.parser").get_text(separator=" ", strip=True)
                trovate_link = contiene(r_text)
                if trovate_link:
                    print(f"✅ [FOUND] Parole chiave trovate in {link}: {trovate_link}")
                    risultati_trovati.append(f"Link: {link} - {', '.join(trovate_link)}")
            except Exception as e:
                print(f"⚠️ [LINK-ERRORE] {link}: {e}")
                continue

        # Costruisci risultato con True/False per ogni keyword
        risultato_dict = {"Link": sito}
        for keyword in keywords:
            risultato_dict[keyword] = keyword in trovate_totali

        return risultato_dict

    except Exception as e:
        print(f"⚠️ [ERRORE] {sito}: {e}")
        risultato_dict = {"Link": sito}
        for keyword in keywords:
            risultato_dict[keyword] = f"Errore: {e}"
        return risultato_dict


# === MULTITHREADING ===
risultati = []
with ThreadPoolExecutor(max_workers=50) as executor:
    start = time.time()
    future_to_sito = {executor.submit(cerca, sito): sito for sito in df[colonna_siti]}

    for future in as_completed(future_to_sito):
        risultato = future.result()
        risultati.append(risultato)


# === FILTRA errori ===
dati_puliti = [r for r in risultati if all(not isinstance(v, str) or not v.startswith("Errore") for k, v in r.items() if k != "Link")]

# === SALVA CSV ===
pd.DataFrame(dati_puliti).to_csv("risultati_parole_chiave.csv", index=False)

finish = time.time()
print(f"⏰ [FINITO] Tempo totale: {finish - start:.2f} secondi")