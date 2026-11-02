from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="MegaMart | Data Quality",
    page_icon="📊",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "reports" / "profiling"


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------


@st.cache_data
def load_report(filename: str) -> pd.DataFrame:
    path = REPORT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Profiling report not found: {path}")

    return pd.read_csv(path)


try:
    summary = load_report("summary.csv")
    tests = load_report("test_results.csv")
    dirty_records = load_report("dirty_records.csv")
except (FileNotFoundError, pd.errors.ParserError) as exc:
    st.error(f"Unable to load profiling reports: {exc}")
    st.stop()


# ---------------------------------------------------------------------
# Derived metrics
# ---------------------------------------------------------------------

total_rows = int(summary["rows"].sum())
affected_rows = int(summary["affected_rows"].sum())
clean_rows = int(summary["clean_rows"].sum())

affected_rate = affected_rows / total_rows * 100 if total_rows else 0.0

statuses = tests["status"].astype(str).str.lower()

passed_tests = int(statuses.eq("pass").sum())
failed_tests = int(statuses.eq("fail").sum())
errored_tests = int(statuses.eq("error").sum())

# Count failed test instances, not distinct affected records.
failed_results = tests.loc[statuses.eq("fail")].copy()
failure_instances = int(
    pd.to_numeric(failed_results["failures"], errors="coerce").fillna(0).sum()
)

category_summary = (
    failed_results.assign(
        failures=pd.to_numeric(failed_results["failures"], errors="coerce").fillna(0)
    )
    .groupby("category")["failures"]
    .sum()
    .sort_values(ascending=False)
)

dataset_summary = summary.sort_values("affected_row_rate", ascending=False)


# ---------------------------------------------------------------------
# Dashboard header
# ---------------------------------------------------------------------

st.title("MegaMart Data Quality Overview")
st.caption("Profiling results from the synthetic retail data pipeline")

st.caption(
    f"Reporting scope: {len(summary)} datasets · "
    f"{len(tests)} validation tests · "
    f"{len(dirty_records):,} dirty-record entries"
)

st.divider()


# ---------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------

st.subheader("Overall data quality")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Datasets profiled",
    f"{summary['dataset'].nunique():,}",
)

col2.metric(
    "Rows across datasets",
    f"{total_rows:,}",
)

col3.metric(
    "Affected rows",
    f"{affected_rows:,}",
)

col4.metric(
    "Affected-row rate",
    f"{affected_rate:.2f}%",
)

st.caption(
    "Row counts are summed across datasets, not deduplicated "
    "across the entire data model."
)

st.divider()


# ---------------------------------------------------------------------
# Validation results
# ---------------------------------------------------------------------

st.subheader("Validation results")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Tests passed", f"{passed_tests:,}")
col2.metric("Tests failed", f"{failed_tests:,}")
col3.metric("Tests errored", f"{errored_tests:,}")
col4.metric("Failure instances", f"{failure_instances:,}")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Affected-row rate by dataset**")

    chart_data = dataset_summary[["dataset", "affected_row_rate"]].set_index("dataset")

    st.bar_chart(chart_data)

with chart_col2:
    st.markdown("**Failure instances by category**")

    if not category_summary.empty:
        st.bar_chart(category_summary)
    else:
        st.info("No failed test instances to display.")


st.divider()


# ---------------------------------------------------------------------
# Validation test explorer
# ---------------------------------------------------------------------

st.subheader("Validation test explorer")

st.caption(
    "Investigate individual validation results and identify "
    "rules requiring attention."
)

test_data = tests.copy()

# Normalise status values for filtering
test_data["_status"] = test_data["status"].astype(str).str.lower()

# Filters
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    status_options = ["All"] + sorted(test_data["_status"].unique().tolist())

    selected_status = st.selectbox(
        "Test status",
        status_options,
        key="test_status_filter",
    )

with filter_col2:
    category_options = ["All"] + sorted(
        test_data["category"].dropna().unique().tolist()
    )

    selected_test_category = st.selectbox(
        "Validation category",
        category_options,
        key="test_category_filter",
    )

test_search = st.text_input(
    "Search validation tests",
    placeholder="Search test name, model, rule or column",
)

filtered_tests = test_data.copy()

if selected_status != "All":
    filtered_tests = filtered_tests[filtered_tests["_status"] == selected_status]

if selected_test_category != "All":
    filtered_tests = filtered_tests[
        filtered_tests["category"] == selected_test_category
    ]

# Search across available test metadata
if test_search.strip():
    searchable_columns = [
        column for column in filtered_tests.columns if column != "_status"
    ]

    search_data = filtered_tests[searchable_columns].fillna("").astype(str)

    mask = search_data.apply(
        lambda column: column.str.contains(
            test_search.strip(),
            case=False,
            regex=False,
        )
    ).any(axis=1)

    filtered_tests = filtered_tests[mask]

