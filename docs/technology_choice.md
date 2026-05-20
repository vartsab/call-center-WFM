# Technology Choice Notes

## Why Microsoft SQL Server Is Defensible

Microsoft SQL Server is a reasonable choice for this capstone because the project is framed as an engineering and analytics system, not just a notebook exercise. The database layer needs to demonstrate:

- raw data landing;
- dimensional warehouse design;
- fact and dimension tables;
- SQL transformations;
- analytical views;
- validation queries;
- dashboard-ready data access.

SQL Server Developer and Express editions are free for local development, and SQL Server is widely used in business intelligence and operations environments. That makes it a realistic technology for a workforce management system.

## Main Weakness

The main drawback is deployment. A free hosted SQL Server environment is harder to find than free-tier options for PostgreSQL, SQLite, DuckDB, or static CSV-backed demos.

This affects the demonstration strategy, not the validity of the technology choice. The project can be presented as a local enterprise-style analytical application:

- SQL Server runs locally as the warehouse;
- Streamlit runs locally as the product interface;
- generated CSV artifacts provide a fallback for demo views and reproducibility;
- code and SQL scripts document how the warehouse can be rebuilt.

## Why Not Switch Now

Switching the main database at this stage would create more risk than value because:

- the SQL Server warehouse is already loaded and validated with 10,336,480 records;
- the views are already integrated into Streamlit;
- the documentation, validation summaries, and reporting evidence are built around SQL Server;
- the project requirements originally included MS SQL Server.

The better approach is to keep SQL Server as the main warehouse and add portability features around it.

## Portability Options

Recommended low-risk portability options:

1. Keep CSV fallback files for the Streamlit demo.
2. Add scripts that rebuild future forecast, staffing, and schedule outputs from existing artifacts.
3. Optionally add a lightweight DuckDB or SQLite export near the end if a fully portable no-SQL-Server demo becomes necessary.

Not recommended right now:

- replacing SQL Server with PostgreSQL or DuckDB as the main warehouse;
- containerizing SQL Server unless deployment portability becomes a formal requirement;
- making MLflow or Docker mandatory for the core demo.

## Report Framing

Suggested wording for the report:

> Microsoft SQL Server was selected as the analytical warehouse platform because the project required dimensional modeling, SQL-based transformations, validation views, and dashboard-ready aggregations similar to a business intelligence environment. Although the demonstration is local rather than cloud-hosted, the use of SQL Server is consistent with enterprise workforce analytics systems. To support reproducibility, generated planning artifacts are also exported as local CSV files and documented through summary outputs.
