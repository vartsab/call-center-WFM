# Dataset Source

## Selected Seed Dataset

Dataset: NYC 311 Service Requests from 2020 to Present

Source: NYC Open Data / Socrata

API endpoint:

```text
https://data.cityofnewyork.us/resource/erm2-nwe9.csv
```

Project use:

- use real city service request timestamps and categories as the demand seed;
- preserve realistic daily, weekly, seasonal, and service-category patterns;
- synthetically generate missing call center operational fields such as wait time, talk time, after-call work, abandonment, SLA status, and agent assignment.

## Why This Dataset Fits

The project needs realistic inbound demand rather than a perfectly complete call center dataset. Public 311 records are suitable because they contain real request timestamps, service categories, agencies, boroughs, and status fields. These fields are enough to create the operational arrival curve and queue mix for a city service contact center.

Most public 311 datasets do not include agent-level call center metadata. That limitation is acceptable for this engineering project because synthetic operational fields can be generated with transparent assumptions and then used to demonstrate database design, dashboarding, forecasting, Erlang C staffing, and shift optimization.

## Initial Fields To Extract

| Field | Use |
| --- | --- |
| `unique_key` | Source request identifier. |
| `created_date` | Demand timestamp and simulated call start base. |
| `closed_date` | Optional service-resolution context. |
| `agency` | Operational owner. |
| `agency_name` | Descriptive agency name. |
| `complaint_type` | Queue/service category seed. |
| `descriptor` | More detailed queue/service context. |
| `location_type` | Optional service context. |
| `incident_zip` | Optional location dimension input. |
| `city` | Optional location dimension input. |
| `borough` | Optional location dimension input. |
| `status` | Service request status. |
| `latitude` | Optional map/dashboard field. |
| `longitude` | Optional map/dashboard field. |

## Sample Strategy

The first working sample should be small enough for rapid iteration:

- default date range: January 2025;
- current sample strategy: 6,200 records allocated across January 2025 days in proportion to real NYC 311 daily request counts;
- current daily sample range: 138 to 268 records per day;
- current generated source rows: 6,200;
- output: `data/raw/nyc_311_sample.csv`;
- generated output: `data/processed/synthetic_calls_sample.csv`.

The sample can be scaled later after the acquisition, generation, SQL, and dashboard paths are stable.

## Known Limitations

- A 311 service request is not guaranteed to be a phone call; records may originate from web, mobile, or other channels.
- True talk time, wait time, ACW, abandonment, and agent assignment are not public fields.
- Synthetic assumptions must be disclosed in the methodology and reports.
- The first synthetic generator preserves the real source date but simulates the call start time within that date to avoid API ordering artifacts in the MVP sample.
- Results should be framed as a realistic operational simulation seeded by real city-service demand, not as a claim about actual NYC 311 call center staffing.
