# dirty_data_profiling/metadata/metadata.py

"""
Metadata describing every supported validation rule.

This file is the single source of truth for:

- category
- severity
- business description
- business impact
- cleaning recommendation
- notebook colours
- dashboard icons

Every validator simply references the metadata here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuleMetadata:

    category: str

    severity: str

    description: str

    business_impact: str

    cleaning_strategy: str

    dbt_recommendation: str

    colour: str

    icon: str


RULE_METADATA = {
    "not_null": RuleMetadata(
        category="Missing Values",
        severity="Medium",
        description="Required value is missing.",
        business_impact="Missing values reduce completeness and may affect downstream analytics.",
        cleaning_strategy="Replace NULL values using business rules or COALESCE().",
        dbt_recommendation="coalesce(), nullif()",
        colour="#F4B183",
        icon="⚠️",
    ),
    "unique": RuleMetadata(
        category="Duplicate Records",
        severity="High",
        description="Duplicate value detected.",
        business_impact="Duplicates may inflate KPIs through double counting.",
        cleaning_strategy="Keep latest record using ROW_NUMBER().",
        dbt_recommendation="row_number()",
        colour="#C00000",
        icon="📄",
    ),
    "accepted_values": RuleMetadata(
        category="Business Rule Violations",
        severity="Medium",
        description="Value is outside accepted domain.",
        business_impact="Unexpected categories reduce reporting quality.",
        cleaning_strategy="Replace invalid values using CASE.",
        dbt_recommendation="case when",
        colour="#FFD966",
        icon="📋",
    ),
    "regex": RuleMetadata(
        category="Formatting",
        severity="Low",
        description="Value does not match expected format.",
        business_impact="Formatting inconsistencies reduce standardisation.",
        cleaning_strategy="Standardise values using regex_replace().",
        dbt_recommendation="regexp_replace(), trim()",
        colour="#9DC3E6",
        icon="✏️",
    ),
    "between": RuleMetadata(
        category="Numeric Issues",
        severity="High",
        description="Numeric value outside valid range.",
        business_impact="Invalid numbers distort reporting.",
        cleaning_strategy="Clamp or remove invalid values.",
        dbt_recommendation="least(), greatest(), safe_cast()",
        colour="#F8CBAD",
        icon="📈",
    ),
    "type": RuleMetadata(
        category="Type Issues",
        severity="High",
        description="Incorrect datatype detected.",
        business_impact="Incorrect datatypes prevent joins and calculations.",
        cleaning_strategy="Convert using SAFE_CAST().",
        dbt_recommendation="safe_cast()",
        colour="#D9EAD3",
        icon="🔢",
    ),
    "expression": RuleMetadata(
        category="Business Rule Violations",
        severity="High",
        description="Business rule failed.",
        business_impact="Record violates business logic.",
        cleaning_strategy="Review failing records.",
        dbt_recommendation="case when",
        colour="#FFE699",
        icon="🧮",
    ),
    "relationships": RuleMetadata(
        category="Referential Integrity",
        severity="High",
        description="Relationship validation failed.",
        business_impact="Broken joins reduce analytical accuracy.",
        cleaning_strategy="Validate foreign keys before loading.",
        dbt_recommendation="relationship tests",
        colour="#B4C7E7",
        icon="🔗",
    ),
}
