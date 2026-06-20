# Portfolio Deployment Status

Last updated: 2026-05-23

## Public Endpoint

- Dashboard URL: `https://wfm.vartsab.com`
- DNS: `wfm.vartsab.com` A record points to `46.225.121.233`
- Host: Hetzner CX23, Ubuntu 22.04, 2 vCPU, 4 GB RAM, 40 GB disk
- Deployment directory: `/opt/wfm`
- Verification: public HTTPS returns `200 OK`, dashboard opens without a password, dashboard reads `Data source: Postgres`

## Port Plan

The VPS also runs an existing Xray/V2Ray service. It was moved from `443` to `4443` so the WFM stack can use standard HTTPS.

| Port | Owner | Purpose |
| ---: | --- | --- |
| 22 | SSH | server administration |
| 80 | Caddy | Let's Encrypt HTTP validation and redirect |
| 443 | Caddy | WFM dashboard HTTPS endpoint |
| 4443 | Xray/V2Ray | VPN/proxy service |

## Runtime Stack

```text
Docker Compose
  db      postgres:16-alpine, seeded from deploy/seed/
  app     Streamlit dashboard, CALLCENTER_DASHBOARD_SOURCE=postgres
  caddy   reverse proxy, HTTPS on 443
```

Secrets live in `/opt/wfm/deploy/env.local` on the VPS and are not committed to git.

## Verified State

Verified on 2026-05-23:

- `docker compose --env-file deploy/env.local ps` shows `db`, `app`, and `caddy` running.
- Postgres health check is healthy.
- Dashboard copy/style hardening update was redeployed with `docker compose --env-file deploy/env.local up -d --build`.
- Caddy obtained a Let's Encrypt certificate for `wfm.vartsab.com` using the HTTP-01 challenge on port `80`.
- `http://wfm.vartsab.com` returns `308` to `https://wfm.vartsab.com/`.
- `https://wfm.vartsab.com` returns `200 OK`.
- `https://wfm.vartsab.com/_stcore/health` returns `ok`.
- Dashboard source indicator shows `Data source: Postgres`.
- `dashboard_volume_30min` row count is `252790`.
- Password-gated browser smoke and browser console checks were previously verified on 2026-05-21. The public portfolio demo now opens without a password; the password gate remains optional through `WFM_DEMO_PASSWORD`.

## Deployment Commands

From `/opt/wfm`:

```bash
docker compose --env-file deploy/env.local config
docker compose --env-file deploy/env.local up -d --build
docker compose --env-file deploy/env.local ps
```

Check logs:

```bash
docker compose --env-file deploy/env.local logs --tail=80 app
docker compose --env-file deploy/env.local logs --tail=80 caddy
```

Check seed data:

```bash
docker exec wfm-db-1 psql -U wfm -d wfm -c "select count(*) from dashboard_volume_30min;"
```

Check public routing:

```bash
curl -I http://wfm.vartsab.com
curl -I https://wfm.vartsab.com
```

## Rebuild Seed

From the local project root:

```powershell
python scripts\build_portfolio_seed.py
```

Then redeploy the updated repository bundle to `/opt/wfm` and recreate the Postgres volume if the seed table contents must be reloaded.
