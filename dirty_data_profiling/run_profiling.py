# dirty_data_profiling/run_profiling.py

from __future__ import annotations

import traceback
from pathlib import Path

import pandas as pd

from dirty_data_profiling.bigquery.table_loader import (
    BigQueryTableLoader,
)
from dirty_data_profiling.dbt.artifact_loader import DBTArtifactLoader
from dirty_data_profiling.dbt.failure_loader import (
    FailureLoader,
)
from dirty_data_profiling.dbt.runner import DBTRunner
from dirty_data_profiling.models import ProfilingResult
from dirty_data_profiling.profiling.dashboard_builder import (
    build_dashboard,
)
from dirty_data_profiling.profiling.exporter import (
    export_profiling_result,
)
from dirty_data_profiling.profiling.insights_builder import (
    build_insights,
)
from dirty_data_profiling.profiling.profile_builder import (
    build_profile,
)

# ==========================================================
# Helpers
# ==========================================================


def build_summary(profile):

    stats = profile.statistics

    return {
        "dataset": profile.dataset,
        "rows": stats.total_rows,
        "affected_rows": stats.affected_rows,
        "clean_rows": stats.clean_rows,
        "affected_row_rate": round(stats.affected_row_rate * 100, 2),
        "failure_instances": stats.failure_instances,
        "most_affected_column": profile.insights.most_affected_column,
        "most_failed_rule": profile.insights.most_failed_rule,
        "most_common_category": profile.insights.most_common_category,
    }


def print_dataset_summary(summary: pd.DataFrame):
    display_summary = summary.copy()

    display_summary["affected_row_rate"] = display_summary["affected_row_rate"].map(
        lambda x: f"{x:.2f}%"
    )

    print(
        display_summary.to_string(
            index=False,
            justify="left",
        )
    )


# ==========================================================
# Runner
# ==========================================================


def run_profiling(
    source_dataset: str,
    dbt_target: str,
    dataset: str | None = None,
    dbt_select: str | None = None,
    output_dir: str | Path | None = None,
):

    print("=" * 70)
    print("Running dbt Validation")
    print("=" * 70)

    run_result, _test_result = DBTRunner().run_test(
        target=dbt_target,
        select=dbt_select or dataset,
    )

    #
    # dbt run execution gate
    #

    if run_result.returncode != 0:

        print()
        print("=" * 70)
        print("dbt run failed")
        print("Profiling aborted.")
        print("=" * 70)

        return [], pd.DataFrame()

    #
    # Load dbt artifacts
    #

    artifact_loader = DBTArtifactLoader()

    dbt_summaries = artifact_loader.load_results()

    if dataset is not None:

        dbt_summaries = [
            summary for summary in dbt_summaries if summary.dataset == dataset
        ]

    #
    # dbt test execution / validation gate
    #

    errored_tests = [
        test for summary in dbt_summaries for test in summary.tests if test.errored
    ]

    if errored_tests:

        print()
        print("=" * 70)
        print("dbt test errors detected")
        print("Profiling aborted.")
        print("=" * 70)

        for test in errored_tests:

            print(f"- {test.model} | " f"{test.rule} | " f"status: {test.status}")

            if test.message:
                print(f"  message: {test.message}")

        return [], pd.DataFrame()

    #
    # Profiling
    #

    profiles = []

    print("=" * 70)
    print("MegaMart Dirty Data Profiler")
    print("=" * 70)

    failure_loader = FailureLoader()

    table_loader = BigQueryTableLoader()

    for dbt_summary in dbt_summaries:

        dataset_name = dbt_summary.dataset

        try:

            dataframe = table_loader.load(
                source_dataset,
                dataset_name,
            )

        except Exception:

            traceback.print_exc()

            continue

        for test in dbt_summary.tests:

            if not test.failed:

                continue

            print(
                "TEST:",
                test.test_type,
                "| rule:",
                test.rule,
                "| status:",
                test.status,
                "| failures:",
                test.failures,
                "| failure_table:",
                test.failure_table,
            )

            if test.failure_table is None:

                continue

            try:

                test.failed_rows = failure_loader.load(
                    test.failure_table,
                )

            except Exception:

                test.failed_rows = None

        profile = build_profile(
            dataset=dataset_name,
            dataframe=dataframe,
            dbt_summary=dbt_summary,
        )

        profile.insights = build_insights(profile)

        profile.dashboard = build_dashboard(
            profile,
        )

        profiles.append(profile)

    #
    # Overall Summary
    #

    summary = pd.DataFrame(build_summary(p) for p in profiles)

    if summary.empty:

        print()
        print("No datasets were profiled")

        return profiles, summary

    total_tests = sum(s.total_tests for s in dbt_summaries)

    passed = sum(s.passed for s in dbt_summaries)

    failed = sum(s.failed for s in dbt_summaries)

    errored = sum(s.errored for s in dbt_summaries)

    success_rate = (
        round(
            passed / total_tests * 100,
            2,
        )
        if total_tests
        else 0
    )

    print(f"Total Tests   : {total_tests}")

    print(f"Passed        : {passed}")

    print(f"Failed        : {failed}")

    print(f"Errored       : {errored}")

    print(f"Success Rate  : {success_rate}%")

    result = ProfilingResult(
        profiles=profiles,
        summary=summary,
        test_results=pd.DataFrame(),
        dirty_records=pd.DataFrame(),
    )

    if output_dir is not None:

        result = export_profiling_result(
            result,
            output_dir,
        )

    return result


if __name__ == "__main__":

    result = run_profiling(
        source_dataset="synthetic_dirty",
        dbt_target="dirty",
        # dataset="bundle_items",
        output_dir=Path("reports/profiling"),
    )

    print("\n" + "=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)

    print_dataset_summary(result.summary)
