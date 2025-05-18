# data_prediction/utils/build_dataset.py
from pathlib import Path
import pandas as pd
from connection import get_conn          # ← import local
# ---------------------------------------------------------------- #
BASE  = Path(__file__).resolve().parent.parent
DATA  = BASE / "get_data" / "data"
PRICE = DATA / "price_chunks"
MACRO = DATA / "macro_chunks"
FIN   = DATA / "financial_statements_chunks"
FEAT  = BASE / "get_data" / "features"; FEAT.mkdir(parents=True, exist_ok=True)
PRICE_COLS = ["open","high","low","close","volume"]

def _to_dt(df):
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.sort_values("date")

def _load_price(path, col):
    return _to_dt(pd.read_parquet(path).rename(columns={"value": col}))

def build_dataset(empresa_nome:str, horizon:int=7, lookback_years:int=4):
    # --- ids ---
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, sector_id FROM companies WHERE name=%s",(empresa_nome,))
        cid, sid = cur.fetchone()
        cur.execute("SELECT id FROM companies WHERE sector_id=%s AND id<>%s",(sid,cid))
        peers = [r[0] for r in cur.fetchall()]

    # --- alvo ---
    base = _load_price(PRICE / f"{cid}_close.parquet", "close")
    max_d = base.date.max()
    min_d = max_d - pd.Timedelta(days=lookback_years*365 + horizon)
    base  = base[base.date.between(min_d, max_d - pd.Timedelta(days=horizon))].copy()

    # helper
    def merge_feat(df):
        nonlocal base
        base = base.merge(df, on="date", how="left")

    # --- próprias colunas ---
    for col in ("open","high","low","volume"):
        p = PRICE / f"{cid}_{col}.parquet"
        if p.exists():
            df = _load_price(p, col)
            merge_feat(df)
            base[col] = base[col].ffill()

    # --- pares de setor ---
    for pid in peers:
        for col in PRICE_COLS:
            p = PRICE / f"{pid}_{col}.parquet"
            if p.exists():
                name = f"{pid}_{col}"
                df = _load_price(p, name)
                merge_feat(df)
                base[name] = base[name].ffill()

    # --- macro ---
    for f in MACRO.glob("*.parquet"):
        name = f"macro_{f.stem}"
        df   = _load_price(f, name)
        merge_feat(df)
        base[name] = base[name].ffill()

    # --- balanço ---
    for f in FIN.glob(f"{cid}_*.parquet"):
        fin = pd.read_parquet(f)                 # account_id, reference_date, value
        fin["value"] = pd.to_numeric(fin["value"], errors="coerce")  # "\N" → NaN
        wide = (fin.pivot(index="reference_date", columns="account_id", values="value")
                   .asfreq("D")      # diário
                   .ffill()          # para frente
                   .bfill()          # para trás (preenche início)
                   .reset_index()
                   .rename(columns={"reference_date":"date"}))
        wide.columns = ["date"] + [f"acct_{c}" for c in wide.columns[1:]]
        merge_feat(_to_dt(wide))
        # forward fill das novas cols (já bfill feitas, mas garante continuidade diária)
        new_cols = [c for c in wide.columns if c != "date"]
        base[new_cols] = base[new_cols].ffill()

    # --- salvar ---
    out = FEAT / f"{cid}_dataset.parquet"
    base.to_parquet(out, index=False)
    print("✅ Dataset salvo em", out)
    return base

# uso direto para testar
if __name__ == "__main__":
    build_dataset("Petrobras")
