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
