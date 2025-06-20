import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

# Lista delle parole chiave da cercare
keywords = ["AI","IA","machine learning","deep learning","intelligenza artificiale","computer vision","artificial intelligence","LLM","reti neurali","neural networks"]
#["borsa","bag","store","negozio"]


prova_file = "Aida_Export_1_half.xlsx"
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
            if len(path_parts) <= 3:
                links.add(full_url)
        elif len(path_parts) <= 2:
            links.add(full_url)

    return links

def contiene(text):

    trovate = []
    for keyword in keywords:
        if keyword == "AI":
            # Cerca solo 'AI' esattamente maiuscolo
            match = re.search(r'\bAI\b', text)
        else:
            # Per tutte le altre: parola intera, case insensitive
            pattern = r'\b' + re.escape(keyword) + r'\b'
            match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
                trovate.append(keyword)
                if keyword == "AI":
                    start, end = match.start(), match.end()
                    contesto = text[max(0, start-30):min(len(text), end+30)]
                    print(f"🔍 [AI TROVATO] Contesto: ...{contesto}...")

    return trovate


def cerca(sito):
    try:
        url = normalizza_url(sito)
        print(f"➡️ [MAIN] Richiesta a: {url}")
        response = requests.get(url, headers=headers, timeout=5)
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
                r = requests.get(link, headers=headers, timeout=5)
                r_text = BeautifulSoup(r.text, "html.parser").get_text(separator=" ", strip=True)
                trovate_link = contiene(r_text)
                if trovate_link:
                    print(f"✅ [FOUND] Parole chiave trovate in {link}: {trovate_link}")
                    risultati_trovati.append(f"Link: {link} - {', '.join(trovate_link)}")
                    trovate_totali.update(trovate_link)
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
            risultato_dict[keyword] = False  # tutte False in caso di errore
        return risultato_dict


"""""
def test_homepage_only(url):
    try:
        url = normalizza_url(url)
        print(f"➡️ [TEST-HOMEPAGE] Richiesta a: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        trovate = []
        for keyword in keywords:
            if keyword == "AI":
                # Cerca solo 'AI' esattamente maiuscolo
                match = re.search(r'\bAI\b', text)
            else:
                # Per tutte le altre: parola intera, case insensitive
                pattern = r'\b' + re.escape(keyword) + r'\b'
                match = re.search(pattern, text, flags=re.IGNORECASE)
    
            if match:
                trovate.append(keyword)
                if keyword == "AI":
                    start, end = match.start(), match.end()
                    contesto = text[max(0, start-30):min(len(text), end+30)]
                    print(f"🔍 [AI TROVATO] Contesto: ...{contesto}...")


        print(f"✅ [RESULT] Parole chiave trovate nella homepage di {url}: {trovate}")

        risultato_dict = {"Link": url}
        for keyword in keywords:
            risultato_dict[keyword] = keyword in trovate

        return risultato_dict

    except Exception as e:
        print(f"⚠️ [TEST-ERRORE] {url}: {e}")
        risultato_dict = {"Link": url}
        for keyword in keywords:
            risultato_dict[keyword] = False
        return risultato_dict


risultato = test_homepage_only("https://ai.google")
print(risultato)
"""""

# === MULTITHREADING ===
risultati = []
with ThreadPoolExecutor(max_workers=50) as executor:
    start = time.time()
    future_to_sito = {executor.submit(cerca, sito): sito for sito in df[colonna_siti]}

    for idx, future in enumerate(as_completed(future_to_sito), start=1):
     risultato = future.result()
     sito_corrente = future_to_sito[future]
     print(f"\n📊 {idx}. {sito_corrente}")
     risultati.append(risultato)



# === SALVA CSV ===
pd.DataFrame(risultati).to_csv("risultati_timeout3.csv", index=False)

finish = time.time()
print(f"⏰ [FINITO] Tempo totale: {finish - start:.2f} secondi")