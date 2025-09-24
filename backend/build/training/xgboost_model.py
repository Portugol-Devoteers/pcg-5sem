import os
from xml.parsers.expat import model
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import numpy as np
import pandas as pd
import xgboost as xgb  # type: ignore
from sklearn.preprocessing import MinMaxScaler
import sys
import re
from datetime import timedelta

# Fixar aleatoriedade
SEED = 42

def train(df: pd.DataFrame, sequence_length: int = 60, predict_days: int = 1):
    import random
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.feature_selection import mutual_info_regression

    random.seed(SEED)
    np.random.seed(SEED)

    # filtros de colunas
    pattern_concorrente = re.compile(r"^\d+_.*")
    pattern_macro = re.compile(r"^(macro_|acct_)")

    target_cols = [col for col in df.columns
                   if col not in ['date', 'open', 'high', 'low', 'volume']
                   and not pattern_concorrente.match(col)
                   and not pattern_macro.match(col)]
    exog_cols = [col for col in df.columns if col not in ['date'] and col not in target_cols]

    # tipos numéricos + limpeza
    df[target_cols + exog_cols] = df[target_cols + exog_cols].astype(float)
    df.dropna(inplace=True)

    feature_cols = target_cols + exog_cols
    target_col = 'close' if 'close' in df.columns else target_cols[0]

    X_data = df[feature_cols].values
    y_data = df[[target_col]].values

    # escala
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    X_scaled = scaler_X.fit_transform(X_data)
    y_scaled = scaler_y.fit_transform(y_data)

    # janelas deslizantes -> flatten p/ árvore
    X, y = [], []
    for i in range(sequence_length, len(X_scaled)):
        X.append(X_scaled[i - sequence_length:i].flatten())
        y.append(y_scaled[i, 0])
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    # modelo XGBoost (GPU) — hiperparâmetros fixos
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=300,
        max_depth=5,
        learning_rate=0.1,
        reg_lambda=1.0,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method='hist',   
        device='cuda',        # força GPU
        random_state=SEED,
        n_jobs=-1,
        verbosity=0,
    )
    model.set_params(eval_metric='rmse')
    model.fit(X, y, eval_set=[(X, y)], verbose=False)
    evals = model.evals_result()
    train_log = evals.get('validation_0', evals.get('train', {})).get('rmse', [])

    # IMPORTÂNCIA DE FEATURES (agregada por variável original)
    n_base = len(feature_cols)
    raw_importances = getattr(model, "feature_importances_", None)
    agg = np.zeros(n_base, dtype=np.float64)
    if raw_importances is not None and raw_importances.size == X.shape[1]:
        raw_importances = raw_importances.astype(float)
        for j in range(raw_importances.size):
            base_idx = j % n_base
            agg[base_idx] += raw_importances[j]
    else:
        booster_scores = model.get_booster().get_score(importance_type='gain')
        for k, v in booster_scores.items():
            try:
                flat_idx = int(k[1:])  # 'f123' -> 123
                base_idx = flat_idx % n_base
                agg[base_idx] += float(v)
            except Exception:
                continue
    feat_importance_df = pd.DataFrame(
        {"feature": feature_cols, "gain": agg}
    ).sort_values("gain", ascending=False)


    yhat_scaled = model.predict(X).astype(np.float32).reshape(-1, 1)
    ytrue_scaled = y.reshape(-1, 1)

    yhat = scaler_y.inverse_transform(yhat_scaled).flatten()
    ytrue = scaler_y.inverse_transform(ytrue_scaled).flatten()

    rmse = float(np.sqrt(mean_squared_error(ytrue, yhat)))
    mae  = float(mean_absolute_error(ytrue, yhat))

    eps = 1e-8
    mape = float(np.mean(np.abs((ytrue - yhat) / (np.abs(ytrue) + eps))) * 100.0)
    r2   = float(r2_score(ytrue, yhat))
    metrics = {"RMSE": rmse, "MAE": mae, "MAPE": mape, "R2": r2}

    train_dates = pd.to_datetime(df['date'].iloc[sequence_length:])  # alinhado com y / X
    recent_n = int(min(200, len(ytrue))) if len(ytrue) > 0 else 0
    if recent_n > 0:
        recent_train_df = pd.DataFrame({
            "date": train_dates.iloc[-recent_n:].values,
            "real": ytrue[-recent_n:],
            "previsto": yhat[-recent_n:]
        })
    else:
        recent_train_df = pd.DataFrame(columns=["date", "real", "previsto"])

    corr_cols = feature_cols + [target_col]
    corr_df = df[corr_cols].corr(method='pearson')

    try:
        mi_vals = mutual_info_regression(df[feature_cols].values, df[target_col].values, random_state=SEED)
        mi_df = pd.DataFrame({"feature": feature_cols, "mi": mi_vals}).sort_values("mi", ascending=False)
    except Exception:
        mi_df = pd.DataFrame({"feature": feature_cols, "mi": []})

    last_sequence = X_scaled[-sequence_length:].copy()
    future_scaled_preds, future_dates = [], []
    last_date = pd.to_datetime(df['date'].iloc[-1], unit='ms') \
        if isinstance(df['date'].iloc[-1], (int, float)) else pd.to_datetime(df['date'].iloc[-1])

    for i in range(predict_days):
        input_seq = last_sequence.flatten().reshape(1, -1)
        next_scaled = float(model.predict(input_seq)[0])
        future_scaled_preds.append(next_scaled)
        new_row = last_sequence[-1].copy()
        new_row[feature_cols.index(target_col)] = next_scaled
        last_sequence = np.vstack([last_sequence[1:], new_row])
        future_dates.append(last_date + timedelta(days=i + 1))

    future_scaled_preds = np.array(future_scaled_preds, dtype=np.float32).reshape(-1, 1)
    future_preds = scaler_y.inverse_transform(future_scaled_preds)
    result_df = pd.DataFrame({'date': future_dates, 'value': future_preds.flatten()})

    return (
        model,
        scaler_X,
        scaler_y,
        result_df,
        train_log,
        feat_importance_df,
        metrics,
        recent_train_df,
        corr_df,
        mi_df,
    )


if __name__ == "__main__":
    sequence_length = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    predict_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7

    company_id = sys.argv[1]
    model_id = 3  # XGBoost
    filename = f"../../data_prediction/get_data/features/{company_id}_dataset.parquet"
    df = pd.read_parquet(filename)

    model, scaler_X, scaler_y, future_df = train(df, sequence_length=sequence_length, predict_days=predict_days)

    output_path = f"../../data_prediction/predictions_temp/{company_id}_{model_id}.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    future_df.to_parquet(output_path, index=False)

    print("Previsões para os próximos dias:")
    print(future_df)
