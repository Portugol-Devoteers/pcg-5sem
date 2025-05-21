# src/data_prediction/dump_price_chunks.py

import os
import pandas as pd
from pathlib import Path
from data_prediction.get_data.connection_trainer import get_conn_trainer  # ou from .connection se for import relativo

def dump_price_history_by_company_column():
    # Cria pasta: data_prediction/data/price_chunks
    BASE_DIR = Path(__file__).resolve().parent
    output_folder = BASE_DIR / "data" / "price_chunks"
    output_folder.mkdir(parents=True, exist_ok=True)

    conn = get_conn_trainer()

    query = """
    SELECT company_id, date, open, high, low, close, volume
    FROM price_history
    ORDER BY company_id, date
    """

    print("📥 Carregando dados da tabela price_history...")
    df = pd.read_sql(query, conn)

    print("🔄 Separando por company_id e coluna...")
    columns = ["open", "high", "low", "close", "volume"]
    grouped = df.groupby("company_id")

    for company_id, group in grouped:
        for col in columns:
            subset = group[["date", col]].dropna()
            subset = subset.rename(columns={col: "value"})
            file_name = f"{company_id}_{col}.parquet"
            path = output_folder / file_name
            subset.to_parquet(path, index=False)

    conn.close()
    print(f"✅ Arquivos salvos em {output_folder}")
