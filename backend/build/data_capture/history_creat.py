import os
from pathlib import Path
import pandas as pd
import psycopg

def log_erro(msg):
    with open('erros_importacao.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def insert_price_history_from_parquets():
    USER_ID = 1
    BASE_PATH = Path(__file__).resolve().parent.parent
    pasta = BASE_PATH.joinpath("data_capture", "parquets", "historical")

    conn = psycopg.connect(
        dbname="tcc_b3",
        user="writer",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    if not os.path.isdir(pasta):
        msg = f"📁 Pasta não encontrada: {pasta}"
        print(msg)
        log_erro(msg)
        return

    for arquivo in os.listdir(pasta):
        if not arquivo.endswith(".parquet"):
            continue

        path_parquet = os.path.join(pasta, arquivo)
        df = pd.read_parquet(path_parquet)

        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index().rename(columns={'index': 'date'})

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        nome_arquivo = arquivo.replace("_historical.parquet", "")
        b3_code = nome_arquivo.replace("_", ".")

        try:
            cur.execute("SELECT id FROM companies WHERE b3_code = %s", (b3_code,))
            result = cur.fetchone()
            if not result:
                msg = f"⚠️ Empresa não encontrada para o código: {b3_code}"
                print(msg)
                log_erro(msg)
                continue
            company_id = result[0]
        except Exception as e:
            msg = f"❌ Erro ao buscar empresa {b3_code}: {e}"
            print(msg)
            log_erro(msg)
            conn.rollback()
            continue

        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO price_history (
                        company_id, date, open, high, low, close,
                        volume, dividends, stock_splits, updated_by_user_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    company_id,
                    pd.to_datetime(row["date"]).date(),
                    row.get("open", 0),
                    row.get("high", 0),
                    row.get("low", 0),
                    row.get("close", 0),
                    int(row.get("volume", 0)) if not pd.isna(row.get("volume")) else 0,
                    row.get("dividends", 0),
                    row.get("stock_splits", 0),
                    USER_ID
                ))

            except Exception as e:
                erro_msg = str(e)
                if 'unique_price_entry' in erro_msg:
                    msg = f"ℹ️ Aviso: Linha já existente para {b3_code}, ignorando."
                    print(msg)
                    conn.rollback()
                    # Não grava no log
                else:
                    msg = f"❌ Erro ao inserir linha de {b3_code}: {e}"
                    print(msg)
                    log_erro(msg)
                    conn.rollback()
                continue


        msg = f"✅ Histórico importado: {b3_code}"
        print(msg)

    conn.commit()
    cur.close()
    conn.close()

    msg = "\n📊 Todos os históricos foram inseridos com sucesso."
    print(msg)

if __name__ == "__main__":
    insert_price_history_from_parquets()
