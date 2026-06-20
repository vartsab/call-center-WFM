# Technology Choice Notes

## SQL Server Role

Microsoft SQL Server supports the engineering and analytics requirements of the project. The database layer demonstrates:

- raw data landing;
- dimensional warehouse design;
- fact and dimension tables;
- SQL transformations;
- analytical views;
- validation queries;
- dashboard-ready data access.

SQL Server Developer and Express editions are free for local development, and SQL Server is widely used in business intelligence and operations environments. That makes it a realistic technology for a workforce management system.

## Deployment Constraint

The main drawback is deployment. A free hosted SQL Server environment is harder to find than free-tier options for PostgreSQL, SQLite, DuckDB, or static CSV-backed demos.

The project therefore uses a two-layer database strategy:

- SQL Server remains the canonical local warehouse and analytical build layer;
- Streamlit can run locally against SQL Server or generated CSV artifacts;
- the public portfolio demo runs against compact PostgreSQL seed tables;
- code, SQL scripts, seed builder, and deployment files document how each layer can be rebuilt.

## Final Database Strategy

SQL Server remains the main development warehouse because:

- the SQL Server warehouse is already loaded and validated with 10,336,480 records;
- the views are already integrated into Streamlit;
- the documentation, validation summaries, and reporting evidence are built around SQL Server;
- the project requirements originally included MS SQL Server.

The final architecture uses SQL Server for the full 10.3M-row engineering pipeline and PostgreSQL for the externally hosted portfolio runtime.

## Portability

Recommended low-risk portability options:

1. Keep CSV fallback files for the Streamlit demo.
2. Add scripts that rebuild future forecast, staffing, and schedule outputs from existing artifacts.
3. Use compact PostgreSQL seed tables for the VPS deployment.
4. Keep the full raw and processed local datasets outside git.

Options reserved for a larger deployment:

- replacing SQL Server with PostgreSQL or DuckDB as the main warehouse;
- containerizing SQL Server unless deployment portability becomes a formal requirement;
- making MLflow or Docker mandatory for the core demo.
