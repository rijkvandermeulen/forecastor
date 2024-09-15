import csv
import io
from typing import Dict

import pandas as pd


def check_delimiter(file_object: io.StringIO):
    """
    Check the delimiter of the uploaded CSV file.
    """

    file_object.seek(0)
    sample = file_object.read(4096)
    if not sample:
        raise ValueError("The file appears to be empty.")
    file_object.seek(0)

    try:
        # Attempt to detect the dialect and delimiter
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except csv.Error:
        raise ValueError("Could not detect the delimiter.")


def moving_average_benchmark(df: pd.DataFrame, time_lag: int, window: int = 3):
    """
    Calculate the moving average benchmark forecast for each demand_forecasting_unit.
    """
    df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d')
    df = df.sort_values(["sku", "date"], ascending=True)
    df["benchmark_forecast"] = (
        df
        .groupby("sku")["sales"]
        .transform(lambda x: x.shift(time_lag).rolling(window=window, min_periods=1).mean())
    )

    return df


def get_forecast_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate forecast accuracy metrics (MAE%-based).
    """
    # Calculate forecast accuracy of the various forecast versions
    mae_perc_stat_fcst = min(1, (df["absolute_error_stat_fcst"].sum() / df["sales"].sum()))
    fa_stat_fcst = (1 - mae_perc_stat_fcst) * 100
    mae_perc_fin_fcst = min(1, (df["absolute_error_fin_fcst"].sum() / df["sales"].sum()))
    fa_fin_fcst = (1 - mae_perc_fin_fcst) * 100
    mae_perc_bm_fcst = min(1, (df["absolute_error_bm_fcst"].sum() / df["sales"].sum()))
    fa_bm_fcst = (1 - mae_perc_bm_fcst) * 100

    # Deltas
    fva_fin_stat = fa_fin_fcst - fa_stat_fcst
    fva_bm_stat = fa_stat_fcst - fa_bm_fcst

    return {
        "fa_stat_fcst": fa_stat_fcst,
        "fa_fin_fcst": fa_fin_fcst,
        "fa_bm_fcst": fa_bm_fcst,
        "fva_fin_stat": fva_fin_stat,
        "fva_bm_stat": fva_bm_stat
    }


def validate_input(df: pd.DataFrame) -> dict:
    """
    Perform input validation for the uploaded file.
    """
    error_message = ""

    # Check if columns are present
    expected_columns = ["date", "sku", "sales", "statistical_forecast", "final_forecast"]
    for column in expected_columns:
        if column not in df.columns:
            error_message += f"The file must contain a '{column}' column. \n"

    # Check that sku-date key is unique
    if df.duplicated(subset=["date", "sku"]).any():
        error_message += "The 'sku' and 'date' columns must form a unique key. \n"

    # Check that the date column can be parsed as a date
    if "date" in df.columns:
        try:
            pd.to_datetime(df["date"])
            input_time_series = pd.DatetimeIndex(df["date"]).unique().sort_values()
            start = input_time_series.min()
            end = input_time_series.max()
            frequency_time_series = pd.date_range(start=start, end=end, freq="MS")
            if not input_time_series.equals(frequency_time_series):
                error_message += (
                    "The 'date' column must contain a continuous time series with monthly frequency ('YYYY-MM-DD'). \n"
                )
        except ValueError:
            error_message += "The 'date' column must be in the format 'YYYY-MM-DD'. \n"

    # Check that the sales, statistical_forecast, and final_forecast columns are numeric and non-negative
    for column in ["sales", "statistical_forecast", "final_forecast"]:
        if column not in df.columns:
            pass
        else:
            if not pd.api.types.is_numeric_dtype(df[column]):
                error_message += f"The '{column}' column must contain numeric values. \n"
            else:
                if (df[column] < 0).any():
                    error_message += f"The '{column}' column must contain non-negative values. \n"

    # Check that the sku and date columns are not empty
    for column in ["sku", "date"]:
        if df[column].isnull().any():
            error_message += f"The '{column}' column must not contain missing values. \n"

    # Check on data size (considering small deployment server)
    unique_skus = df["sku"].nunique()
    if unique_skus > 200:
        error_message += f"Your file contains {unique_skus} unique SKUs. The current limit is 200. \n"
    rows = df.shape[0]
    if rows > 10000:
        error_message += f"Your file contains {rows} rows. The current limit is 10,000. \n"

    if error_message:
        return {
            "is_valid": False,
            "error_message": "The file is not valid. Please correct the following issues:",
            "error_details": error_message
        }
    else:
        return {"is_valid": True}
