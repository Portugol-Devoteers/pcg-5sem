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

# Fixar aleatoriedade
SEED = 42

def train(df: pd.DataFrame, sequence_length: int = 60):
    # Fixar seed novamente aqui
    import random
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)
    feature_cols = ['close', 'volume', 'selic', 'ipca', 'usd_brl', 'ibov']
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
    return model, scaler_X, scaler_y
