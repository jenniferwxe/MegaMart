# dirty_data_profiling/models/profile.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dirty_data_profiling.models.dashboard import DashboardMetrics
from dirty_data_profiling.models.dbt import DBTValidationSummary
from dirty_data_profiling.models.insights import DatasetInsights


@dataclass(slots=True)
class DatasetStatistics:

    total_rows: int

    clean_rows: int

    dirty_rows: int

    dirty_ratio: float

    health_score: float


@dataclass(slots=True)
class DatasetProfile:

    #
    # Dataset
    #

    dataset: str

    dataframe: Any

    dbt_summary: DBTValidationSummary
    statistics: DatasetStatistics

    #
    # Analytics
    #

    issue_summary: dict = field(default_factory=dict)

    severity_summary: dict = field(default_factory=dict)

    category_summary: dict = field(default_factory=dict)

    column_summary: dict = field(default_factory=dict)

    rule_summary: dict = field(default_factory=dict)

    #
    # Notebook
    #

    dirty_examples: Any = None

    failed_rows: Any = None

    #
    # Insights
    #

    insights: DatasetInsights | None = None

    test_summary: Any = None

    dashboard: DashboardMetrics | None = None
