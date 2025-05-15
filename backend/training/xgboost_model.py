import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor


# Fixar aleatoriedade
SEED = 42


def train(df: pd.DataFrame, sequence_length: int = 60):
    import random
    random.seed(SEED)
    np.random.seed(SEED)

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
        # Flatten as features for XGBoost
        X.append(X_scaled[i - sequence_length:i].flatten())
        y.append(y_scaled[i, 0])

    X, y = np.array(X), np.array(y)

    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    model.fit(X, y)

    return model, scaler_X, scaler_y
