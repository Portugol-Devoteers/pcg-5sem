import os
import sys
import pandas as pd

from lstm_model import train as train_lstm
from gru_model import train as train_gru
from xgboost_model import train as train_xgb

# Parâmetros
SEQUENCE_LENGTH = int(sys.argv[2]) if len(sys.argv) > 2 else 60
PREDICT_DAYS = int(sys.argv[3]) if len(sys.argv) > 3 else 7
COMPANY_ID = sys.argv[1] if len(sys.argv) > 1 else None

if COMPANY_ID is None:
    print("Uso: python run_models.py <company_id> [sequence_length] [predict_days]")
    sys.exit(1)

file_path = f"../../data_prediction/get_data/features/{COMPANY_ID}_dataset.parquet"
output_dir = f"../../data_prediction/predictions_temp"
os.makedirs(output_dir, exist_ok=True)

# Carrega o dataset
df = pd.read_parquet(file_path)

import psycopg

conn = psycopg.connect(
    dbname="tcc_b3",
    user="postgres",
    password="postgres",  # troque se necessário
    host="localhost",
    port="5432"
)

modelos = []
with conn.cursor() as cursor:
    cursor.execute("SELECT id, model FROM models;")
    rows = cursor.fetchall()
    for row in rows:
        model_id = row[0]
        model_name = row[1]
        if model_name == "lstm":
            modelos.append((train_lstm, model_name, model_id))
        elif model_name == "gru":
            modelos.append((train_gru, model_name, model_id))
        elif model_name == "xgboost":
            modelos.append((train_xgb, model_name, model_id))

for func, model_name, model_id in modelos:
    print(f"\n==> Rodando modelo {str(model_name).upper()}...")
    _, _, _, result_df = func(df, sequence_length=SEQUENCE_LENGTH, predict_days=PREDICT_DAYS)

    output_path = os.path.join(output_dir, f"{COMPANY_ID}_{model_id}.parquet")
    result_df.to_parquet(output_path, index=False)

    print(result_df)