# Summary
st.caption(f"Showing {len(filtered_tests):,} of {len(test_data):,} validation tests")

# Display results
display_tests = filtered_tests.drop(columns=["_status"])

st.dataframe(
    display_tests,
    use_container_width=True,
    hide_index=True,
)

# Export filtered results
st.download_button(
    "Download filtered test results",
    data=display_tests.to_csv(index=False).encode("utf-8"),
    file_name="filtered_validation_tests.csv",
    mime="text/csv",
    key="download_validation_tests",
)


# ---------------------------------------------------------------------
# Dataset-level investigation
# ---------------------------------------------------------------------

st.subheader("Dataset health")

selected_datasets = st.multiselect(
    "Filter datasets",
    options=sorted(summary["dataset"].dropna().unique()),
    placeholder="All datasets",
)

filtered_summary = dataset_summary.copy()

if selected_datasets:
    filtered_summary = filtered_summary[
        filtered_summary["dataset"].isin(selected_datasets)
    ]

display_columns = [
    "dataset",
    "rows",
    "affected_rows",
    "clean_rows",
    "affected_row_rate",
    "failure_instances",
    "most_affected_column",
    "most_failed_rule",
    "most_common_category",
]

st.dataframe(
    filtered_summary[display_columns],
    use_container_width=True,
    hide_index=True,
    column_config={
        "affected_row_rate": st.column_config.NumberColumn(
            "Affected-row rate (%)",
            format="%.2f%%",
        ),
        "failure_instances": st.column_config.NumberColumn(
            "Failure instances",
            format="%d",
        ),
    },
)

# ---------------------------------------------------------------------
# Issue severity overview
# ---------------------------------------------------------------------

st.divider()
st.subheader("Issue severity overview")

st.caption(
    "Understand the distribution of data quality issues "
    "and identify datasets requiring prioritised investigation."
)

# Normalise severity values
severity_data = dirty_records.copy()

severity_data["severity"] = (
    severity_data["severity"]
    .fillna("Unspecified")
    .astype(str)
    .str.strip()
    .replace("", "Unspecified")
)

# Severity distribution
severity_summary = (
    severity_data["severity"]
    .value_counts()
    .rename_axis("severity")
    .reset_index(name="failure_entries")
)

# Severity breakdown by dataset
severity_by_dataset = (
    severity_data.groupby(["dataset", "severity"]).size().unstack(fill_value=0)
)

# Visualisations
severity_col1, severity_col2 = st.columns(2)

with severity_col1:
    st.markdown("**Issue entries by severity**")

    if not severity_summary.empty:
        chart_data = severity_summary.set_index("severity")

        st.bar_chart(chart_data["failure_entries"])
    else:
        st.info("No severity data available.")

with severity_col2:
    st.markdown("**Severity distribution by dataset**")

    if not severity_by_dataset.empty:
        st.bar_chart(severity_by_dataset)
    else:
        st.info("No dataset severity data available.")

# Severity summary table
st.markdown("**Severity summary**")

if not severity_summary.empty:
    st.dataframe(
        severity_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "severity": st.column_config.TextColumn("Severity level"),
            "failure_entries": st.column_config.NumberColumn(
                "Dirty-record entries",
                format="%d",
            ),
        },
    )

st.caption(
    "Counts represent dirty-record entries, not necessarily "
    "distinct affected records. A single record may have multiple "
    "validation failures."
)


# ---------------------------------------------------------------------
# Dataset-level drilldown
# ---------------------------------------------------------------------

st.divider()
st.subheader("Dataset investigation")

st.caption(
    "Explore dataset-specific data quality metrics, identify "
    "recurring validation issues and inspect affected records."
)

# Dataset selection
dataset_options = sorted(summary["dataset"].dropna().unique().tolist())

selected_detail_dataset = st.selectbox(
    "Select a dataset to investigate",
    options=dataset_options,
    key="dataset_detail_selector",
)

# Retrieve dataset-level summary
dataset_detail = summary.loc[summary["dataset"] == selected_detail_dataset].iloc[0]

# Retrieve associated dirty records
dataset_records = dirty_records.loc[
    dirty_records["dataset"] == selected_detail_dataset
].copy()

# Dataset KPIs
st.markdown(f"**{selected_detail_dataset} — Data quality summary**")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

metric_col1.metric(
    "Total rows",
    f"{int(dataset_detail['rows']):,}",
)

metric_col2.metric(
    "Affected rows",
    f"{int(dataset_detail['affected_rows']):,}",
)

metric_col3.metric(
    "Clean rows",
    f"{int(dataset_detail['clean_rows']):,}",
)

metric_col4.metric(
    "Affected-row rate",
    f"{float(dataset_detail['affected_row_rate']):.2f}%",
)

