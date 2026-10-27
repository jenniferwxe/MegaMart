# dirty_data_profiling/profiling/numeric_profiler.py

"""
Computes descriptive statistics for every numeric column.
"""

from __future__ import annotations

import pandas as pd


def profile_numeric_columns(
    df: pd.DataFrame,
) -> dict[str, dict]:

    numeric_df = df.select_dtypes(include="number")

    profile = {}

    for column in numeric_df.columns:

        series = numeric_df[column]

        profile[column] = {
            "count": int(series.count()),
            "missing": int(series.isna().sum()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "q1": float(series.quantile(0.25)),
            "q3": float(series.quantile(0.75)),
        }

    return profile
