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
import re
from datetime import datetime, timedelta

# Fixar aleatoriedade
SEED = 42

def train(df: pd.DataFrame, sequence_length: int = 60, predict_days: int = 1):
    import random
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)

    pattern_concorrente = re.compile(r"^\\d+_.*")
    pattern_macro = re.compile(r"^(macro_|acct_)")

    target_cols = [col for col in df.columns if col not in ['date'] and not pattern_concorrente.match(col) and not pattern_macro.match(col)]
    exog_cols = [col for col in df.columns if col not in ['date'] and col not in target_cols]

    df[target_cols + exog_cols] = df[target_cols + exog_cols].astype(float)
    df.dropna(inplace=True)

    feature_cols = target_cols + exog_cols
    target_col = 'close' if 'close' in df.columns else target_cols[0]

    X_data = df[feature_cols].values
    y_data = df[[target_col]].values

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

    last_sequence = X_scaled[-sequence_length:].copy()
    future_scaled_preds = []
    future_dates = []

    last_date = pd.to_datetime(df['date'].iloc[-1], unit='ms') if isinstance(df['date'].iloc[-1], (int, float)) else pd.to_datetime(df['date'].iloc[-1])

    for i in range(predict_days):
        input_seq = last_sequence.reshape(1, sequence_length, len(feature_cols))
        next_scaled = model.predict(input_seq, verbose=0)[0][0]
        future_scaled_preds.append(next_scaled)

        new_row = last_sequence[-1].copy()
        new_row[feature_cols.index(target_col)] = next_scaled
        last_sequence = np.vstack([last_sequence[1:], new_row])

        future_dates.append(last_date + timedelta(days=i + 1))

    future_scaled_preds = np.array(future_scaled_preds).reshape(-1, 1)
    future_preds = scaler_y.inverse_transform(future_scaled_preds)

    result_df = pd.DataFrame({
        'date': future_dates,
        'value': future_preds.flatten()
    })

    return model, scaler_X, scaler_y, result_df

if __name__ == "__main__":
    sequence_length = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    predict_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7

    company_id = sys.argv[1]
    model_id = 1  
    filename = f"../../data_prediction/get_data/features/{company_id}_dataset.parquet"
    df = pd.read_parquet(filename)

    model, scaler_X, scaler_y, future_df = train(df, sequence_length=sequence_length, predict_days=predict_days)

    output_path = f"../../data_prediction/predictions_temp/{company_id}_{model_id}.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    future_df.to_parquet(output_path, index=False)

    print("Previsões para os próximos dias:")
    print(future_df)
