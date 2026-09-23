# dirty_data_profiling/models/dashboard.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DashboardMetrics:

    #
    # Overall
    #

    total_rows: int

    clean_rows: int

    dirty_rows: int

    health_score: float

    success_rate: float

    #
    # dbt

    total_tests: int

    passed_tests: int

    failed_tests: int

    errored_tests: int

    #
    # Top Issues

    most_affected_column: str | None

    most_failed_rule: str | None

    most_common_category: str | None

    #
    # Charts

    category_summary: dict

    severity_summary: dict

    column_summary: dict

    rule_summary: dict
