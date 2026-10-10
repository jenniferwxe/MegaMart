# dirty_data_profiling/profiling/insights_builder.py

"""
Builds executive-level insights from a DatasetProfile.

This layer converts profiling statistics into
human-readable recommendations for notebooks,
HTML reports and dashboards.
"""

from __future__ import annotations

from dirty_data_profiling.models.insights import DatasetInsights
from dirty_data_profiling.models.profile import DatasetProfile

# ==========================================================
# "Most" Tabulation Helpers
# ==========================================================


def most_affected_column(
    profile: DatasetProfile,
):

    counter: dict[str, int] = {}

    for test in profile.dbt_summary.tests:

        if not test.failed:

            continue

        if test.column is None:

            continue

        counter.setdefault(
            test.column,
            0,
        )

        counter[test.column] += test.failures or 0

    if not counter:

        return None

    return max(
        counter,
        key=lambda key: counter[key],
    )


def most_failed_rule(
    profile: DatasetProfile,
):

    counter: dict[str, int] = {}

    for test in profile.dbt_summary.tests:

        if not test.failed:

            continue

        counter.setdefault(
            test.rule,
            0,
        )

        counter[test.rule] += test.failures or 0

    if not counter:

        return None

    return max(
        counter,
        key=lambda key: counter[key],
    )


def most_common_category(
    profile: DatasetProfile,
):

    counter: dict[str, int] = {}

    for test in profile.dbt_summary.tests:

        if not test.failed:

            continue

        if test.metadata is None:

            continue

        category = test.metadata.category

        counter.setdefault(
            category,
            0,
        )

        counter[category] += test.failures or 0

    if not counter:

        return None

    return max(
        counter,
        key=lambda key: counter[key],
    )


# ==========================================================
# Recommended dbt Cleaning Functions
# ==========================================================


def recommended_models(
    profile: DatasetProfile,
):

    recommendations = set()

    for test in profile.dbt_summary.tests:

        if not test.failed:
            continue

        if test.metadata and test.metadata.dbt_recommendation:

            recommendations.add(test.metadata.dbt_recommendation)

    return sorted(recommendations)


# ==========================================================
# Executive Summary
# ==========================================================


def generate_summary(
    profile: DatasetProfile,
):

    stats = profile.statistics

    failed_tests = profile.dbt_summary.failed

    return (
        f"{stats.affected_rows:,} records "
        f"failed one or more dbt validation rules "
        f"({stats.affected_row_rate:.1%} of the dataset). "
        f"{stats.failure_instances:,} total failure instances "
        f"were identified across {failed_tests} failed validation tests. "
        f"The most affected column was "
        f"{most_affected_column(profile) or 'None'}, "
        f"with "
        f"{most_common_category(profile) or 'None'} "
        f"as the most common issue category."
    )


# ==========================================================
# Builder
# ==========================================================


def build_insights(
    profile: DatasetProfile,
) -> DatasetInsights:

    return DatasetInsights(
        most_affected_column=most_affected_column(profile),
        most_failed_rule=most_failed_rule(profile),
        most_common_category=most_common_category(profile),
        recommended_dbt_models=recommended_models(profile),
        summary=generate_summary(profile),
    )
