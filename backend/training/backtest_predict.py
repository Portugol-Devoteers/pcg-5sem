import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import sys
import time
import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from psycopg import connect
from psycopg.rows import dict_row
import yfinance as yf
import warnings
import tensorflow as tf  # type: ignore

# Imports dos modelos
from lstm_model import train as train_lstm
from gru_model import train as train_gru
from xgboost_model import train as train_xgb

# Fixar aleatoriedade
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

warnings.filterwarnings("ignore", category=UserWarning, module="yfinance")

def get_connection():
    return connect(
        dbname="tcc_b3",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

def get_company_ticker(company_id: int) -> str:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT b3_code FROM companies WHERE id = %s", (company_id,))
            row = cur.fetchone()
            if row and row["b3_code"]:
                return row["b3_code"]
            raise ValueError(f"Empresa com ID {company_id} não encontrada ou sem b3_code.")

def buscar_valor_real(ticker: str, a_partir_de: str, max_dias=5):
    data = datetime.strptime(a_partir_de, "%Y-%m-%d")
    for _ in range(max_dias):
        data_str = data.strftime("%Y-%m-%d")
        next_day = (data + timedelta(days=1)).strftime("%Y-%m-%d")

        df_real = yf.download(
            ticker,
            start=data_str,
            end=next_day,
            auto_adjust=False,
            progress=False
        )

        if not df_real.empty:
            valor = df_real["Close"].iloc[0]
            if isinstance(valor, pd.Series):
                valor = valor.values[0]
            return float(valor), data_str

        data += timedelta(days=1)

    raise ValueError(f"Nenhum dado encontrado para {ticker} nos {max_dias} dias após {a_partir_de}")

def backtest_predict(company_id: int, data_simulada: str, modelo: str):
    data_ref = datetime.strptime(data_simulada, "%Y-%m-%d")
    data_inicio = data_ref - timedelta(days=90)
    data_fim = data_ref

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    ph.date,
                    ph.close,
                    ph.volume,
                    mi.selic,
                    mi.ipca,
                    mi.usd_brl,
                    mi.ibov
                FROM price_history ph
                JOIN macro_indicators mi ON ph.date = mi.date
                WHERE ph.company_id = %s AND ph.date BETWEEN %s AND %s
                ORDER BY ph.date
            """, (company_id, data_inicio, data_fim))
            rows = cur.fetchall()

    df = pd.DataFrame(rows)

    if df.empty:
        return {"error": "Nenhum dado retornado do banco para essa empresa."}

    df = df.sort_values("date").reset_index(drop=True)

    if len(df) < 61:
        return {"error": "Não há dados suficientes para o backtest."}

    feature_cols = ['close', 'volume', 'selic', 'ipca', 'usd_brl', 'ibov']
    df_train = df.iloc[-61:].copy()
    df_train[feature_cols] = df_train[feature_cols].astype(float)

    if modelo == "lstm":
        model, scaler_X, scaler_y = train_lstm(df_train)
    elif modelo == "gru":
        model, scaler_X, scaler_y = train_gru(df_train)
    elif modelo == "xgboost":
        model, scaler_X, scaler_y = train_xgb(df_train)
    else:
        raise ValueError("Modelo não suportado. Use 'lstm', 'gru' ou 'xgboost'.")

    last_60 = df_train[feature_cols].values[-60:]
    X_input = scaler_X.transform(last_60).reshape(1, 60, len(feature_cols))

    if modelo == "xgboost":
        pred_scaled = model.predict(X_input.reshape(1, -1))
        pred_real = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))
    else:
        pred_scaled = model.predict(X_input, verbose=0)
        pred_real = scaler_y.inverse_transform(pred_scaled)

    empresa = get_company_ticker(company_id)
    data_real = (data_ref + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        real_price, data_encontrada = buscar_valor_real(empresa, data_real)
    except Exception as e:
        return {"error": str(e)}

    erro_abs = abs(real_price - pred_real[0][0])
    erro_pct = (erro_abs / real_price) * 100

    return {
        "modelo": modelo,
        "company_id": company_id,
        "simulated_date": data_simulada,
        "predicted_for": data_encontrada,
        "predicted_close": round(float(pred_real[0][0]), 2),
        "real_close": round(real_price, 2),
        "absolute_error": round(erro_abs, 2),
        "percent_error": round(erro_pct, 2)
    }

if __name__ == "__main__":
    print("+======================================================+")
    print("|        Backtest de Previsão - Comparativo           |")
    print("+======================================================+")

    if len(sys.argv) < 2:
        print("Uso: python backtest_predict.py <company_id> [modelo]")
        print("Exemplo: python backtest_predict.py 1 lstm")
        sys.exit(1)

    company_id = int(sys.argv[1])
    data_simulada = "2024-10-01"
    modelos = ["lstm", "gru", "xgboost"] if len(sys.argv) < 3 else [sys.argv[2]]

    for modelo in modelos:
        print(f"\n>> Rodando modelo: {modelo.upper()}\n")
        start_time = time.time()
        resultado = backtest_predict(company_id, data_simulada, modelo)

        if "error" in resultado:
            print("\n❌ Erro:", resultado["error"])
        else:
            print(f"""
Resultado do Backtest usando {modelo.upper()}:
- Empresa ID          : {resultado['company_id']}
- Data simulada       : {resultado['simulated_date']}
- Data prevista       : {resultado['predicted_for']}
- Preço previsto      : R$ {resultado['predicted_close']:.2f}
- Preço real          : R$ {resultado['real_close']:.2f}
- Erro absoluto       : R$ {resultado['absolute_error']:.2f}
- Erro percentual     : {resultado['percent_error']:.2f}%
Tempo de execução    : {time.time() - start_time:.2f} segundos
""")

    print("+======================================================+")
