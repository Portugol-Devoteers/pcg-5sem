import psycopg
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score
import json

# --------------------------- conexao ---------------------------
def get_conn():
    return psycopg.connect(
        dbname="tcc_b3",
        user="compareter",
        password="postgres",
        host="localhost",
        port="5432"
    )

# --------------------------- métricas auxiliares ----------------
def smape(y_true, y_pred):
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    return np.mean(np.abs(y_pred - y_true) / denom) * 100

def hit_rate(df):
    return df["hit"].mean() * 100


def to_py(obj):
    "Converte np.* para int/float padrão."
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj

# --------------------------- principal --------------------------
def gerar_estatisticas_por_setor(sector_id: int) -> dict:
    """
    Calcula MAE, RMSE, SMAPE, R² e Hit-rate
    só para empresas cujo companies.sector_id = sector_id.
    Retorna um dicionário JSON-serializável.
    """
    with get_conn() as conn, conn.cursor() as cur:
        # 1) vencedor do dia/papel (dentro do setor)
        cur.execute(
            """
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
                JOIN sectors        s  ON s.id         = c.sector_id
              WHERE hc.column_name ILIKE 'close'
                AND c.sector_id     = %s
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
            """,
            (sector_id,),
        )
        winners = pd.DataFrame(
            cur.fetchall(),
            columns=["date", "b3_code_id", "model", "y_pred", "y_true"]
        )

        # 2) preço de fechamento anterior
        cur.execute(
            """
            SELECT company_id AS b3_code_id,
                   date,
                   close
            FROM price_history ph
            JOIN companies     c ON c.id = ph.company_id
            WHERE c.sector_id = %s
            ORDER BY b3_code_id, date;
            """,
            (sector_id,),
        )
        ph = pd.DataFrame(cur.fetchall(), columns=["b3_code_id", "date", "close"])

    # -------------------- pós-processamento -----------------------
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
        np.sign(winners["y_true"] - winners["prev_close"])
        == np.sign(winners["y_pred"] - winners["prev_close"])
    )

    mae  = winners["abs_err"].mean()
    rmse = np.sqrt((winners["abs_err"] ** 2).mean())
    smp  = smape(winners["y_true"], winners["y_pred"])
    r2   = r2_score(winners["y_true"], winners["y_pred"])
    hitp = hit_rate(winners)

    stats = {
        "MAE":       float(round(mae, 4)),
        "RMSE":      float(round(rmse, 4)),
        "SMAPE_percentage":   float(round(smp, 3)),
        "R2":        float(round(r2, 4)),
        "Hit_rate_percentage":float(round(hitp, 2)),
        "n_obs":     int(len(winners)),
    }

    winners_json = (
        winners
        .applymap(to_py)          # tira np.float64 / np.int64
        .assign(date=lambda df: df["date"].astype(str))
        .to_dict(orient="records")
    )

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT name
            FROM sectors
            WHERE id = %s;
            """,
            (sector_id,),
        )
        sector_name = cur.fetchone()[0]

    return {
        "sector_name": sector_name,
        "stats": stats, 
        "winners": winners_json
    }

if __name__ == "__main__":
    setor = 7         # exemplo
    stats, df = gerar_estatisticas_por_setor(setor)

    print(f"Métricas – setor {setor}:")
    for k, v in stats.items():
        print(f"{k}: {v}")

    # print("\nAmostra de vencedores:")
    # print(df.head())