st.caption(
    f"{len(dataset_records):,} dirty-record entries identified " "in this dataset."
)

# Issue breakdowns
detail_col1, detail_col2 = st.columns(2)

with detail_col1:
    st.markdown("**Issues by category**")

    if not dataset_records.empty:
        category_breakdown = (
            dataset_records["category"].fillna("Unspecified").value_counts()
        )

        st.bar_chart(category_breakdown)
    else:
        st.info("No dirty-record entries found.")

with detail_col2:
    st.markdown("**Most affected columns**")

    if not dataset_records.empty:
        column_breakdown = (
            dataset_records["column"].fillna("Unspecified").value_counts().head(10)
        )

        st.bar_chart(column_breakdown)
    else:
        st.info("No column-level issues found.")

# Most frequently failing rules
st.markdown("**Validation rules requiring attention**")

if not dataset_records.empty:
    rule_breakdown = (
        dataset_records.groupby("rule")
        .size()
        .reset_index(name="failure_entries")
        .sort_values("failure_entries", ascending=False)
    )

    st.dataframe(
        rule_breakdown,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No validation rule failures found.")

# Associated dirty records
st.markdown("**Affected records**")

st.dataframe(
    dataset_records.head(500),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Breakdown counts represent dirty-record entries. "
    "A single record may contribute multiple entries."
)


# ---------------------------------------------------------------------
# Dirty-record investigation
# ---------------------------------------------------------------------

st.divider()
st.subheader("Dirty-record explorer")

search_term = st.text_input(
    "Search records",
    placeholder="Search dataset, rule, column, category or primary key",
)

record_filters = st.columns(3)

with record_filters[0]:
    dataset_options = sorted(dirty_records["dataset"].dropna().unique())
    selected_dataset = st.selectbox(
        "Dataset",
        ["All"] + dataset_options,
    )

with record_filters[1]:
    category_options = sorted(dirty_records["category"].dropna().unique())
    selected_category = st.selectbox(
        "Failure category",
        ["All"] + category_options,
    )

with record_filters[2]:
    severity_options = sorted(dirty_records["severity"].dropna().unique())
    selected_severity = st.selectbox(
        "Severity",
        ["All"] + severity_options,
    )

filtered_records = dirty_records.copy()

if selected_dataset != "All":
    filtered_records = filtered_records[filtered_records["dataset"] == selected_dataset]

if selected_category != "All":
    filtered_records = filtered_records[
        filtered_records["category"] == selected_category
    ]

if selected_severity != "All":
    filtered_records = filtered_records[
        filtered_records["severity"] == selected_severity
    ]

if search_term.strip():
    searchable_columns = [
        column
        for column in [
            "dataset",
            "primary_key",
            "rule",
            "column",
            "category",
        ]
        if column in filtered_records.columns
    ]

    matches = filtered_records[searchable_columns].fillna("").astype(str)
    mask = matches.apply(
        lambda column: column.str.contains(
            search_term.strip(),
            case=False,
            regex=False,
        )
    ).any(axis=1)

    filtered_records = filtered_records[mask]

st.caption(
    f"{len(filtered_records):,} matching entries"
    + (" · Showing first 500" if len(filtered_records) > 500 else "")
)

st.dataframe(
    filtered_records.head(500),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download filtered dirty records",
    data=filtered_records.to_csv(index=False).encode("utf-8"),
    file_name="filtered_dirty_records.csv",
    mime="text/csv",
)


# ---------------------------------------------------------------------
# Dashboard methodology
# ---------------------------------------------------------------------

st.divider()

with st.expander("Data quality metrics and methodology"):

    st.markdown(
        """
        ### Metric definitions

        | Metric | Definition |
        |---|---|
        | Total rows | Sum of profiled rows across datasets |
        | Affected rows | Sum of rows containing data quality issues |
        | Clean rows | Rows without identified data quality issues |
        | Affected-row rate | Affected rows / Total rows × 100 |
        | Passed tests | Number of validation tests with pass status |
        | Failed tests | Number of validation tests with fail status |
        | Errored tests | Number of validation tests with error status |
        | Failure instances | Sum of failure counts from failed tests |
        | Dirty-record entries | Individual validation failure entries |

        ### Interpretation notes

        - Row counts are aggregated across datasets and are not
          deduplicated across the entire data model.
        - A single record may have multiple validation failures.
        - Failure instances and dirty-record entries represent
          different measurements.
        - Severity breakdowns count dirty-record entries,
          not unique affected records.
        - Affected-row rates reflect the profiling results
          generated by the data quality pipeline.

        ### Data sources

        - `summary.csv`: Dataset-level profiling metrics.
        - `test_results.csv`: Individual validation test results.
        - `dirty_records.csv`: Record-level validation failures.
        """
    )
