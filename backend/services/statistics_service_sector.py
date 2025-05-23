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
# ------------------------------------------------------------------
# Estatísticas filtradas por setor
# ------------------------------------------------------------------
def gerar_estatisticas_por_setor(sector_id: int):
    """
    Calcula métricas (MAE, RMSE, SMAPE, R2, Hit-rate) considerando
    apenas empresas cujo companies.sector_id = sector_id.
    """
    with get_conn() as conn, conn.cursor() as cur:

        # 1) “vencedor” por dia/papel *dentro do setor*
        cur.execute("""
            WITH ranked AS (
              SELECT p.*,
                     m.model,
                     ROW_NUMBER() OVER (
                       PARTITION BY p.date, p.b3_code_id
                       ORDER BY ABS(p.value - ph.close) / ph.close
                     ) AS rk
              FROM predictions      p
              JOIN companies        c  ON c.id         = p.b3_code_id
              JOIN models           m  ON m.id         = p.model_id
              JOIN history_columns  hc ON hc.id        = p.history_columns_id
              JOIN price_history    ph ON ph.company_id = p.b3_code_id
                                       AND ph.date      = p.date
              WHERE hc.column_name ILIKE 'close'
                AND c.sector_id     = %s               -- <-- filtro
            )
            SELECT r.date,
                   r.b3_code_id,
                   r.model,
                   r.value       AS y_pred,
                   ph.close      AS y_true
            FROM ranked r
            JOIN price_history ph
              ON ph.company_id = r.b3_code_id
             AND ph.date       = r.date
            WHERE r.rk = 1;
        """, (sector_id,))

        winners = pd.DataFrame(
            cur.fetchall(),
            columns=["date", "b3_code_id", "model", "y_pred", "y_true"]
        )

        # 2) price_history só das empresas do setor
        cur.execute("""
            SELECT company_id      AS b3_code_id,
                   date,
                   close
            FROM price_history    ph
            JOIN companies        c  ON c.id = ph.company_id
            WHERE c.sector_id = %s
            ORDER BY b3_code_id, date
        """, (sector_id,))
        ph = pd.DataFrame(cur.fetchall(),
                          columns=["b3_code_id", "date", "close"])

    # ---------- mesma rotina de pós-processamento ------------------
    winners = winners.dropna(subset=["y_true", "y_pred"]).copy()
    winners[["y_true", "y_pred"]] = winners[["y_true", "y_pred"]].astype(float)

    winners["abs_err"] = np.abs(winners["y_true"] - winners["y_pred"])
    winners["pct_err"] = winners["abs_err"] / winners["y_true"] * 100

    ph["prev_close"] = ph.groupby("b3_code_id")["close"].shift(1)
    winners = winners.merge(
        ph[["b3_code_id", "date", "prev_close"]],
        on=["b3_code_id", "date"],
        how="left"
    ).dropna(subset=["prev_close"])
    winners["prev_close"] = winners["prev_close"].astype(float)

    winners["hit"] = (
        np.sign(winners["y_true"] - winners["prev_close"]) ==
        np.sign(winners["y_pred"] - winners["prev_close"])
    )

    mae  = winners["abs_err"].mean()
    rmse = np.sqrt((winners["abs_err"] ** 2).mean())
    smp  = smape(winners["y_true"], winners["y_pred"])
    r2   = r2_score(winners["y_true"], winners["y_pred"])
    hitp = hit_rate(winners)

    stats = {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "SMAPE_%": round(smp, 3),
        "R2": round(r2, 4),
        "Hit_rate_%": round(hitp, 2),
        "n_observacoes": len(winners)
    }
    return stats, winners

if __name__ == "__main__":
    setor = 7         # exemplo
    stats, df = gerar_estatisticas_por_setor(setor)

    print(f"Métricas – setor {setor}:")
    for k, v in stats.items():
        print(f"{k}: {v}")

    # print("\nAmostra de vencedores:")
    # print(df.head())
