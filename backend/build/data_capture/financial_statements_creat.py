import os
from pathlib import Path
import pandas as pd
import psycopg

def insert_financial_statements_from_parquets():
    USER_ID = 1

    BASE_PATH = Path(__file__).resolve().parent.parent
    
    PATHS = {
        "DRE":      (BASE_PATH.joinpath("data_capture", "parquets", "DRE"),      1),
        "Balance":  (BASE_PATH.joinpath("data_capture", "parquets", "balance"),  2),
        "Cashflow": (BASE_PATH.joinpath("data_capture", "parquets", "cashflow"), 3)
    }
    
    TYPE_IDS = {"DRE": 1, "Balance": 2, "Cashflow": 3}

    with psycopg.connect(
        dbname="tcc_b3",
        user="writer",
        password="postgres",
        host="localhost",
        port="5432"
    ) as conn, conn.cursor() as cur:

        for tipo_nome, (pasta, tipo_id) in PATHS.items():
            tipo_id = TYPE_IDS[tipo_nome]
            if not os.path.isdir(pasta):
                print(f"📁 Pasta não encontrada: {pasta}")
                continue

            for arquivo in os.listdir(pasta):
                if not arquivo.endswith(".parquet"):
                    continue

                # Ex.: AALR3_SA_dre.parquet  →  AALR3.SA
                parte1, parte2, *_ = arquivo.split('_')
                b3_code = f"{parte1}.{parte2}"

                cur.execute("SELECT id FROM companies WHERE b3_code = %s", (b3_code,))
                row = cur.fetchone()
                if not row:
                    print(f"⚠️ Empresa não encontrada: {b3_code}")
                    continue
                company_id = row[0]

                df = (
                    pd.read_parquet(os.path.join(pasta, arquivo))
                    .reset_index()                       # traz o índice para colunas
                    .rename(columns={'index': 'account_name'})  # garante o nome correto
                )
                df.rename(columns={df.columns[0]: "account_name"}, inplace=True)

                # transforma wide → long: conta | reference_date | value
                long_df = (
                    df.melt(
                        id_vars="account_name",
                        var_name="reference_date",
                        value_name="value"
                    )
                    .dropna(subset=["value"])
                )

                for _, r in long_df.iterrows():
                    account_name   = str(r["account_name"]).strip()
                    reference_date = pd.to_datetime(r["reference_date"]).date()
                    value          = r["value"]

                    cur.execute(
                        "SELECT id FROM financial_accounts "
                        "WHERE name = %s AND statement_type_id = %s",
                        (account_name, tipo_id)
                    )
                    acc = cur.fetchone()
                    if not acc:
                        print(f"  ⚠️ Conta não encontrada: {account_name} ({tipo_nome})")
                        continue
                    account_id = acc[0]

                    try:
                        cur.execute(
                            """
                            INSERT INTO financial_statements
                                (company_id, account_id, reference_date, value, updated_by_user_id)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (company_id, account_id, reference_date)
                            DO UPDATE SET
                                value              = EXCLUDED.value,
                                updated_by_user_id = EXCLUDED.updated_by_user_id,
                                updated_at         = CURRENT_TIMESTAMP;
                            """,
                            (company_id, account_id, reference_date, value, USER_ID)
                        )
                    except Exception as e:
                        conn.rollback()  # descarta só a linha
                        print(f"  ❌ Erro em '{account_name}' {b3_code}: {e}")

                conn.commit()  # fecha o Parquet
                print(f"✅ {b3_code}: demonstrativo {tipo_nome} inserido/atualizado")

    print("\n🎉 Processo concluído – todos os Parquets percorridos.")

if __name__ == "__main__":
    insert_financial_statements_from_parquets()
