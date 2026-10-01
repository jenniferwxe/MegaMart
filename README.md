# MegaMart - End-to-End Retail Analytics & AI Data Platform
> A production inspired retail analytics platform built with Python, BigQuery, dbt, data quality engineering, and Model Context Protocol (MCP) powered AI analytics.

## Overview
MegaMart is an end-to-end synthetic retail analytics platform that simulates a modern supermarket and e-commerce data environment. The project deliberately introduces realistic data quality issues and processes the data through validation, transformation, analytics, machine learning preparation, business intelligence, and AI assisted analysis.

The platform demonstrates how **data engineering**, **data quality**, **business analytics**, **machine learning**, **cloud data warehousing**, and **AI tooling** can be integrated across a complete analytics lifecycle.

The project covers multiple interconnected business domains including:
- 👥 Customers
- 🛍️ Products
- 🏪 Stores
- 🧾 Transactions
- 📦 Inventory
- 🎯 Marketing Campaigns
- 🌐 Customer Sessions & Clickstreams
- 📈 Product Lifecycle & Version History

## Why MegaMart?
Many analytics projects begin with a clean dataset and end with a dashboard. Real world analytics workflows require substantially more work before data can be consumed and insights can be generated.

MegaMart is designed around practical questions such as:
- Is the source data trustworthy?
- How frequently and severely do quality issues occur?
- How can problematic data be identified and handled before downstream analysis?
- How can analytical data be exposed to AI systems in a controlled and explainable way?

## Workflow
MegaMart follows data through the complete analytical lifecycle, from generation to consumption.

### 1. Synthetic Data Generation
Generate interconnected synthetic datasets using Python with configurable volumes, deterministic random seeds, business rules, and referential relationships.

### 2. Dirty Data Injection
Inject controlled data quality issues using Python to simulate realistic source system imperfections, edge cases, and varying levels of data quality severity.

### 3. Data Ingestion & Warehousing
Ingest generated datasets into **Google BigQuery** as the cloud data warehouse, establishing the raw data layer.

### 4. dbt Transformation & Testing
Use dbt to define the transformation pipeline and data quality framework through SQL models, validation tests, reusable macros, and automated test execution.

### 5. Data Quality Profiling
Execute dbt tests with stored failures, then extract and analyse **dbt artifacts and failure records** to quantify affected rows, failure rates, failure instances, and violated business rules.

Results are aggregated and presented in **Jupyter Notebook** to make data quality findings accessible to both technical and non-technical stakeholders.

### 6. Data Cleaning & Transformation
Clean and standardise raw data into trusted analytical datasets using dbt SQL models, standardisation logic, deduplication, data type handling, business rules, and derived fields to form a staging layer.

### 7. Exploratory Data Analysis (EDA)
Perform statistical and visual analysis in Python using Jupyter Notebook to assess distributions, relationships, trends, patterns and anomalies across the transformed datasets.

### 8. Feature Engineering
Construct reusable analytical and machine learning ready features using Python and SQL, including derived metrics, customer attributes, behavioural indicators, and business KPIs.

### 9. Advanced Analytics & Machine Learning
Apply predictive modelling, customer segmentation, forecasting, and association-rule mining to support business decision making.

### 8. Dashboarding & Business Intelligence
Develop interactive Power BI dashboards using dashboard ready datasets from the production analytical layer to monitor business KPIs, customer behaviour, sales performance, inventory, and other operational metrics.

### 9. MCP Analytics Tools
Build Model Context Protocol (MCP) tools that expose the analytical environment to AI agents, enabling programmatic access to business data, controlled querying, analytical workflows, and AI assisted business question answering.

## Supporting Practises
The technical workflow is supported by engineering and project-management practises throughout the project.
- **Project Management** - planning, milestones, sprint management, and task tracking using Jira and Confluence.
- **Engineering & Quality Practises** - automated testing, validation, CI/CD, dependency management, pre-commit checks, and reproducible workflows using Python, Github Actions, and development tooling.
- **Documentation & Knowledge Management** - architecture, documentation, methodology, technical decisions, debugging guides, implementation notes, and user documentation using Confluence and Github repository documentation.
- **Version Control** - source controlled code, configuration driven workflows, deterministic data generation, and repeatable development and production runs.

## Scale & Reproducibility:
MegaMart supports **configurable dataset sizes** for development and larger production style runs. Dataset volumes, business entities, and geeneration parameters can be adjusted through configuration.

The current synthetic data period spans 1 January 2023 to 31 December 2025. A fixed random seed ensures deterministic generation, allowing the same environment and data characteristics to be reproduced across runs while supporting large scale dataset generation.
