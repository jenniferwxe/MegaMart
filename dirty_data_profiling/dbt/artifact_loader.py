# dirty_data_profiling/dbt/artifact_loader.py

from __future__ import annotations

import json
from pathlib import Path

from dirty_data_profiling.metadata.metadata import (
    RULE_METADATA,
    RuleMetadata,
)
from dirty_data_profiling.models import (
    DBTTestResult,
    DBTValidationSummary,
)

# ==========================================================
# Locations
# ==========================================================

TARGET = Path("dbt/target")


# ==========================================================
# Canonical dbt test names
# ==========================================================

TEST_NAME_MAPPING = {
    #
    # built-in
    #
    "not_null": "not_null",
    "unique": "unique",
    "accepted_values": "accepted_values",
    "relationships": "relationships",
    #
    # dbt_utils
    #
    "expression_is_true": "expression",
    #
    # dbt_expectations
    #
    "expect_column_values_to_match_regex": "regex",
    "expect_column_values_to_be_between": "between",
    "expect_column_values_to_be_of_type": "type",
}


def canonical_name(
    namespace: str | None,
    name: str,
) -> str:

    #
    # dbt built-in
    #

    if namespace is None:

        return TEST_NAME_MAPPING.get(
            name,
            name,
        )

    #
    # dbt_utils
    #

    if namespace == "dbt_utils":

        return TEST_NAME_MAPPING.get(
            name,
            name,
        )

    #
    # dbt_expectations
    #

    if namespace == "dbt_expectations":

        return TEST_NAME_MAPPING.get(
            name,
            name,
        )

    return name


# ==========================================================
# Loader
# ==========================================================


