import os
import sys
import pandas as pd
from lstm_model import train as train_lstm
from gru_model import train as train_gru
from xgboost_model import train as train_xgb
from psycopg import connect
import time

COMPANY_ID = sys.argv[1] if len(sys.argv) > 1 else None
SEQUENCE_LENGTH = int(sys.argv[2]) if len(sys.argv) > 2 else 60
PREDICT_DAYS = int(sys.argv[3]) if len(sys.argv) > 3 else 7

if COMPANY_ID is None:
    print("Uso: python run_models.py <company_id> [sequence_length] [predict_days]")
    sys.exit(1)

# Caminhos
file_path = f"../../data_prediction/get_data/features/{COMPANY_ID}_dataset.parquet"
output_dir = f"../../data_prediction/predictions_temp"
os.makedirs(output_dir, exist_ok=True)

# Carregar o dataset
try:
    df = pd.read_parquet(file_path)
except Exception as e:
    print(f"❌ Erro ao carregar o arquivo {file_path}: {e}")
    sys.exit(1)

# Ler modelos do banco
modelos = []
try:
    with connect(
        dbname="tcc_b3",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, model FROM models;")
            rows = cursor.fetchall()

            for model_id, model_name in rows:
                if model_name == "lstm":
                    modelos.append((train_lstm, model_name, model_id))
                elif model_name == "gru":
                    modelos.append((train_gru, model_name, model_id))
                elif model_name == "xgboost":
                    modelos.append((train_xgb, model_name, model_id))
except Exception as e:
    print(f"❌ Erro ao conectar ou consultar o banco: {e}")
    sys.exit(1)

# Rodar modelos
for func, model_name, model_id in modelos:
    print(f"\n==> Rodando modelo {model_name.upper()}...")
    start_time = time.time()
    try:
        _, _, _, result_df = func(df, sequence_length=SEQUENCE_LENGTH, predict_days=PREDICT_DAYS)
        output_path = os.path.join(output_dir, f"{COMPANY_ID}_{model_id}.parquet")
        result_df.to_parquet(output_path, index=False)
        print(result_df)
    except Exception as e:
        print(f"❌ Erro ao rodar modelo {model_name.upper()}: {e}")
    print(f"✅ Modelo {model_name.upper()} rodado em {time.time() - start_time:.2f} segundos.")