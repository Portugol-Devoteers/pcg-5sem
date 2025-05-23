# statistics_service.py
import psycopg
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score
from typing import Dict, List, Any


# ------------------------------------------------------------------
# Conexão
# ------------------------------------------------------------------
def get_conn():
    return psycopg.connect(
        dbname="tcc_b3",
        user="compareter",
        password="postgres",
        host="localhost",
        port="5432"
    )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    return float(np.mean(np.abs(y_pred - y_true) / denom) * 100)


def hit_rate(df: pd.DataFrame) -> float:
    return float(df["hit"].mean() * 100)


def _numpy_to_py(obj: Any) -> Any:
    """Converte np.* ou pd.Timestamp em tipos nativos JSON‐safe."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


# ------------------------------------------------------------------
# Função principal
# ------------------------------------------------------------------
def gerar_estatisticas_gerais() -> Dict[str, Any]:
    """
    Calcula métricas gerais (MAE, RMSE, SMAPE, R², Hit-rate)
    considerando apenas o “vencedor” (melhor modelo) de cada
    dia/papel. Retorna um dicionário pronto para ir pro FastAPI.
    """

    with get_conn() as conn, conn.cursor() as cur:
        # ----------------------------------------------------------
        # 1) Quem foi o “vencedor” em cada dia/papel
        # ----------------------------------------------------------
        cur.execute(
            """
            WITH ranked AS (
              SELECT  p.*,
                      m.model,
                      ROW_NUMBER() OVER (
                        PARTITION BY p.date, p.b3_code_id
                        ORDER BY ABS(p.value - ph.close) / ph.close
                      ) AS rk
              FROM predictions      p
              JOIN models           m  ON m.id = p.model_id
              JOIN history_columns  hc ON hc.id = p.history_columns_id
              JOIN price_history    ph ON ph.company_id = p.b3_code_id
                                       AND ph.date      = p.date
              WHERE hc.column_name ILIKE 'close'
            )
            SELECT  r.date,
                    r.b3_code_id,
                    r.model,
                    r.value   AS y_pred,
                    ph.close  AS y_true
            FROM ranked r
            JOIN price_history ph
              ON ph.company_id = r.b3_code_id
             AND ph.date       = r.date
            WHERE r.rk = 1;
            """
        )
        winners = pd.DataFrame(
            cur.fetchall(),
            columns=["date", "b3_code_id", "model", "y_pred", "y_true"]
        )

        # ----------------------------------------------------------
        # 2) Fechamento do dia anterior (para o hit)
        # ----------------------------------------------------------
        cur.execute(
            """
            SELECT company_id AS b3_code_id,
                   date,
                   close
            FROM price_history
            ORDER BY b3_code_id, date;
            """
        )
        ph = pd.DataFrame(cur.fetchall(), columns=["b3_code_id", "date", "close"])

    # ----------------------------------------------------------------
    # Pós-processamento
    # ----------------------------------------------------------------
    winners = winners.dropna(subset=["y_true", "y_pred"]).copy()
    winners[["y_true", "y_pred"]] = winners[["y_true", "y_pred"]].astype(float)

    # Erros absolutos e percentuais
    winners["abs_err"] = np.abs(winners["y_true"] - winners["y_pred"])
    winners["pct_err"] = winners["abs_err"] / winners["y_true"] * 100

    # Hit-rate
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

    # ----------------------------------------------------------------
    # Métricas
    # ----------------------------------------------------------------
    mae   = float(winners["abs_err"].mean())
    rmse  = float(np.sqrt((winners["abs_err"] ** 2).mean()))
    smp   = smape(winners["y_true"].values, winners["y_pred"].values)
    try:
        r2   = float(r2_score(winners["y_true"], winners["y_pred"]))
    except ValueError:      # r² exige pelo menos 2 pontos distintos
        r2   = float("nan")
    hitp  = hit_rate(winners)

    stats: Dict[str, Any] = {
        "MAE":        round(mae, 4),
        "RMSE":       round(rmse, 4),
        "SMAPE_%":    round(smp, 3),
        "R2":         round(r2, 4) if not np.isnan(r2) else None,
        "Hit_rate_%": round(hitp, 2),
        "n_obs":      int(len(winners)),
    }

    # ----------------------------------------------------------------
    # Winners → lista de dicionários só com tipos nativos
    # ----------------------------------------------------------------
    winners_json: List[Dict[str, Any]] = (
        winners
        .applymap(_numpy_to_py)
        .assign(date=lambda df: df["date"].astype(str))  # ISO-8601
        .to_dict(orient="records")
    )

    return {
        "stats": stats,
        "winners": winners_json
    }


# ------------------------------------------------------------------
# Execução direta
# ------------------------------------------------------------------
if __name__ == "__main__":
    result = gerar_estatisticas_gerais()
    print("\nMétricas gerais:")
    for k, v in result["stats"].items():
        print(f"{k}: {v}")
    # print("\nAmostra de winners:", result["winners"][:3])
