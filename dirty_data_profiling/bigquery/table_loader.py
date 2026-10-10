# dirty_data_profiling/bigquery/table_loader.py

from google.cloud import bigquery

from data_ingestion.config.bigquery_config import PROJECT_ID


class BigQueryTableLoader:

    def __init__(self):

        self.client = bigquery.Client(project=PROJECT_ID)

    def load(
        self,
        dataset_name: str,
        table_name: str,
    ):

        query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{dataset_name}.{table_name}`
        """

        return self.client.query(query).to_dataframe()
