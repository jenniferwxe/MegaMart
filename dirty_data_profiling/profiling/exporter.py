from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dirty_data_profiling.models import ProfilingResult

# ==========================================================
# Helper
# ==========================================================


def _format_primary_key(
    record: dict,
    primary_key: list[str],
) -> str:

    return "|".join(str(record.get(column)) for column in primary_key)


# ==========================================================
# Results Exporter
# ==========================================================


def build_test_results(
    result: ProfilingResult,
) -> pd.DataFrame:

    rows = []

    for profile in result.profiles:

        for test in profile.dbt_summary.tests:

            rows.append(
                {
                    "dataset": profile.dataset,
                    "column": (test.column if test.column is not None else "row-level"),
                    "test_type": test.test_type,
                    "rule": test.rule,
                    "category": (
                        test.metadata.category if test.metadata else "Unknown"
                    ),
                    "severity": (
                        test.metadata.severity if test.metadata else "Unknown"
                    ),
                    "status": test.status,
                    "failures": test.failures or 0,
                    "execution_time": test.execution_time,
                }
            )

    return pd.DataFrame(rows)


def build_dirty_records(
    result: ProfilingResult,
) -> pd.DataFrame:

    rows = []

    for profile in result.profiles:

        primary_key = profile.dbt_summary.primary_key

        for test in profile.dbt_summary.tests:

            if not test.failed:
                continue

            if test.failed_rows is None:
                continue

            for _, record in test.failed_rows.iterrows():

                record_dict = record.to_dict()

                rows.append(
                    {
                        "dataset": profile.dataset,
                        "primary_key": _format_primary_key(
                            record_dict,
                            primary_key,
                        ),
                        "test_type": test.test_type,
                        "rule": test.rule,
                        "column": (
                            test.column if test.column is not None else "row-level"
                        ),
                        "category": (
                            test.metadata.category if test.metadata else "Unknown"
                        ),
                        "severity": (
                            test.metadata.severity if test.metadata else "Unknown"
                        ),
                        "record": json.dumps(
                            record_dict,
                            default=str,
                        ),
                    }
                )

    return pd.DataFrame(rows)


def export_profiling_result(
    result: ProfilingResult,
    output_dir: str | Path,
) -> ProfilingResult:

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.test_results = build_test_results(result)
    result.dirty_records = build_dirty_records(result)

    result.summary.to_csv(
        output_dir / "summary.csv",
        index=False,
    )

    result.test_results.to_csv(
        output_dir / "test_results.csv",
        index=False,
    )

    result.dirty_records.to_csv(
        output_dir / "dirty_records.csv",
        index=False,
    )

    return result
