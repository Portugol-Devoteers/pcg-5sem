#%%
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import psycopg

# Conexão com o banco
conn_params = {
    "dbname": "tcc_b3",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

# Datas
end_date = datetime.today()
start_date = end_date - timedelta(days=730)

def get_data(ticker, name):
    df = yf.download(ticker, start=start_date, end=end_date)[['Close']]
    df.columns = [name]
    df.index.name = 'date'
    return df.reset_index().set_index('date')

# Baixar dados reais
ibov = get_data("^BVSP", "ibov")
usdbrl = get_data("USDBRL=X", "usd_brl")

# Usa as datas reais do mercado como base
base = ibov.join(usdbrl, how="inner")

# Adiciona as variáveis simuladas
base["selic"] = 13.75
base["ipca"] = 0.40

# Reorganiza as colunas
df = base[["selic", "ipca", "usd_brl", "ibov"]].dropna().reset_index()

# Criação da tabela
create_table = """
CREATE TABLE IF NOT EXISTS macro_indicators (
    date DATE PRIMARY KEY,
    selic NUMERIC(5, 2),
    ipca NUMERIC(5, 3),
    usd_brl NUMERIC(5, 3),
    ibov NUMERIC(10, 2)
);
"""

# Inserção com upsert
insert = """
INSERT INTO macro_indicators (date, selic, ipca, usd_brl, ibov)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (date) DO UPDATE SET
    selic = EXCLUDED.selic,
    ipca = EXCLUDED.ipca,
    usd_brl = EXCLUDED.usd_brl,
    ibov = EXCLUDED.ibov;
"""

# Envia para o banco
with psycopg.connect(**conn_params) as conn:
    with conn.cursor() as cur:
        cur.execute(create_table)
        for _, row in df.iterrows():
            cur.execute(insert, (
                row['date'].date(),
                round(row['selic'], 2),
                round(row['ipca'], 3),
                round(row['usd_brl'], 3),
                round(row['ibov'], 2)
            ))
    conn.commit()

print(f"Total de registros para inserção: {len(df)}")
print("Dados inseridos com sucesso no banco!")


# %%
