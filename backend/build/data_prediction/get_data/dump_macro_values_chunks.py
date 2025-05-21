# src/data_prediction/dump_macro_chunks.py

from pathlib import Path
import pandas as pd
from data_prediction.get_data.connection_trainer import get_conn_trainer  # ou from .connection se for import relativo

def dump_macro_values_chunks():
    """
    Exporta macro_values em Parquet:
      – um arquivo por macro_indicator_id
      – colunas: date, value
      – destino: data/macro_chunks/{macro_indicator_id}.parquet
    """
    # Diretório relativo ao arquivo
    BASE_DIR = Path(__file__).resolve().parent
    output_folder = BASE_DIR / "data" / "macro_chunks"
    output_folder.mkdir(parents=True, exist_ok=True)

    conn = get_conn_trainer()
    df = pd.read_sql(
        """
        SELECT date, macro_indicator_id, value
        FROM macro_values
        """,
        conn
    )
    conn.close()

    for macro_id, grp in df.groupby("macro_indicator_id"):
        subset = grp[["date", "value"]].dropna()
        file_path = output_folder / f"{macro_id}.parquet"
        subset.to_parquet(file_path, index=False, compression="snappy")

    print(f"✅ {len(df)} linhas exportadas em {output_folder}")
