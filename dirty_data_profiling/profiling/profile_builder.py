# dirty_data_profiling/profiling/profile_builder.py

"""
Builds a DatasetProfile from dbt validation results.

dbt is the single source of truth for data quality.

This module converts dbt test results into summary
statistics used by notebooks, dashboards and reports.
"""

from __future__ import annotations

import pandas as pd

from dirty_data_profiling.models import (
    DatasetProfile,
    DatasetStatistics,
    DBTValidationSummary,
)

# ==========================================================
# Helper
# ==========================================================


def _row_key(
    row: pd.Series,
    primary_key: list[str],
) -> tuple:
    return tuple(row[column] for column in primary_key)


# ==========================================================
# Statistics
# ==========================================================


def build_statistics(
    dataframe: pd.DataFrame,
    dbt_summary: DBTValidationSummary,
):

    total_rows = len(dataframe)

    primary_key = dbt_summary.primary_key

    affected_row_ids: set = set()

    failure_instances = 0

    for test in dbt_summary.tests:

        if not test.failed:
            continue

        failure_instances += test.failures or 0

        if test.failed_rows is None:
            continue

        if not all(column in test.failed_rows.columns for column in primary_key):
            continue

        affected_row_ids.update(
            test.failed_rows.apply(
                lambda row: _row_key(
                    row,
                    primary_key,
                ),
                axis=1,
            )
        )

    affected_rows = len(affected_row_ids)

    clean_rows = total_rows - affected_rows

    affected_row_rate = affected_rows / total_rows if total_rows else 0

    return DatasetStatistics(
        total_rows=total_rows,
        affected_rows=affected_rows,
        clean_rows=clean_rows,
        affected_row_rate=affected_row_rate,
        failure_instances=failure_instances,
    )


# ==========================================================
# Rule Summary
# ==========================================================


def build_rule_summary(
    dbt_summary: DBTValidationSummary,
):

    counter: dict[str, int] = {}

    for test in dbt_summary.tests:

        if not test.failed:
            continue

        counter.setdefault(
            test.rule,
            0,
        )

        counter[test.rule] += test.failures or 0

    return dict(counter)


# ==========================================================
# Category Summary
# ==========================================================


def build_category_summary(
    dbt_summary: DBTValidationSummary,
):

    counter: dict[str, int] = {}

    for test in dbt_summary.tests:

        if not test.failed:
            continue

        if test.metadata is None:
            continue

        counter.setdefault(
            test.metadata.category,
            0,
        )

        counter[test.metadata.category] += test.failures or 0

    return dict(counter)


# ==========================================================
# Severity Summary
# ==========================================================


def build_severity_summary(
    dbt_summary: DBTValidationSummary,
):

    counter: dict[str, int] = {}

    for test in dbt_summary.tests:

        if not test.failed:
            continue

        if test.metadata is None:
            continue

        counter.setdefault(
            test.metadata.severity,
            0,
        )

        counter[test.metadata.severity] += test.failures or 0

    return dict(counter)


# ==========================================================
# Column Summary
# ==========================================================


def build_column_summary(
    dbt_summary: DBTValidationSummary,
):

    counter: dict[str, int] = {}

    for test in dbt_summary.tests:

        if not test.failed:

            continue

        if test.column is None:

            continue

        counter.setdefault(
            test.column,
            0,
        )

        counter[test.column] += test.failures or 0

    return dict(counter)


# ==========================================================
# Dirty Examples
# ==========================================================


def build_dirty_examples(
    dbt_summary: DBTValidationSummary,
    max_rows: int = 20,
) -> pd.DataFrame:

    grouped = {}

    primary_key = dbt_summary.primary_key

    for test in dbt_summary.tests:

        if not test.failed:

            continue

        if test.failed_rows is None:

            continue

        if not all(column in test.failed_rows.columns for column in primary_key):
            continue

        for _, row in test.failed_rows.iterrows():

            pk = _row_key(
                row,
                primary_key,
            )

            if pk not in grouped:

                grouped[pk] = {
                    "record": row.to_dict(),
                    "failed_rules": [],
                    "categories": [],
                    "severity": [],
                }

            grouped[pk]["failed_rules"].append(test.rule)

            if test.metadata:

                grouped[pk]["categories"].append(test.metadata.category)

                grouped[pk]["severity"].append(test.metadata.severity)

    examples = []

    for _, info in grouped.items():

        record = info["record"].copy()

        record["failed_rules"] = ", ".join(sorted(set(info["failed_rules"])))
        record["failed_rule_count"] = len(set(info["failed_rules"]))
        record["categories"] = ", ".join(sorted(set(info["categories"])))
        record["severity"] = ", ".join(sorted(set(info["severity"])))

        examples.append(record)

    print(f"Dirty example groups: {len(grouped)}")
    print(f"Dirty example rows: {len(examples)}")

    if not examples:
        return pd.DataFrame()

    return (
        pd.DataFrame(examples)
        .sort_values("failed_rule_count", ascending=False)
        .head(max_rows)
        .reset_index(drop=True)
    )


# ==========================================================
# Build Test Summary
# ==========================================================


def build_test_summary(
    dbt_summary: DBTValidationSummary,
):

    rows = []

    for test in dbt_summary.tests:

        rows.append(
            {
                "column": test.column if test.column is not None else "row-level",
                "rule": test.rule,
                "category": (test.metadata.category if test.metadata else "Unknown"),
                "severity": (test.metadata.severity if test.metadata else "Unknown"),
                "status": test.status,
                "failures": test.failures,
            }
        )

    return pd.DataFrame(rows)


# ==========================================================
# Main Builder
# ==========================================================


def build_profile(
    *,
    dataset: str,
    dataframe: pd.DataFrame,
    dbt_summary: DBTValidationSummary,
):

    profile = DatasetProfile(
        dataset=dataset,
        dataframe=dataframe,
        dbt_summary=dbt_summary,
        statistics=build_statistics(
            dataframe,
            dbt_summary,
        ),
        severity_summary=build_severity_summary(
            dbt_summary,
        ),
        category_summary=build_category_summary(
            dbt_summary,
        ),
        column_summary=build_column_summary(
            dbt_summary,
        ),
        rule_summary=build_rule_summary(
            dbt_summary,
        ),
        dirty_examples=build_dirty_examples(
            dbt_summary,
        ),
        test_summary=build_test_summary(
            dbt_summary,
        ),
    )

    return profile
