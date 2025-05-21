import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Lista delle parole chiave da cercare
keywords = ["blockchain", "intelligenza artificiale", "artificial intelligence", "machine learning"]
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

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Solo link interni
        if parsed.netloc != urlparse(base_url).netloc:
            continue

        path_parts = parsed.path.strip("/").split("/")

        # Se include una lingua valida
        if len(path_parts) >= 1 and path_parts[0].lower() in lingua_valide:
            # Permetti massimo: /it-it        o  /it-it/qualcosa
            if len(path_parts) <= 2:
                links.add(full_url)

        # Se non ci sono lingue nel sito, accetta solo link diretti (non profondi)
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
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        trovate_home = contiene(text)

        risultati_trovati = []
        if trovate_home:
            print(f"✅ [FOUND] Parole chiave trovate nella homepage di {url}: {trovate_home}")
            risultati_trovati.append(f"Homepage: {', '.join(trovate_home)}")

        # Cerca anche nei link interni
        links = estrai_link(soup, url)
        for link in links:
            try:
                print(f"➡️ [LINK] Richiesta a: {link}")
                r = requests.get(link, headers=headers, timeout=5)
                r_text = BeautifulSoup(r.text, "html.parser").get_text(separator=" ", strip=True)
                trovate_link = contiene(r_text)
                if trovate_link:
                    print(f"✅ [FOUND] Parole chiave trovate in {link}: {trovate_link}")
                    risultati_trovati.append(f"Link: {link} - {', '.join(trovate_link)}")
            except Exception as e:
                print(f"⚠️ [LINK-ERRORE] {link}: {e}")
                continue

        if risultati_trovati:
            return sito, " | ".join(risultati_trovati)

        print(f"❌ [NOT FOUND] Nessuna delle parole chiave trovata in {url} o nei suoi link")
        return sito, "Nessuna parola chiave trovata"

    except Exception as e:
        print(f"⚠️ [ERRORE] {sito}: {e}")
        return sito, f"Errore: {e}"


# === MULTITHREADING ===
risultati = []
with ThreadPoolExecutor(max_workers=50) as executor:
    future_to_sito = {executor.submit(cerca, sito): sito for sito in df[colonna_siti]}

    for future in as_completed(future_to_sito):
        sito, risultato = future.result()
        risultati.append({"Sito": sito, "Risultato": risultato})

# === OPZIONALE: Salva anche su CSV ===
# pd.DataFrame(risultati).to_csv("risultati_parole_chiave_dettagli.csv", index=False)
