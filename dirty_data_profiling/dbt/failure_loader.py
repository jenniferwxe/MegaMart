# dirty_data_profiling/dbt/failure_loader.py

from __future__ import annotations

import pandas as pd
from google.cloud import bigquery


class FailureLoader:
    """
    Loads dbt failure tables stored by
    `dbt build --store-failures`.
    """

    def __init__(
        self,
        project: str = "mega-mart-storage",
        dataset: str = "synthetic_dirty_dbt_test__audit",
    ):

        self.client = bigquery.Client(project=project)

        self.project = project
        self.dataset = dataset

    def load(
        self,
        table_name: str,
    ) -> pd.DataFrame:

        query = f"""
        SELECT *

        FROM `{self.project}.{self.dataset}.{table_name}`

        ORDER BY 1
        """

        return self.client.query(query).to_dataframe()
