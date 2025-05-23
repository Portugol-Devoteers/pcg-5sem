# comparison_service.py
import psycopg
import pandas as pd


# ----------------------------------------------------------------------
# 1) Conexão ----------------------------------------------------------------
# ----------------------------------------------------------------------
def get_connection():
    """Retorna uma conexão psycopg já configurada."""
    return psycopg.connect(
        dbname="tcc_b3",
        user="compareter",
        password="postgres",
        host="localhost",
        port="5432"
    )


# ----------------------------------------------------------------------
# 2) Utilitários de price_history --------------------------------------
# ----------------------------------------------------------------------
def fetch_price_history_columns(conn, df):
    """
    Para cada linha do DataFrame, busca:
      • price_history_value  (na própria data)
      • price_history_value_anterior (data imediatamente anterior)
    Retorna duas listas na ordem do DataFrame.
    """
    atual, anterior = [], []

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            col = row["history_column_name"].lower()

            # valor atual
            cur.execute(
                f"""SELECT ph."{col}"
                    FROM price_history ph
                    WHERE ph.date = %s AND ph.company_id = %s""",
                (row["date"], row["b3_code_id"]),
            )
            atual.append((cur.fetchone() or [None])[0])

            # valor anterior
            cur.execute(
                f"""SELECT ph."{col}"
                    FROM price_history ph
                    WHERE ph.date < %s AND ph.company_id = %s
                    ORDER BY ph.date DESC
                    LIMIT 1""",
                (row["date"], row["b3_code_id"]),
            )
            anterior.append((cur.fetchone() or [None])[0])

    return atual, anterior


