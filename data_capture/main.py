from coletar_dados_b3 import export_company_data_to_files
import psycopg
import os
from accounts_creat import insert_financial_accounts_from_csvs
from financial_statements_creat import insert_financial_statements_from_csvs
from history_creat import insert_price_history_from_csvs
from descriptive_stats_creat import insert_descriptive_stats_from_csvs
from macro_values_creat import inserir_macro_values

# Conexão com o banco
conn = psycopg.connect(
    dbname="tcc_b3",
    user="writer",
    password="postgres",  # troque se necessário
    host="localhost",
    port="5432"
)

with conn.cursor() as cur:
    cur.execute("SELECT b3_code FROM companies")
    tickers = [row[0] for row in cur.fetchall()]

# Total de tickers
total_tickers = len(tickers)

# Loop pelos tickers do banco
for i, ticker in enumerate(tickers, start=1):
    try:
        print(f"\n🔄 Processando {ticker} ({i}/{total_tickers})...")
        files = export_company_data_to_files(ticker)
        print("✅ Arquivos salvos:")
        print(files["excel"])
    except Exception as e:
        print(f"❌ Erro ao processar {ticker} ({i}/{total_tickers}): {e}")

insert_financial_accounts_from_csvs()

insert_financial_statements_from_csvs()

insert_price_history_from_csvs()

insert_descriptive_stats_from_csvs()

inserir_macro_values()