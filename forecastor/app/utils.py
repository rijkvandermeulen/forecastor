import csv
import io
from typing import Dict

import pandas as pd


def check_delimiter(file_object: io.StringIO):

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
    print("DEBUG")
    print(df.head(30))

    return df


def get_forecast_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate forecast accuracy metrics.
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


def validate_input(df: pd.DataFrame, time_lag: int) -> dict:
    """
    Perform input validation for the uploaded file.
    """
    return {
        "is_valid": False,
        "error_message": "The uploaded file doesn't match the expected format. Please check your CSV file and try again.",
        "error_details": "Detailed error information: Column 'Date' is missing in the CSV file."
    }

    # if "date" not in df.columns:
    #     raise ValueError("The file must contain a 'date' column.")
    # if "sku" not in df.columns:
    #     raise ValueError("The file must contain a 'sku' column.")
    # if "sales" not in df.columns:
    #     raise ValueError("The file must contain a 'sales' column.")
    # if "statistical_forecast" not in df.columns:
    #     raise ValueError("The file must contain a 'statistical_forecast' column.")
    # if "final_forecast" not in df.columns:
    #     raise ValueError("The file must contain a 'final_forecast' column.")
    #
    # if time_lag < 1:
    #     raise ValueError("The time lag must be greater than or equal to 1.")
