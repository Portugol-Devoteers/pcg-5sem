import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
import pandas as pd
import tensorflow as tf  # type: ignore
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.layers import GRU, Dense, Dropout  # type: ignore
from tensorflow.keras import Input  # type: ignore
import sys

# Fixar aleatoriedade
SEED = 42

def train(df: pd.DataFrame, sequence_length: int = 60, predict_days: int = 1):
    # Fixar seed novamente aqui
    import random
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)

    # Se houver colunas de concorrentes, inclui
    concorrente_cols = [col for col in df.columns if col.startswith("concorrente_")]

    feature_cols = ['close', 'volume', 'selic', 'ipca', 'usd_brl', 'ibov'] + concorrente_cols
    df[feature_cols] = df[feature_cols].astype(float)

    X_data = df[feature_cols].values
    y_data = df[['close']].values

    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()

    X_scaled = scaler_X.fit_transform(X_data)
    y_scaled = scaler_y.fit_transform(y_data)

    X, y = [], []
    for i in range(sequence_length, len(X_scaled)):
        X.append(X_scaled[i - sequence_length:i])
        y.append(y_scaled[i, 0])

    X, y = np.array(X), np.array(y)

    model = Sequential()
    model.add(Input(shape=(X.shape[1], X.shape[2])))
    model.add(GRU(units=50, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(GRU(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=20, batch_size=32, verbose=0)

    # Previsão recursiva dos próximos N dias
    last_sequence = X_scaled[-sequence_length:].copy()
    future_scaled_preds = []

    for _ in range(predict_days):
        input_seq = last_sequence.reshape(1, sequence_length, len(feature_cols))
        next_scaled = model.predict(input_seq, verbose=0)[0][0]
        future_scaled_preds.append(next_scaled)

        new_row = last_sequence[-1].copy()
        new_row[0] = next_scaled  # substitui 'close' previsto
        last_sequence = np.vstack([last_sequence[1:], new_row])

    future_scaled_preds = np.array(future_scaled_preds).reshape(-1, 1)
    future_preds = scaler_y.inverse_transform(future_scaled_preds)

    return model, scaler_X, scaler_y, future_preds

if __name__ == "__main__":
    import psycopg

    conn = psycopg.connect(
        dbname="tcc_b3",
        user="postgres",
        password="postgres",  # troque se necessário
        host="localhost",
        port="5432"
    )

    sequence_length = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    predict_days = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    query = """
        SELECT 
            ph.date,
            ph.close,
            ph.volume,
            MAX(CASE WHEN mi.name = 'SELIC' THEN mv.value END) AS selic,
            MAX(CASE WHEN mi.name = 'IPCA' THEN mv.value END) AS ipca,
            MAX(CASE WHEN mi.name = 'USD/BRL' THEN mv.value END) AS usd_brl,
            MAX(CASE WHEN mi.name = 'IBOV' THEN mv.value END) AS ibov
        FROM 
            companies c
        JOIN
            price_history ph ON c.id = ph.company_id
        JOIN
            macro_values mv ON mv.date = ph.date
        JOIN 
            macro_indicators mi ON mv.macro_indicator_id = mi.id
        WHERE 
            c.b3_code = 'PETR4.SA'
        GROUP BY
            ph.date, ph.close, ph.volume
        ORDER BY 
            ph.date ASC
    """

    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=columns)

    model, scaler_X, scaler_y, future_preds = train(df, sequence_length=sequence_length, predict_days=predict_days)

    print("Previsões para os próximos dias:")
    print(future_preds)
