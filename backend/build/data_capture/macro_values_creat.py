import psycopg
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

def inserir_macro_values():
    conn = psycopg.connect(
        dbname="tcc_b3",
        user="writer",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    # Buscar todos os indicadores macro
    cur.execute("SELECT id, name, ticker FROM macro_indicators")
    indicadores = cur.fetchall()

    for macro_id, nome, ticker in indicadores:
        print(f"📥 Buscando: {nome}")

        df = None

        if ticker and ticker.startswith("SGS:"):
            # API SGS do BACEN
            codigo = ticker.split(":")[1]
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
            response = requests.get(url)
            data = response.json()
            df = pd.DataFrame(data)
            df["data"] = pd.to_datetime(df["data"], dayfirst=True)
            df["valor"] = df["valor"].str.replace(",", ".").astype(float)
            df.rename(columns={"data": "date", "valor": "value"}, inplace=True)

        elif ticker:
            # Yahoo Finance
            yf_data = yf.Ticker(ticker).history(period="max", interval="1d")
            if yf_data.empty:
                print(f"⚠️ Nenhum dado encontrado para {nome}")
                continue
            df = yf_data.reset_index()[["Date", "Close"]].rename(columns={"Date": "date", "Close": "value"})
            df = df[df["value"].notnull()]

        if df is None or df.empty:
            print(f"❌ Falha ao obter dados de {nome}")
            continue

        inseridos = 0
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO macro_values (date, macro_indicator_id, value, updated_by_user_id, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (row["date"].date(), macro_id, row["value"], 1))
                inseridos += 1
            except psycopg.errors.UniqueViolation:
                conn.rollback()  # limpa o erro da transação atual
            except Exception as e:
                conn.rollback()
                print(f"⚠️ Erro inesperado em {nome} - {row['date']}: {e}")

        print(f"✅ Inseridos {inseridos} valores para {nome}")

    conn.commit()
    cur.close()
    conn.close()
    print("🏁 Processo concluído.")

