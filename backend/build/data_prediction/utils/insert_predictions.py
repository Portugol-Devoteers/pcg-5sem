import os
from pathlib import Path
import pandas as pd
from psycopg import connect
import shutil

def run_insert_predictions():
    # Caminho da pasta com os arquivos de previsão

    BASE_PATH = Path(__file__).resolve().parent.parent
    PREDICTIONS_FOLDER = BASE_PATH / "predictions_temp"

    HISTORY_COLUMNS_ID = 6 # ID da coluna "close"

    # Conexão com o banco
    def get_connection():
        return connect(
            dbname="tcc_b3",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )

    # Processa cada arquivo na pasta
    def insert_all_predictions():
        arquivos = [f for f in os.listdir(PREDICTIONS_FOLDER) if f.endswith(".parquet")]
        print(f"\nEncontrados {len(arquivos)} arquivos para inserção.")

        for nome_arquivo in arquivos:
            caminho = os.path.join(PREDICTIONS_FOLDER, nome_arquivo)
            print(f"\nInserindo: {nome_arquivo}")

            try:
                b3_code_id, model_id = nome_arquivo.replace(".parquet", "").split("_")
                df = pd.read_parquet(caminho)

                with get_connection() as conn:
                    with conn.cursor() as cur:
                        for _, row in df.iterrows():
                            try:
                                cur.execute("""
                                    INSERT INTO predictions (date, model_id, value, b3_code_id, history_columns_id, updated_by_user_id)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (
                                    pd.to_datetime(row['date']),
                                    int(model_id),
                                    float(row['value']),
                                    int(b3_code_id),
                                    HISTORY_COLUMNS_ID,
                                    2
                                ))
                            except Exception as e:
                                conn.rollback()  # volta apenas essa operação
                                print(f"⚠️ Erro ao inserir linha: {row['date']} | Motivo: {e}")
                                continue  # tenta a próxima linha

                        conn.commit()  # salva todas as válidas

                os.remove(caminho)
                print(f"✅ Inserido com sucesso e deletado: {nome_arquivo}")

            except Exception as e:
                print(f"❌ Erro ao inserir {nome_arquivo}: {e}")

        if PREDICTIONS_FOLDER.exists() and PREDICTIONS_FOLDER.is_dir():
            shutil.rmtree(PREDICTIONS_FOLDER)
            print(f"🗑️ Pasta removida: {PREDICTIONS_FOLDER}")
        else:
            print(f"⚠️ Pasta não encontrada para remoção: {PREDICTIONS_FOLDER}")
    # Executa a função principal
    insert_all_predictions()

if __name__ == "__main__":
    run_insert_predictions()
