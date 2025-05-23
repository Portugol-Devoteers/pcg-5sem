# statistics_service.py

import psycopg
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score

# ---------------------------
# Conexão
# ---------------------------
def get_conn():
    return psycopg.connect(
        dbname="tcc_b3",
        user="compareter",
        password="postgres",
        host="localhost",
        port="5432"
    )

# ---------------------------
# Helpers
# ---------------------------
def smape(y_true, y_pred):
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    return np.mean(np.abs(y_pred - y_true) / denom) * 100

def hit_rate(df):
    return df["hit"].mean() * 100

# ---------------------------
# Função principal
# ---------------------------
def gerar_estatisticas_gerais():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            WITH ranked AS (
              SELECT p.*,
                     m.model,
                     hc.column_name,
                     ROW_NUMBER() OVER (
                       PARTITION BY p.date, p.b3_code_id
                       ORDER BY ABS(p.value - ph.close) / ph.close
                     ) AS rk
              FROM predictions p
              JOIN models          m  ON p.model_id = m.id
              JOIN history_columns hc ON p.history_columns_id = hc.id
              JOIN price_history   ph ON ph.company_id = p.b3_code_id
                                      AND ph.date = p.date
              WHERE hc.column_name ILIKE 'close'
            )
            SELECT ranked.date,
                   ranked.b3_code_id,
                   ranked.model,
                   ranked.value AS y_pred,
                   ph.close     AS y_true
            FROM ranked
            JOIN price_history ph ON ph.company_id = ranked.b3_code_id
                                  AND ph.date = ranked.date
            WHERE ranked.rk = 1;
        """)
        
        winners = pd.DataFrame(cur.fetchall(),
                               columns=["date","b3_code_id","model","y_pred","y_true"])
        

        # 1. Carrega price_history (só 3 colunas bastam) (para calcular o hit)
        cur.execute("""
            SELECT company_id      AS b3_code_id,
                date,
                close
            FROM price_history
            ORDER BY b3_code_id, date
        """)
        ph = pd.DataFrame(cur.fetchall(), columns=["b3_code_id", "date", "close"])

    # Garantir que não há NaN e tipo numérico
    winners = winners.dropna(subset=["y_true", "y_pred"]).copy()
    winners["y_true"] = winners["y_true"].astype(float)
    winners["y_pred"] = winners["y_pred"].astype(float)

    # Cálculo dos erros
    winners["abs_err"] = np.abs(winners["y_true"] - winners["y_pred"])
    winners["pct_err"] = winners["abs_err"] / winners["y_true"] * 100

#------------------------------------------------------------------------------------------------
    # Cálculo do hit: direção correta?
    # 2. Calcula o close do dia imediatamente anterior
    ph["prev_close"] = ph.groupby("b3_code_id")["close"].shift(1)

    # 3. Mantém só (código, data, prev_close) e faz o merge
    prev = ph[["b3_code_id", "date", "prev_close"]]
    winners = winners.merge(prev, on=["b3_code_id", "date"], how="left")
    winners = winners.dropna(subset=["prev_close"])

    # converte prev_close de Decimal → float
    winners["prev_close"] = winners["prev_close"].astype(float)

    # Cálculo do hit com base no prev_close
    winners["hit"] = (
        np.sign(winners["y_true"] - winners["prev_close"]) ==
        np.sign(winners["y_pred"] - winners["prev_close"])
    )

#------------------------------------------------------------------------------------------------

    # Métricas
    mae = winners["abs_err"].mean()
    rmse = np.sqrt((winners["abs_err"] ** 2).mean())
    smape_val = smape(winners["y_true"], winners["y_pred"])
    r2 = r2_score(winners["y_true"], winners["y_pred"])
    hit = hit_rate(winners)
    
    stats = {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "SMAPE_%": round(smape_val, 3),
        "R2": round(r2, 4),
        "Hit_rate_%": round(hit, 2),
        "n_observacoes": len(winners)
    }

    return stats#, winners

# ---------------------------
# Execução simples
# ---------------------------
if __name__ == "__main__":
    stats, winners_df = gerar_estatisticas_gerais()

    print("Métricas gerais:")
    for k, v in stats.items():
        print(f"{k}: {v}")

    # print("\nAmostra de vencedores:")
    # print(winners_df.head())
