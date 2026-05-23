# Repository Handoff

Last updated: 2026-05-23

## Repository

- Remote: `https://github.com/vartsab/call-center-WFM.git`
- Branch: `main`
- Current public demo: `https://wfm.vartsab.com:8443`
- Base commit before final deployment work: `db1c5bb Add staffing scenarios by forecast model`

## What The Repository Should Contain

The GitHub repository should contain the reproducible project package:

- source code under `src/`;
- Streamlit dashboard under `app/streamlit/`;
- SQL Server schema, raw, ETL, validation, and view scripts under `sql/`;
- methodology and final documentation under `docs/`;
- deployment package under `Dockerfile`, `docker-compose.yml`, and `deploy/`;
- compact Postgres portfolio seed files under `deploy/seed/`;
- tests under `tests/`;
- helper scripts under `scripts/`.

The repository should not contain local secrets or full raw/processed datasets.
Generated Office files and other local submission exports should stay outside git.

## Ignored Local Files

These files are intentionally local:

- `.venv/`
- `data/raw/`
- `data/processed/`
- `data/external/`
- `.streamlit/secrets.toml`
- `deploy/env.local`
- `deploy_bundle.tgz`
- `*.log`
- `docs/final/`
- `docs/reporting/word/`
- `*.docx`
- `*.pptx`

The weekly report Markdown sources under `docs/reporting/` are part of the repository. Generated Word and PowerPoint files are local submission artifacts and should remain outside git unless the program specifically requires storing Office binaries in the repository.

## Final Pre-Push Checks

Run before committing:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\scripts\check_demo_readiness.ps1
git status --short --untracked-files=all
```

Optional public deployment check:

```powershell
curl.exe -I http://wfm.vartsab.com
curl.exe -I https://wfm.vartsab.com:8443
```

Expected results:

- tests pass: `13 passed`;
- readiness check passes;
- HTTP redirects to HTTPS on `8443`;
- HTTPS returns `200 OK`.

## Suggested Commit Grouping

Use one final productization commit unless a reviewer wants separate commits:

```text
Finalize portfolio deployment and documentation
```

Suggested commit contents:

- deployment files and Postgres seed;
- Streamlit Postgres/password support;
- demo readiness scripts;
- updated README and documentation;
- deployment status and repository handoff docs;
- tests for dashboard source selection.

## Notes For Reviewers

The canonical analytical warehouse remains Microsoft SQL Server. The public VPS deployment uses PostgreSQL seed tables as a compact portfolio runtime so the dashboard can be shared externally without hosting the full 10.3M-row SQL Server warehouse.
