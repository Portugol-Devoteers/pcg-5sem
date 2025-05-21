import os
import pandas as pd
import psycopg

def insert_descriptive_stats_from_parquets():
    USER_ID = 1
    DESCRIPTIVE_DIR = "parquets/descriptive"

    conn = psycopg.connect(
        dbname="tcc_b3",
        user="writer",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    if not os.path.isdir(DESCRIPTIVE_DIR):
        print(f"📁 Pasta não encontrada: {DESCRIPTIVE_DIR}")
        return

    for arquivo in os.listdir(DESCRIPTIVE_DIR):
        if not arquivo.endswith(".parquet"):
            continue

        path_parquet = os.path.join(DESCRIPTIVE_DIR, arquivo)

        # Extrai PETR4.SA do padrão PETR4_SA_descriptive.parquet
        partes = arquivo.replace("_descriptive.parquet", "").split("_")
        if len(partes) < 2:
            print(f"⚠️ Nome de arquivo inesperado: {arquivo}")
            continue
        b3_code = f"{partes[0]}.{partes[1]}"

        # Busca company_id
        cur.execute("SELECT id FROM companies WHERE b3_code = %s", (b3_code,))
        row = cur.fetchone()
        if not row:
            print(f"⚠️ Empresa não encontrada: {b3_code}")
            continue
        company_id = row[0]

        # Lê Parquet
        df = pd.read_parquet(path_parquet)
        df.rename(columns={"25%": "p25", "75%": "p75", "IQR": "iqr"}, inplace=True)

        safe = lambda v: None if pd.isna(v) else float(v)

        for indicator, vals in df.iterrows():
            indicator = str(indicator).strip()

            # Descobre history_columns_id
            cur.execute("SELECT id FROM history_columns WHERE column_name = %s",
                        (indicator,))
            hc = cur.fetchone()
            if not hc:
                print(f"  ⚠️ Indicador não encontrado: {indicator}")
                continue
            history_id = hc[0]

            try:
                cur.execute(
                    """
                    INSERT INTO descriptive_stats (
                        company_id, history_columns_id,
                        count, mean, median, mode, std,
                        min, p25, p75, iqr, max,
                        updated_by_user_id
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (company_id, history_columns_id)
                    DO UPDATE SET
                        count  = EXCLUDED.count,
                        mean   = EXCLUDED.mean,
                        median = EXCLUDED.median,
                        mode   = EXCLUDED.mode,
                        std    = EXCLUDED.std,
                        min    = EXCLUDED.min,
                        p25    = EXCLUDED.p25,
                        p75    = EXCLUDED.p75,
                        iqr    = EXCLUDED.iqr,
                        max    = EXCLUDED.max,
                        updated_by_user_id = EXCLUDED.updated_by_user_id,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        company_id, history_id,
                        safe(vals.get("count")),  safe(vals.get("mean")),
                        safe(vals.get("median")), safe(vals.get("mode")),
                        safe(vals.get("std")),    safe(vals.get("min")),
                        safe(vals.get("p25")),    safe(vals.get("p75")),
                        safe(vals.get("iqr")),    safe(vals.get("max")),
                        USER_ID
                    )
                )
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️ Erro ao inserir/atualizar '{indicator}' ({b3_code}): {e}")
                continue

        conn.commit()
        print(f"✅ {b3_code}: descritivas inseridas/atualizadas")

    cur.close()
    conn.close()
    print("\n🎉 Processo concluído – duplicatas foram atualizadas e erros ignorados linha-a-linha.")

if __name__ == "__main__":
    insert_descriptive_stats_from_parquets()
