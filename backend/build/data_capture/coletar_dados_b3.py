import yfinance as yf
import pandas as pd
import os

def strip_tz(obj):
    if isinstance(obj, pd.Series):
        if isinstance(obj.index, pd.DatetimeIndex) and obj.index.tz is not None:
            obj.index = obj.index.tz_localize(None)
        return obj

    if isinstance(obj.index, pd.DatetimeIndex) and obj.index.tz is not None:
        obj.index = obj.index.tz_localize(None)

    for c in obj.select_dtypes(include=["datetimetz"]).columns:
        obj[c] = obj[c].dt.tz_localize(None)
    return obj

def export_company_data_to_files(ticker: str):
    print(f"📦 Coletando dados do ticker: {ticker}")
    tck = ticker.upper()
    ticker_obj = yf.Ticker(tck)

    historical_data = strip_tz(ticker_obj.history(period="max", interval="1d"))

    historical_data.columns = [c.lower() for c in historical_data.columns]

    income_stmt     = strip_tz(ticker_obj.financials.copy())
    balance         = strip_tz(ticker_obj.balance_sheet.copy())
    cashflow        = strip_tz(ticker_obj.cashflow.copy())

    num_cols = historical_data.select_dtypes(include="number")
    stats = pd.DataFrame(index=num_cols.columns)
    stats["count"]  = num_cols.count()
    stats["mean"]   = num_cols.mean()
    stats["median"] = num_cols.median()
    stats["mode"]   = num_cols.mode().iloc[0] if not num_cols.mode().empty else pd.NA
    stats["std"]    = num_cols.std()
    stats["min"]    = num_cols.min()
    stats["25%"]    = num_cols.quantile(0.25)
    stats["75%"]    = num_cols.quantile(0.75)
    stats["max"]    = num_cols.max()
    stats["IQR"]    = stats["75%"] - stats["25%"]
    stats = stats[["count", "mean", "median", "mode", "std", "min", "25%", "75%", "IQR", "max"]]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    parquet_base = os.path.join(base_dir, "parquets")
    #excel_dir = os.path.join(base_dir, "excels")
    #os.makedirs(excel_dir, exist_ok=True)

    subfolders = ["historical", "descriptive", "DRE", "balance", "cashflow"]
    for sub in subfolders:
        os.makedirs(os.path.join(parquet_base, sub), exist_ok=True)

    safe_name = tck.replace(".", "_").replace("/", "_")
    #excel_file = os.path.join(excel_dir, f"{safe_name}_dados.xlsx")
    parquet_files = {
        "historical": os.path.join(parquet_base, "historical", f"{safe_name}_historical.parquet"),
        "descriptive": os.path.join(parquet_base, "descriptive", f"{safe_name}_descriptive.parquet"),
        "DRE": os.path.join(parquet_base, "DRE", f"{safe_name}_dre.parquet"),
        "balance": os.path.join(parquet_base, "balance", f"{safe_name}_balanco.parquet"),
        "cashflow": os.path.join(parquet_base, "cashflow", f"{safe_name}_fluxo_caixa.parquet")
    }

    # with pd.ExcelWriter(excel_file, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
    #     historical_data.to_excel(writer, sheet_name="Historico")
    #     stats.to_excel(writer,          sheet_name="Descritivas")
    #     income_stmt.to_excel(writer,    sheet_name="DRE")
    #     balance.to_excel(writer,        sheet_name="Balanco")
    #     cashflow.to_excel(writer,       sheet_name="FluxoCaixa")
    #     pd.DataFrame({
    #         "Sheet": ["Historico", "DRE", "Balanco", "FluxoCaixa"],
    #         "Units": ["Preço em BRL; Volume = nº de ações",
    #                   "Valores em BRL", "Valores em BRL", "Valores em BRL"]
    #     }).to_excel(writer, sheet_name="Unidades", index=False)

    historical_data.to_parquet(parquet_files["historical"], index=True)
    stats.to_parquet(parquet_files["descriptive"], index=True)
    income_stmt.to_parquet(parquet_files["DRE"], index=True)
    balance.to_parquet(parquet_files["balance"], index=True)
    cashflow.to_parquet(parquet_files["cashflow"], index=True)

    # print(f"✅ Excel salvo em: {excel_file}")
    print("📂 Parquets salvos em:")
    for key, path in parquet_files.items():
        print(f"   - {path}")

    # return {
    #     "excel": excel_file,
    #     **parquet_files
    # }

if __name__ == "__main__":
    export_company_data_to_files()
