# dirty_data_profiling/models/dbt.py

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from dirty_data_profiling.metadata.metadata import (
    RuleMetadata,
)

# ==========================================================
# One dbt Test
# ==========================================================


@dataclass(slots=True)
class DBTTestResult:

    #
    # Identity
    #

    unique_id: str

    model: str

    column: str | None

    test_name: str

    #
    # Execution
    #

    status: str

    execution_time: float

    failures: int | None = None

    message: str | None = None

    #
    # SQL
    #

    compiled_sql: str | None = None

    relation_name: str | None = None

    #
    # Failure Table
    #

    failure_table: str | None = None

    failed_rows: pd.DataFrame | None = None

    #
    # Metadata
    #

    metadata: RuleMetadata | None = None

    @property
    def passed(self):

        return self.status == "pass"

    @property
    def failed(self):

        return self.status == "fail"

    @property
    def errored(self):

        return self.status == "error"


# ==========================================================
# Dataset Summary
# ==========================================================


@dataclass(slots=True)
class DBTValidationSummary:

    dataset: str

    primary_key: str

    tests: list[DBTTestResult] = field(default_factory=list)

    @property
    def total_tests(self):

        return len(self.tests)

    @property
    def passed(self):

        return sum(test.passed for test in self.tests)

    @property
    def failed(self):

        return sum(test.failed for test in self.tests)

    @property
    def errored(self):

        return sum(test.errored for test in self.tests)

    @property
    def success_rate(self):

        if self.total_tests == 0:

            return 0

        return round(
            self.passed / self.total_tests * 100,
            2,
        )
