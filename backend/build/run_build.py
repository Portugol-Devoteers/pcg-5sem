from data_capture.run_create_table import run_create_table
from data_prediction.get_data.run_get_data import run_get_data
from data_prediction.utils.build_dataset import run_build_dataset
from training.run_models import run_models
from data_prediction.utils.insert_predictions import run_insert_predictions


def run_build():
    """
    Executa o processo de construção do banco de dados.
    """
    print("🔄 Iniciando o processo de construção do banco de dados...")

    # Passo 1: Criar tabelas
    # run_create_table()

    # Passo 2: Coletar dados
    # run_get_data()

    # Passo 3: Construir dataset
    # run_build_dataset()

    # Passo 4: Treinar modelos
    # run_models()

    # Passo 5: Inserir previsões no banco de dados
    run_insert_predictions()

    print("✅ Processo de construção do banco de dados concluído.")

if __name__ == "__main__":
    run_build()