class DBTArtifactLoader:
    """
    Loads dbt artifacts and converts them into
    profiling-friendly objects.
    """

    def __init__(self):

        self.manifest = self._load(TARGET / "manifest.json")

        self.run_results = self._load(TARGET / "run_results.json")

        self.nodes = self.manifest["nodes"]

    @staticmethod
    def _load(
        path: Path,
    ):

        with open(
            path,
            encoding="utf8",
        ) as f:

            return json.load(f)

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------

    def _model_node(
        self,
        unique_id: str,
    ):

        node = self.nodes[unique_id]

        attached = node["attached_node"]

        return self.nodes[attached]

    def _primary_key(
        self,
        unique_id: str,
    ) -> list[str]:

        node = self.nodes[unique_id]

        # Resolve test node -> model node if necessary
        if node.get("resource_type") == "test":
            model_unique_id = node.get("attached_node")

            if not model_unique_id:
                raise ValueError(f"Test {unique_id} has no attached model.")

            model = self.nodes[model_unique_id]

        else:
            model = node

        # Explicit primary key metadata
        primary_key = model.get("primary_key", [])

        if primary_key:
            return primary_key

        model_unique_id = model["unique_id"]

        # Infer key from dbt tests
        for node in self.nodes.values():

            if node.get("resource_type") != "test":
                continue

            if node.get("attached_node") != model_unique_id:
                continue

            metadata = node.get("test_metadata", {})

            namespace = metadata.get("namespace")
            name = metadata.get("name")

            #
            # Single-column unique
            #

            if name == "unique" and namespace is None:
                column = node.get("column_name")

                if column:
                    return [column]

            #
            # Composite unique
            #

            if namespace == "dbt_utils" and name == "unique_combination_of_columns":
                combination = metadata.get("kwargs", {}).get("combination_of_columns")

                if combination:
                    return combination

        raise ValueError(
            f"{model['name']} has no primary key, "
            "unique test, or unique column combination."
        )

    def _dataset(
        self,
        unique_id: str,
    ) -> str:

        model = self._model_node(unique_id)

        return model["name"]

    def _column(
        self,
        node: dict,
    ):

        return node.get("column_name")

    def _metadata(self, node: dict, canonical_test: str) -> RuleMetadata:

        #
        # defaults
        #

        default = RULE_METADATA.get(canonical_test)

        meta = node.get("config", {}).get("meta", {})

        if default is None:
            return RuleMetadata(
                category=meta.get("category", "Unknown"),
                severity=meta.get("severity", "Medium"),
                description=meta.get("description", ""),
                business_impact=meta.get("business_impact", ""),
                cleaning_strategy=meta.get("cleaning_strategy", ""),
                dbt_recommendation=meta.get("dbt_recommendation", ""),
                colour=meta.get("colour", "#DDDDDD"),
                icon=meta.get("icon", "❓"),
            )

        #
        # dbt meta overrides
        #

        return RuleMetadata(
            category=meta.get("category", default.category),
            severity=meta.get("severity", default.severity),
            description=meta.get("description", default.description),
            business_impact=meta.get("business_impact", default.business_impact),
            cleaning_strategy=meta.get(
                "cleaning_strategy",
                default.cleaning_strategy,
            ),
            dbt_recommendation=meta.get(
                "dbt_recommendation",
                default.dbt_recommendation,
            ),
            colour=meta.get("colour", default.colour),
            icon=meta.get("icon", default.icon),
        )

    # ------------------------------------------------------
    # Failure Table
    # ------------------------------------------------------

    def _failure_table(
        self,
        node: dict,
        result: dict,
    ) -> str | None:
        """
        Returns the BigQuery table storing failed rows.

        dbt 1.11 unfortunately does not expose this consistently
        in the manifest, so we try a few locations.

        FailureLoader will later query this table.
        """

        #
        # Preferred (future dbt versions)
        #

        relation = result.get("relation_name")

        if relation:
            return relation.split(".")[-1].strip("`")

        adapter = result.get("adapter_response", {})

        relation = adapter.get("relation_name")

        if relation:
            return relation.split(".")[-1].strip("`")

        relation = adapter.get("table")

        if relation:
            return relation.strip("`")

        #
        # Fallback
        #

        alias = node.get("alias")

        if alias:
            return alias

        return None

    # ------------------------------------------------------
    # One dbt test
    # ------------------------------------------------------

    def _build_test_result(
        self,
        node: dict,
        result: dict,
    ) -> DBTTestResult:

        metadata = node["test_metadata"]

        test_type = canonical_name(
            metadata.get("namespace"),
            metadata["name"],
        )

        meta = node.get("config", {}).get("meta", {})

        rule = meta.get("title") or node["name"]

        return DBTTestResult(
            unique_id=node["unique_id"],
            model=self._dataset(
                node["unique_id"],
            ),
            column=self._column(
                node,
            ),
            test_type=test_type,
            rule=rule,
            status=result["status"],
            execution_time=result["execution_time"],
            failures=result.get(
                "failures",
            ),
            message=result.get(
                "message",
            ),
            compiled_sql=node.get(
                "compiled_code",
            ),
            relation_name=node.get(
                "relation_name",
            ),
            failure_table=self._failure_table(
                node,
                result,
            ),
            metadata=self._metadata(
                node,
                test_type,
            ),
        )

    # ------------------------------------------------------
    # Public
    # ------------------------------------------------------

    def load_results(
        self,
    ) -> list[DBTValidationSummary]:

        #
        # dataset -> summary
        #

        summaries: dict[
            str,
            DBTValidationSummary,
        ] = {}

        for result in self.run_results["results"]:

            unique_id = result["unique_id"]

            node = self.nodes.get(unique_id)

            if node is None:
                continue

            if node["resource_type"] != "test":
                continue

            dataset = self._dataset(
                unique_id,
            )

            if dataset not in summaries:

                summaries[dataset] = DBTValidationSummary(
                    dataset=dataset,
                    primary_key=self._primary_key(
                        unique_id,
                    ),
                )

            summaries[dataset].tests.append(
                self._build_test_result(
                    node,
                    result,
                )
            )

        return list(summaries.values())

    # ------------------------------------------------------
    # Convenience
    # ------------------------------------------------------

    def load_dataset(
        self,
        dataset: str,
    ) -> DBTValidationSummary:

        summaries = self.load_results()

        for summary in summaries:

            if summary.dataset == dataset:

                return summary

        raise ValueError(f"Dataset '{dataset}' not found.")
