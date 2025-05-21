from data_capture.coletar_dados_b3 import export_company_data_to_files
import psycopg
import os
import shutil

from data_capture.accounts_creat import insert_financial_accounts_from_parquets
from data_capture.financial_statements_creat import insert_financial_statements_from_parquets
from data_capture.history_creat import insert_price_history_from_parquets
from data_capture.descriptive_stats_creat import insert_descriptive_stats_from_parquets
from data_capture.macro_values_creat import inserir_macro_values  # Mantém, pois coleta direto das APIs

def run_create_table():
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

    ## Loop pelos tickers do banco
    for i, ticker in enumerate(tickers, start=1):
        try:
            print(f"\n🔄 Processando {ticker} ({i}/{total_tickers})...")
            export_company_data_to_files(ticker)
        except Exception as e:
            print(f"❌ Erro ao processar {ticker} ({i}/{total_tickers}): {e}")

    insert_financial_accounts_from_parquets()

    insert_financial_statements_from_parquets()

    insert_price_history_from_parquets()

    insert_descriptive_stats_from_parquets()

    inserir_macro_values()

    PARQUETS_DIR = os.path.join(os.path.dirname(__file__), "parquets")

    if os.path.exists(PARQUETS_DIR) and os.path.isdir(PARQUETS_DIR):
        shutil.rmtree(PARQUETS_DIR)
        print(f"🗑️ Pasta removida: {PARQUETS_DIR}")
    else:
        print(f"⚠️ Pasta não encontrada para remoção: {PARQUETS_DIR}")

    # PARQUETS_DIR = os.path.join(os.path.dirname(__file__), "excels")

    # if os.path.exists(PARQUETS_DIR) and os.path.isdir(PARQUETS_DIR):
    #     shutil.rmtree(PARQUETS_DIR)
    #     print(f"🗑️ Pasta removida: {PARQUETS_DIR}")
    # else:
    #     print(f"⚠️ Pasta não encontrada para remoção: {PARQUETS_DIR}")

if __name__ == "__main__":
    run_create_table()