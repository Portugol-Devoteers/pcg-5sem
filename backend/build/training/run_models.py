import os
from pathlib import Path
import sys
import pandas as pd
from training.lstm_model import train as train_lstm
from training.gru_model import train as train_gru
from training.xgboost_model import train as train_xgb
from psycopg import connect
import time
import shutil
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

def run_models():
    start_time = time.time()

    # Parâmetros da CLI
    def get_cli_args():
        company_id = sys.argv[1] if len(sys.argv) > 1 else None
        sequence_length = int(sys.argv[2]) if len(sys.argv) > 2 else 800
        predict_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        return company_id, sequence_length, predict_days

    COMPANY_ID, SEQUENCE_LENGTH, PREDICT_DAYS = get_cli_args()

    # Diretório de saída e log
    def ensure_dir(path):
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    BASE_PATH  = Path(__file__).resolve().parent.parent
    INPUT_PATH = BASE_PATH / "data_prediction" / "get_data" / "features"

    
    OUTPUT_DIR = ensure_dir(BASE_PATH / "data_prediction" / "predictions_temp")
    print(f"🔄 Criando pasta de saída: {OUTPUT_DIR}")
    LOG_FILE   = OUTPUT_DIR / "run_models.log"

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
        file_path = f"{INPUT_PATH}/{company_id}_dataset.parquet"
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
                model_name = model_name.lower()
                if model_name == "xgboost":
                    # chamada
                    ret = func(df, sequence_length=SEQUENCE_LENGTH, predict_days=PREDICT_DAYS)
                    (model, _, _, result_df, train_log, feat_importance_df,
                    metrics, recent_train_df, corr_df, mi_df) = ret  # agora 10 retornos

                    # salva previsões (já fazia)
                    output_path = os.path.join(OUTPUT_DIR, f"{company_id}_{model_id}.parquet")
                    result_df.to_parquet(output_path, index=False)

                    # diretório de plots por empresa
                    plots_dir = ensure_dir(OUTPUT_DIR / "plots" / str(company_id))
                    base = f"{company_id}_xgb"

                    # (a) Curva de treinamento — RMSE vs #árvores
                    if len(train_log) > 0:
                        plt.figure()
                        plt.plot(range(1, len(train_log) + 1), train_log)
                        plt.xlabel("Número de árvores")
                        plt.ylabel("RMSE (treino)")
                        plt.title(f"Curva de treinamento (XGBoost) — {company_id}")
                        plt.tight_layout()
                        plt.savefig(plots_dir / f"{base}_train_rmse.png", dpi=150)
                        plt.close()

                    # (b) Importância de features — Top-10 (gain)
                    if (hasattr(feat_importance_df, "empty") and not feat_importance_df.empty):
                        top = feat_importance_df.head(10).iloc[::-1]
                        plt.figure()
                        plt.barh(top['feature'], top['gain'])
                        plt.xlabel("Gain")
                        plt.title(f"Top-10 Importância de Features — {company_id}")
                        plt.tight_layout()
                        plt.savefig(plots_dir / f"{base}_feat_importance.png", dpi=150)
                        plt.close()

                    # (c) Série com previsão futura
                    try:
                        last_close = float(df['close'].iloc[-1])
                        last_date_real = df['date'].iloc[-1]
                    except Exception:
                        last_close, last_date_real = None, None
                    plt.figure()
                    if last_close is not None:
                        plt.plot([last_date_real], [last_close], marker='o', label='Último close conhecido')
                    plt.plot(result_df['date'], result_df['value'], marker='o', label='Previsão')
                    plt.xlabel("Data")
                    plt.ylabel("Preço")
                    plt.title(f"Previsão {PREDICT_DAYS} dia(s) — {company_id} (XGBoost)")
                    plt.legend()
                    plt.tight_layout()
                    plt.savefig(plots_dir / f"{base}_forecast.png", dpi=150)
                    plt.close()

                    # (d) Real vs. Previsto (últimos N do treino)
                    if not recent_train_df.empty:
                        plt.figure()
                        plt.plot(recent_train_df['date'], recent_train_df['real'], label='Real')
                        plt.plot(recent_train_df['date'], recent_train_df['previsto'], label='Previsto')
                        plt.xlabel("Data")
                        plt.ylabel("Preço")
                        plt.title(f"Real vs Previsto (treino, últimos {len(recent_train_df)} pts) — {company_id}")
                        plt.legend()
                        plt.tight_layout()
                        plt.savefig(plots_dir / f"{base}_train_fit.png", dpi=150)
                        plt.close()

                    # (e) Histograma de resíduos (treino)
                    if not recent_train_df.empty:
                        resid = recent_train_df['real'].values - recent_train_df['previsto'].values
                        plt.figure()
                        plt.hist(resid, bins=30)
                        plt.xlabel("Erro (Real - Previsto)")
                        plt.ylabel("Frequência")
                        plt.title(f"Distribuição dos resíduos (treino) — {company_id}")
                        plt.tight_layout()
                        plt.savefig(plots_dir / f"{base}_residuals_hist.png", dpi=150)
                        plt.close()

                    # (f) Matriz de correlação (Pearson)
                    if hasattr(corr_df, "values") and corr_df.shape[0] > 1:
                        plt.figure(figsize=(8, 6))
                        im = plt.imshow(corr_df.values, aspect='auto')
                        plt.colorbar(im, fraction=0.046, pad=0.04)
                        plt.xticks(range(len(corr_df.columns)), corr_df.columns, rotation=90)
                        plt.yticks(range(len(corr_df.index)), corr_df.index)
                        plt.title(f"Matriz de correlação — {company_id}")
                        plt.tight_layout()
                        plt.savefig(plots_dir / f"{base}_corr_matrix.png", dpi=200)
                        plt.close()
                        # salva CSV para consulta textual
                        corr_df.to_csv(plots_dir / f"{base}_corr_matrix.csv", index=True)

                    # (g) Mutual Information (Top-20)
                    if hasattr(mi_df, "empty") and not mi_df.empty:
                        topk = mi_df.head(20).iloc[::-1]
                        plt.figure(figsize=(8, 6))
                        plt.barh(topk['feature'], topk['mi'])
                        plt.xlabel("Mutual Information")
                        plt.title(f"Informação Mútua (Top-20) — {company_id}")
                        plt.tight_layout()
                        plt.savefig(plots_dir / f"{base}_mi_top20.png", dpi=200)
                        plt.close()
                        mi_df.to_csv(plots_dir / f"{base}_mi_full.csv", index=False)

                    # (h) Salvar métricas em CSV
                    import csv
                    metrics_path = plots_dir / f"{base}_metrics.csv"
                    with open(metrics_path, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["metric", "value"])
                        for k, v in metrics.items():
                            writer.writerow([k, v])


                elapsed = time.time() - start_time_2
                print(f"   ✅ {model_name.upper()} concluído em {elapsed:.2f}s")
                log(f"Modelo {model_name} finalizado em {elapsed:.2f}s para {company_id}")

            except Exception as e:
                msg = f"Erro ao rodar {model_name.upper()} para {company_id}: {e}"
                print(f"   ❌ {msg}")
                log(msg)

    # Finalização

    if INPUT_PATH.exists() and INPUT_PATH.is_dir():
        shutil.rmtree(INPUT_PATH)
        print(f"🗑️ Pasta removida: {INPUT_PATH}")
    else:
        print(f"⚠️ Pasta não encontrada para remoção: {INPUT_PATH}")    

    total_time = time.time() - start_time
    print(f"\n🎉 Processamento concluído para todas as empresas em {total_time:.2f}s!")
    log("Processamento completo para todas as empresas")


if __name__ == "__main__":
    run_models()