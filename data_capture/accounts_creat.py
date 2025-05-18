
import os
import pandas as pd
import psycopg
import psycopg.errors  # Importa as exceções específicas do psycopg

def insert_financial_accounts_from_csvs():
    # Configurações fixas
    USER_ID = 1
    PATHS = {
        "DRE":      ("csvs/dre",      1),
        "Balance":  ("csvs/balance",  2),
        "Cashflow": ("csvs/cashflow", 3)
    }

    # Conexão com o banco
    conn = psycopg.connect(
        dbname="tcc_b3",
        user="writer",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    for tipo_nome, (pasta, tipo_id) in PATHS.items():
        if not os.path.isdir(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            continue

        for arquivo in os.listdir(pasta):
            if not arquivo.endswith(".csv"):
                continue

            path_csv = os.path.join(pasta, arquivo)
            df = pd.read_csv(path_csv, index_col=0)

            for conta in df.index:
                conta_nome = str(conta).strip()

                try:
                    # Verifica se já existe
                    cur.execute("""
                        SELECT 1 FROM financial_accounts
                        WHERE statement_type_id = %s AND name = %s
                        LIMIT 1
                    """, (tipo_id, conta_nome))

                    if cur.fetchone():
                        continue  # já existe

                    # Insere nova conta
                    cur.execute("""
                        INSERT INTO financial_accounts (name, statement_type_id, updated_by_user_id)
                        VALUES (%s, %s, %s)
                    """, (conta_nome, tipo_id, USER_ID))
                    print(f"✅ Inserido: {conta_nome} ({tipo_nome})")

                except psycopg.errors.UniqueViolation:
                    # Trata a violação de unicidade e continua
                    print(f"⚠️ Violação de unicidade: {conta_nome} já existe no banco de dados.")
                    conn.rollback()  # Reverte a transação atual para evitar problemas
                    continue

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 Contas inseridas com sucesso!")

if __name__ == "__main__":
    insert_financial_accounts_from_csvs()