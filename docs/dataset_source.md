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

## Full Extract Now Used

The project now uses a full local extract for 2023-01-01 through 2025-12-31.

| Metric | Value |
| --- | ---: |
| Raw extracted records | 10,336,480 |
| Chunk files | 225 |
| Date count | 1,096 |
| Average daily records | 9,431.09 |
| Maximum daily records | 17,962 |
| SQL raw table rows | 10,336,480 |

Yearly source volume:

| Year | Records |
| --- | ---: |
| 2023 | 3,224,722 |
| 2024 | 3,456,770 |
| 2025 | 3,654,988 |

The raw extract is loaded into:

```text
dbo.Raw_NYC_311_Service_Requests
```

Raw CSV chunks and processed modeling files are excluded from version control.

## Why This Dataset Fits

The project requires realistic inbound demand. Public 311 records provide request timestamps, service categories, agencies, boroughs, and status fields that support an operational arrival curve and service mix.

Most public 311 datasets do not include agent-level call center metadata. That limitation is acceptable for this engineering project because synthetic operational fields can be generated with transparent assumptions and then used to demonstrate database design, dashboarding, forecasting, Erlang C staffing, and shift optimization.

## Extracted Fields

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

The smaller January 2025 synthetic call sample remains in the project as a fast development fixture for SQL schema work, agent-level metrics, and dashboard fallback mode. It is no longer the main forecasting history.

Current sample fixture:

- date range: January 2025;
- generated source rows: 6,200;
- generated output: `data/processed/synthetic_calls_sample.csv`;
- SQL fact rows: 6,200.

## Known Limitations

- A 311 service request is not guaranteed to be a phone call; records may originate from web, mobile, or other channels.
- True talk time, wait time, ACW, abandonment, and agent assignment are not public fields.
- Synthetic assumptions must be disclosed in the methodology and reports.
- Results should be framed as a realistic operational simulation seeded by real city-service demand, not as a claim about actual NYC 311 call center staffing.
