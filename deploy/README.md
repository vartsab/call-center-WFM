# VPS Deployment

This deployment runs the portfolio version of the WFM dashboard on a small VPS:

- Streamlit application container
- PostgreSQL container with compact analytical seed tables
- Caddy reverse proxy with automatic HTTPS
- simple dashboard password gate through `WFM_DEMO_PASSWORD`

It intentionally does not deploy the full raw NYC 311 extract or the full SQL Server warehouse. The VPS version is a compact, portfolio-friendly slice backed by Postgres seed tables.

## Current Target

The current deployment target is:

- VPS: Ubuntu 22.04 on Hetzner CX23, 2 vCPU, 4 GB RAM, 40 GB disk
- Public IP: `46.225.121.233`
- DNS: `wfm.vartsab.com` A record pointing to `46.225.121.233`
- Public dashboard URL: `https://wfm.vartsab.com:8443`
- Port `443`: reserved for the existing VPN service
- Port `8443`: WFM HTTPS dashboard
- Port `80`: Caddy HTTP challenge and redirect to `8443`

## Architecture

```text
Browser
  -> https://wfm.vartsab.com:8443
  -> Caddy container
  -> Streamlit app container
  -> Postgres container
```

Caddy listens on `80` and `8443`. Port `80` is required so Let's Encrypt can validate the domain and so plain HTTP requests can redirect to the dashboard HTTPS URL. Port `443` is not used by this stack.

## Build Seed Data

Run this from the project root before deploying or refreshing seed files:

```powershell
python scripts\build_portfolio_seed.py
```

The generated seed CSV files live in `deploy/seed/` and are loaded by `deploy/postgres/001_schema.sql` when the Postgres volume is first created.

## Environment

Create a private environment file:

```bash
cp deploy/env.example deploy/env.local
nano deploy/env.local
```

Use long unique values for `POSTGRES_PASSWORD` and `WFM_DEMO_PASSWORD`. Do not commit `deploy/env.local`; it is intentionally ignored by git.

Required values:

```text
POSTGRES_DB=wfm
POSTGRES_USER=wfm
POSTGRES_PASSWORD=replace-with-a-long-random-db-password
WFM_DEMO_PASSWORD=replace-with-demo-password
WFM_DOMAIN=wfm.vartsab.com
```

## VPS Bootstrap

Install Docker and Compose on Ubuntu:

```bash
apt-get update
apt-get install -y docker.io docker-compose-v2 ufw
systemctl enable --now docker
```

Allow SSH, HTTP, and the dashboard HTTPS port. Keep `443` only if another service, such as the VPN, needs it.

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 8443/tcp
ufw enable
```

If the existing VPN is already allowed on `443`, leave that rule in place.

## Deploy

Copy the repository bundle to the VPS and extract it under `/opt/wfm`. From `/opt/wfm`, validate and start the stack:

```bash
docker compose --env-file deploy/env.local config
docker compose --env-file deploy/env.local up -d --build
```

## Check

```bash
docker compose --env-file deploy/env.local ps
docker compose --env-file deploy/env.local logs --tail=80 app
docker compose --env-file deploy/env.local logs --tail=80 caddy
```

Useful database smoke test:

```bash
docker exec wfm-db-1 psql -U wfm -d wfm -c "select count(*) from dashboard_volume_30min;"
```

Expected access checks:

```bash
curl -I http://wfm.vartsab.com
curl -I https://wfm.vartsab.com:8443
```

The HTTP check should redirect to `https://wfm.vartsab.com:8443`. The HTTPS check should return the Streamlit app.

## Update

After code or config changes:

```bash
docker compose --env-file deploy/env.local up -d --build
```

If only Caddy config changed:

```bash
docker compose --env-file deploy/env.local up -d caddy
```

## Reset Seed Database

Postgres initialization scripts run only when the data volume is empty. To reload seed data from scratch:

```bash
docker compose --env-file deploy/env.local down -v
docker compose --env-file deploy/env.local up -d --build
```

## Operations Notes

- Keep `deploy/env.local` private because it contains the dashboard password and database password.
- Rotate `WFM_DEMO_PASSWORD` by editing `deploy/env.local` and restarting the `app` service.
- The seed database is reproducible from CSV files, so a formal backup is optional for the portfolio demo. If the app becomes more than a demo, add scheduled Postgres backups.
- Standard HTTPS on `443` can be enabled later by freeing port `443`, changing the Caddy port mapping back to `443:443`, and removing `https_port 8443` from `deploy/Caddyfile`.
