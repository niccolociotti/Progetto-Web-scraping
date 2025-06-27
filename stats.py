import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Carica il dataset Excel direttamente in un DataFrame
filepath = '/Users/niccolociotti/Desktop/Progetto-Web-scraping/risultati_uniti.xlsx'
if not os.path.isfile(filepath):
    raise FileNotFoundError(f"File '{filepath}' non trovato.")
df = pd.read_excel(filepath)

# 2. Individua le colonne boolean (True/False) come tecnologie
tech_cols = [
    col for col in df.columns
    if df[col].dropna().isin([True, False]).all()
]
if "AI" not in tech_cols:
    raise ValueError("Colonna 'AI' non trovata tra le tecnologie.")

# 3. Filtra aziende con AI = True
aziende_ai = df[df["AI"] == True]
total_ai = len(aziende_ai)

# 4. Conteggia quante tecnologie diverse sono True per ciascuna azienda
tech_counts_per_row = aziende_ai[tech_cols].sum(axis=1)

# 5. Suddividi in "solo AI" vs "AI + almeno un'altra tecnologia"
aziende_ai_solo = aziende_ai[tech_counts_per_row == 1]
aziende_ai_multi = aziende_ai[tech_counts_per_row > 1]

count_ai_solo = len(aziende_ai_solo)
count_ai_multi = len(aziende_ai_multi)

# 6. Stampa riepilogo
print("===== Risultati analisi AI =====")
print(f"Totale aziende con AI=True:        {total_ai}")
print(f"Aziende con solo AI:               {count_ai_solo}")
print(f"Aziende con AI + altra tecnologia: {count_ai_multi}")
print(f"Percentuale solo AI:               {count_ai_solo/total_ai*100:.1f}%")
print(f"Percentuale AI+altre:              {count_ai_multi/total_ai*100:.1f}%")

# 7. Prepara output directory per i grafici
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# 8. Grafico a barre
labels = ["Solo AI", "AI + altra"]
values = [count_ai_solo, count_ai_multi]
plt.figure(figsize=(8,5))
plt.bar(labels, values, color=["#4C72B0", "#55A868"])
plt.title("Aziende con solo AI vs AI + altre tecnologie")
plt.ylabel("Numero di aziende")
for i, v in enumerate(values):
    plt.text(i, v + total_ai*0.01, str(v), ha="center")
plt.tight_layout()
bar_path = os.path.join(output_dir, "ai_solo_vs_multi_bar.png")
plt.savefig(bar_path)
plt.close()
print(f"Grafico a barre salvato in: {bar_path}")

# 9. Grafico a torta
plt.figure(figsize=(6,6))
plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
plt.title("Percentuale aziende Solo AI vs AI + altre")
pie_path = os.path.join(output_dir, "ai_solo_vs_multi_pie.png")
plt.savefig(pie_path)
plt.close()
print(f"Grafico a torta salvato in: {pie_path}")