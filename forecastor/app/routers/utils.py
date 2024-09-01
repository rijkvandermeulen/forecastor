import csv
import io

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
    df = df.sort_values(["demand_forecasting_unit", "date"], ascending=True)
    df["benchmark_forecast"] = (
        df
        .groupby("demand_forecasting_unit")["sales"]
        .transform(lambda x: x.shift(time_lag).rolling(window=window, min_periods=1).mean())
    )
    print("DEBUG")
    print(df.head(30))

    return df
