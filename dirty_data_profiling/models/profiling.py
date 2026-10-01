from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from dirty_data_profiling.models.profile import DatasetProfile


@dataclass(slots=True)
class ProfilingResult:

    profiles: list[DatasetProfile]

    summary: pd.DataFrame

    test_results: pd.DataFrame

    dirty_records: pd.DataFrame