# ----------------------------------------------------------------------
# 3) Dados de uma empresa (curto / longo / vencedores) -----------------
# ----------------------------------------------------------------------
def load_company_predictions(conn, company_id):
    """Carrega as 9 datas mais recentes da empresa + dados auxiliares."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT date
            FROM predictions
            WHERE b3_code_id = %s
            ORDER BY date DESC
            LIMIT 9
            """,
            (company_id,),
        )
        ultimas_datas = [r[0] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT
                p.date,
                m.model AS model_name,
                p.value,
                c.name  AS company_name,
                hc.column_name AS history_column_name,
                p.history_columns_id,
                p.b3_code_id
            FROM predictions p
            JOIN models          m  ON p.model_id          = m.id
            JOIN companies       c  ON p.b3_code_id        = c.id
            JOIN history_columns hc ON p.history_columns_id = hc.id
            WHERE p.b3_code_id = %s
              AND p.date = ANY(%s)
            ORDER BY p.date DESC
            """,
            (company_id, ultimas_datas),
        )
        cols = [
            "date",
            "model_name",
            "value",
            "company_name",
            "history_column_name",
            "history_columns_id",
            "b3_code_id",
        ]
        return pd.DataFrame(cur.fetchall(), columns=cols)


def calcular_metricas(df):
    """Adiciona comparison_percent, error_percent, ordena date/model."""
    df["comparison_percent"] = (
        100 - (df["value"].sub(df["price_history_value"]).abs()
               / df["price_history_value"] * 100)
    ).round(3)

    df["error_percent"] = (
        df["value"].sub(df["price_history_value"]).abs()
        / df["price_history_value"] * 100
    ).round(3)

    return df.sort_values(["date", "model_name"]).reset_index(drop=True)


def gerar_resumos_empresa(conn, company_id):
    """Retorna df da empresa, vencedores/dia, curto, longo."""
    df = load_company_predictions(conn, company_id)

    # Preenche price_history
    at, ant = fetch_price_history_columns(conn, df)
    df["price_history_value"] = at
    df["price_history_value_anterior"] = ant
    df = df[df["price_history_value"].notnull()].reset_index(drop=True)
    df = calcular_metricas(df)

    # melhor modelo por dia
    vencedores = df.loc[
        df.groupby("date")["error_percent"].idxmin(),
        ["date", "model_name", "error_percent"],
    ].reset_index(drop=True)

    # curto / longo
    curto = df[df["date"] == df["date"].min()].sort_values("error_percent")
    longo = df[df["date"] == df["date"].max()].sort_values("error_percent")

    return df, vencedores, curto, longo


# ----------------------------------------------------------------------
# 4) Dataset geral (todas as empresas)  --------------------------------
# ----------------------------------------------------------------------
def load_all_predictions(conn):
    """Carrega todas as linhas de predictions com joins auxiliares."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.date,
                m.model AS model_name,
                p.value,
                c.name  AS company_name,
                hc.column_name AS history_column_name,
                p.history_columns_id,
                p.b3_code_id
            FROM predictions p
            JOIN models          m  ON p.model_id          = m.id
            JOIN companies       c  ON p.b3_code_id        = c.id
            JOIN history_columns hc ON p.history_columns_id = hc.id
            ORDER BY p.b3_code_id, p.date DESC
            """
        )
        cols = [
            "date",
            "model_name",
            "value",
            "company_name",
            "history_column_name",
            "history_columns_id",
            "b3_code_id",
        ]
        return pd.DataFrame(cur.fetchall(), columns=cols)


def adicionar_variancias(df):
    """Adiciona variance_prediction, real_variance, variance_accuracy."""
    # valor de referência (primeira price_history_value_anterior por empresa)
    ref_dict = (
        df.groupby("b3_code_id")["price_history_value_anterior"]
        .first()
        .to_dict()
    )

    def _calc(row):
        ref = ref_dict.get(row["b3_code_id"])
        if pd.isna(ref):
            return pd.Series([None, None, None])
        pred = "up" if row["value"] - ref >= 0 else "down"
        real = "up" if row["price_history_value"] - ref >= 0 else "down"
        return pd.Series([pred, real, pred == real])

    df[["variance_prediction", "real_variance", "variance_accuracy"]] = (
        df.apply(_calc, axis=1)
    )
    return df


def calcular_acuracias(df):
    """Gera dois DataFrames: acertos por modelo e por data."""
    base = df.dropna(subset=["variance_accuracy"])

    def _agg(group):
        total = len(group)
        total_acertos = group["variance_accuracy"].sum()
        geral = round(total_acertos / total * 100, 2) if total else None

        # up/down
        tot_up = len(group[group["variance_prediction"] == "up"])
        tot_dn = len(group[group["variance_prediction"] == "down"])

        up_ok = len(
            group[
                (group["variance_prediction"] == "up")
                & (group["variance_prediction"] == group["real_variance"])
            ]
        )
        dn_ok = len(
            group[
                (group["variance_prediction"] == "down")
                & (group["variance_prediction"] == group["real_variance"])
            ]
        )

        up_acc = round(up_ok / tot_up * 100, 2) if tot_up else None
        dn_acc = round(dn_ok / tot_dn * 100, 2) if tot_dn else None
        return pd.Series(
            {
                "up_accuracy_percent": up_acc,
                "down_accuracy_percent": dn_acc,
                "geral_accuracy_percent": geral,
            }
        )

    acertos_modelo = base.groupby("model_name").apply(_agg).reset_index()
    acertos_data = base.groupby("date").apply(_agg).reset_index()
    return acertos_modelo, acertos_data


def anexar_acuracias(df_base, acc_model, acc_date):
    """Adiciona colunas de acurácia do modelo e da data."""
    acc_model = acc_model.rename(
        columns={
            "up_accuracy_percent": "up_accuracy_percent_model",
            "down_accuracy_percent": "down_accuracy_percent_model",
            "geral_accuracy_percent": "geral_accuracy_percent_model",
        }
    )
    acc_date = acc_date.rename(
        columns={
            "up_accuracy_percent": "up_accuracy_percent_date",
            "down_accuracy_percent": "down_accuracy_percent_date",
            "geral_accuracy_percent": "geral_accuracy_percent_date",
        }
    )
    df_out = df_base.merge(acc_model, on="model_name", how="left")
    df_out = df_out.merge(acc_date, on="date", how="left")
    return df_out


# ----------------------------------------------------------------------
# 5) Função principal de serviço ---------------------------------------
# ----------------------------------------------------------------------
def comparar_dados_empresa(ticker: str):
    """
    Pipeline completo:
      • dados da empresa (df, vencedores, curto, longo)
      • dataset geral -> acurácias
      • consolida tudo num dicionário de DataFrames
    """

    with get_connection() as conn:
        # ----- busca id da empresa
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM companies WHERE b3_code = %s", (ticker,)
            )
            company_id = (cur.fetchone() or [None])[0]

    with get_connection() as conn:
        # ----- empresa específica
        df_emp, vencedores_emp, curto_emp, longo_emp = gerar_resumos_empresa(
            conn, company_id
        )

        # ----- dataset geral + variâncias
        df_all = load_all_predictions(conn)
        at, ant = fetch_price_history_columns(conn, df_all)
        df_all["price_history_value"] = at
        df_all["price_history_value_anterior"] = ant
        df_all = df_all[df_all["price_history_value"].notnull()].reset_index(
            drop=True
        )
        df_all = adicionar_variancias(
            df_all
        )  # adiciona variance_* e accuracy

    # ----- acurácias globais
    acc_model, acc_date = calcular_acuracias(df_all)

    # ----- consolida acurácias nos DataFrames da empresa
    df_emp_full = anexar_acuracias(df_emp, acc_model, acc_date)
    vencedores_full = anexar_acuracias(vencedores_emp, acc_model, acc_date)
    curto_full = anexar_acuracias(curto_emp, acc_model, acc_date)
    longo_full = anexar_acuracias(longo_emp, acc_model, acc_date)


    return {
        # "vencedores": data_to_json(vencedores_full),
        "short_term": data_to_json(curto_full),
        "long_term": data_to_json(longo_full),
        "company_name": curto_full["company_name"].iloc[0],
    }

def data_to_json(data):
    """
    Converte um DataFrame em um dicionário JSON.
    """
    return data.to_dict(orient="records")
# ----------------------------------------------------------------------
# Execução simples -----------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    resultado = comparar_dados_empresa("PETR4.SA")

import pandas as pd
import json

def jsons_to_excel(json_dict, output_file="comparacao_resultados.xlsx"):
    """
    Converte dicionário de listas (output de data.to_dict) em múltiplas abas de um Excel.

    :param json_dict: dict {nome: lista_de_dicts}
    :param output_file: nome do arquivo de saída
    """
    with pd.ExcelWriter(output_file) as writer:
        for nome, json_data in json_dict.items():
            # Converte lista de dicts para DataFrame
            df = pd.DataFrame(json_data)
            # Salva como uma aba no Excel
            df.to_excel(writer, sheet_name=nome[:31], index=False)  # Excel limita sheet a 31 chars

    print(f"Arquivo Excel salvo como: {output_file}")

# jsons_to_excel(resultado, output_file="resultado_empresa_1.xlsx")
