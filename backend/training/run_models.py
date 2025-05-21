import os
import sys
import pandas as pd
from lstm_model import train as train_lstm
from gru_model import train as train_gru
from xgboost_model import train as train_xgb
from psycopg import connect
import time

start_time = time.time()

# Parâmetros da CLI
def get_cli_args():
    company_id = sys.argv[1] if len(sys.argv) > 1 else None
    sequence_length = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    predict_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    return company_id, sequence_length, predict_days

COMPANY_ID, SEQUENCE_LENGTH, PREDICT_DAYS = get_cli_args()

# Diretório de saída e log
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

OUTPUT_DIR = ensure_dir("../../data_prediction/predictions_temp")
LOG_FILE = os.path.join(OUTPUT_DIR, 'run_models.log')

def log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - {message}\n")

# Início do processamento
log("Iniciando run_models.py")
if COMPANY_ID:
    print(f"🔄 Rodando modelos apenas para a empresa {COMPANY_ID}")
    log(f"Parâmetro company_id definido: {COMPANY_ID}")
    companies = [COMPANY_ID]
else:
    print("🔄 Rodando modelos para todas as empresas")
    log("Nenhum company_id fornecido; processando todas as empresas")
    # Função para buscar todas as empresas
def get_all_companies():
    try:
        with connect(
            dbname="tcc_b3", user="postgres", password="postgres", host="localhost", port="5432"
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM companies;")
                return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Erro ao buscar empresas: {e}")
        log(f"Erro ao buscar empresas: {e}")
        return []

if not COMPANY_ID:
    companies = get_all_companies()

# Carrega lista de modelos ativos
modelos = []
try:
    with connect(
        dbname="tcc_b3", user="postgres", password="postgres", host="localhost", port="5432"
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, model FROM models;")
            for model_id, model_name in cursor.fetchall():
                if model_name == "lstm": modelos.append((train_lstm, model_name, model_id))
                elif model_name == "gru": modelos.append((train_gru, model_name, model_id))
                elif model_name == "xgboost": modelos.append((train_xgb, model_name, model_id))
except Exception as e:
    print(f"❌ Erro ao carregar modelos do banco: {e}")
    log(f"Erro ao carregar modelos do banco: {e}")
    sys.exit(1)

# Loop pelas empresas
for idx, company_id in enumerate(companies, start=1):
    print(f"\n🏢 [{idx}/{len(companies)}] Processando empresa: {company_id}")
    log(f"Iniciando processamento da empresa {company_id}")

    # Verifica e carrega dataset
    file_path = f"../../data_prediction/get_data/features/{company_id}_dataset.parquet"
    if not os.path.exists(file_path):
        msg = f"Dataset não encontrado para empresa {company_id}"
        print(f"❌ {msg}")
        log(msg)
        continue
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        msg = f"Erro ao carregar dataset da empresa {company_id}: {e}"
        print(f"❌ {msg}")
        log(msg)
        continue

    # Executa cada modelo
    for func, model_name, model_id in modelos:
        print(f"   ▶️ Iniciando {model_name.upper()} para empresa {company_id}...")
        log(f"Iniciando modelo {model_name} para {company_id}")
        start_time_2 = time.time()
        try:
            _, _, _, result_df = func(df, sequence_length=SEQUENCE_LENGTH, predict_days=PREDICT_DAYS)
            output_path = os.path.join(OUTPUT_DIR, f"{company_id}_{model_id}.parquet")
            result_df.to_parquet(output_path, index=False)
            elapsed = time.time() - start_time_2
            print(f"   ✅ {model_name.upper()} concluído em {elapsed:.2f}s")
            log(f"Modelo {model_name} finalizado em {elapsed:.2f}s para {company_id}")
        except Exception as e:
            msg = f"Erro ao rodar {model_name.upper()} para {company_id}: {e}"
            print(f"   ❌ {msg}")
            log(msg)

# Finalização
total_time = time.time() - start_time
print(f"\n🎉 Processamento concluído para todas as empresas em {total_time:.2f}s!")
log("Processamento completo para todas as empresas")
