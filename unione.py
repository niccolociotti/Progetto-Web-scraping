import pandas as pd

# Leggi il file Excel
df_excel = pd.read_excel('Aida_Export.xlsx')

# Leggi il file CSV
df_csv = pd.read_csv('RISULTATI2.csv')

# Rinomina la colonna del CSV per farla combaciare
df_csv.rename(columns={'Link': 'Website'}, inplace=True)

df_csv = df_csv.drop_duplicates(subset=['Website'])
df_unito = pd.merge(df_excel, df_csv, on='Website', how='left')

# Salva il risultato in un nuovo file Excel
df_unito.to_excel('risultati_uniti.xlsx', index=False)
