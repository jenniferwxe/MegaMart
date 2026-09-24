# dirty_data_profiling/models/insights.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DatasetInsights:

    #
    # Overall quality
    #

    quality_grade: str

    health_score: float

    recommendation: str

    #
    # Biggest problems
    #

    most_affected_column: str | None

    most_failed_rule: str | None

    most_common_category: str | None

    #
    # Cleaning priorities
    #

    recommended_dbt_models: list[str] = field(default_factory=list)

    #
    # Executive summary
    #

    summary: str = ""
