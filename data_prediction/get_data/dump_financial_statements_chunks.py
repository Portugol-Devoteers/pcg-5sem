# src/data_prediction/dump_financial_chunks.py

from pathlib import Path
import pandas as pd
from connection import get_conn  # ou from .connection se estiver dentro de um pacote

def dump_financial_statements_chunks():
    """
    Gera arquivos Parquet (snappy) divididos por company_id e statement_type_id.

    • JOIN financial_statements → financial_accounts para obter statement_type_id
    • Arquivo:  {company_id}_{statement_type_id}.parquet
    • Colunas:  account_id, reference_date, value
    """
    # Diretório relativo ao arquivo atual
    BASE_DIR = Path(__file__).resolve().parent
    output_folder = BASE_DIR / "data" / "financial_statements_chunks"
    output_folder.mkdir(parents=True, exist_ok=True)

    conn = get_conn()

    query = """
        SELECT
            fs.company_id,
            fa.statement_type_id,
            fs.account_id,
            fs.reference_date,
            fs.value
        FROM financial_statements AS fs
        JOIN financial_accounts  AS fa ON fa.id = fs.account_id
    """

    df = pd.read_sql(query, conn)
    conn.close()

    for (company_id, stmt_type_id), grp in df.groupby(["company_id", "statement_type_id"]):
        file_path = output_folder / f"{company_id}_{stmt_type_id}.parquet"
        grp[["account_id", "reference_date", "value"]].dropna().to_parquet(
            file_path,
            index=False,
            compression="snappy"
        )

    print(f"✅ {len(df)} linhas exportadas em {output_folder} (Parquet por company_id + statement_type_id)")
