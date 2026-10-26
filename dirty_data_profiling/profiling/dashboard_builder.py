# dirty_data_profiling/profiling/dashboard_builder.py

from __future__ import annotations

from dirty_data_profiling.models import (
    DashboardMetrics,
    DatasetProfile,
)


def build_dashboard(
    profile: DatasetProfile,
):

    return DashboardMetrics(
        total_rows=profile.statistics.total_rows,
        affected_rows=profile.statistics.affected_rows,
        clean_rows=profile.statistics.clean_rows,
        affected_row_rate=profile.statistics.affected_row_rate,
        failure_instances=profile.statistics.failure_instances,
        success_rate=profile.dbt_summary.success_rate,
        total_tests=profile.dbt_summary.total_tests,
        passed_tests=profile.dbt_summary.passed,
        failed_tests=profile.dbt_summary.failed,
        errored_tests=profile.dbt_summary.errored,
        most_affected_column=(
            profile.insights.most_affected_column
            if profile.insights is not None
            else None
        ),
        most_failed_rule=(
            profile.insights.most_failed_rule if profile.insights is not None else None
        ),
        most_common_category=(
            profile.insights.most_common_category
            if profile.insights is not None
            else None
        ),
        category_summary=profile.category_summary,
        severity_summary=profile.severity_summary,
        column_summary=profile.column_summary,
        rule_summary=profile.rule_summary,
    )
