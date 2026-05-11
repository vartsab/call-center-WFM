# Data Dictionary

This is the initial target schema. Final column names may change after seed data selection and SQL implementation.

## Fact_Calls

Grain: one row per simulated inbound call/contact.

| Column | Type | Description |
| --- | --- | --- |
| Call_ID | bigint | Unique call identifier. |
| Source_Request_ID | varchar | Original public service request identifier, if available. |
| Date_ID | int | Foreign key to `Dim_Date`. |
| Time_ID | int | Foreign key to `Dim_Time`, usually 30-minute interval. |
| Agent_ID | int | Foreign key to `Dim_Agent`; null or special value for abandoned before assignment. |
| Queue_ID | int | Foreign key to `Dim_Queue`. |
| Call_Start_Datetime | datetime2 | Simulated call arrival timestamp. |
| Answer_Datetime | datetime2 | Simulated answer timestamp, if answered. |
| End_Datetime | datetime2 | Simulated call end timestamp. |
| Talk_Time_Sec | int | Simulated talk time. |
| Hold_Time_Sec | int | Simulated wait/hold time before answer. |
| ACW_Time_Sec | int | Simulated after-call work. |
| Handle_Time_Sec | int | Talk time plus ACW time. |
| Abandoned_Flag | bit | Whether caller abandoned before answer. |
| SLA_Met_Flag | bit | Whether the call met service-level target. |

## Dim_Date

| Column | Type | Description |
| --- | --- | --- |
| Date_ID | int | Date key, usually `YYYYMMDD`. |
| Calendar_Date | date | Calendar date. |
| Day_Of_Week | varchar | Day name. |
| Week_Of_Year | int | Week number. |
| Month | int | Month number. |
| Month_Name | varchar | Month name. |
| Quarter | int | Calendar quarter. |
| Year | int | Calendar year. |
| Is_Weekend | bit | Weekend flag. |
| Is_Holiday | bit | Holiday flag, if available. |

## Dim_Time

| Column | Type | Description |
| --- | --- | --- |
| Time_ID | int | Time key, for example `HHMM`. |
| Interval_Start_Time | time | Start of the 30-minute interval. |
| Interval_End_Time | time | End of the 30-minute interval. |
| Hour | int | Hour of day. |
| Half_Hour_Index | int | Index from 0 to 47. |
| Shift_Band | varchar | Morning, midday, evening, overnight, or similar. |

## Dim_Agent

| Column | Type | Description |
| --- | --- | --- |
| Agent_ID | int | Unique synthetic agent identifier. |
| Agent_Name | varchar | Synthetic name or anonymized label. |
| Skill_Group | varchar | Queue/skill group assignment. |
| Hire_Date | date | Synthetic hire date. |
| Tenure_Band | varchar | Synthetic tenure group. |
| Employment_Type | varchar | Full-time, part-time, contractor, etc. |
| Active_Flag | bit | Agent active status. |

## Dim_Queue

| Column | Type | Description |
| --- | --- | --- |
| Queue_ID | int | Unique queue identifier. |
| Queue_Name | varchar | Queue or service category. |
| Service_Category | varchar | Higher-level service grouping. |
| SLA_Target_Sec | int | Target answer time, such as 20 seconds. |
| Target_Service_Level | decimal | Target percentage answered within SLA. |

## Modeling Notes

- Synthetic fields must be reproducible with a random seed.
- Talk time should use a right-skewed distribution such as log-normal or gamma.
- Abandonment probability should increase as wait time increases.
- Agent assignment should respect queue/skill groups when implemented.
- All synthetic assumptions must be documented in `docs/decision_log.md` or a dedicated methodology note.

## Seed Dataset Fields

Initial seed dataset: NYC 311 Service Requests from 2020 to Present.

| Source Field | Target Use |
| --- | --- |
| `unique_key` | `Fact_Calls.Source_Request_ID` |
| `created_date` | `Source_Created_Datetime` and `Call_Start_Datetime` seed |
| `closed_date` | Optional future service-resolution analysis |
| `agency` | Optional future agency dimension |
| `agency_name` | Optional future agency dimension |
| `complaint_type` | `Dim_Queue.Queue_Name` seed |
| `descriptor` | Queue classification helper |
| `location_type` | Optional service context |
| `incident_zip` | `Fact_Calls.Incident_Zip` |
| `incident_address` | Not planned for fact table; avoid unnecessary address exposure in dashboards |
| `city` | Optional location dimension |
| `status` | `Fact_Calls.Source_Status` |
| `borough` | `Fact_Calls.Borough` |
| `latitude` | Optional future map view |
| `longitude` | Optional future map view |

## Generated Sample Outputs

The first generation script writes:

| Output | Description |
| --- | --- |
| `data/raw/nyc_311_sample.csv` | Downloaded public 311 seed sample. |
| `data/raw/nyc_311_sample_metadata.json` | Query metadata for reproducibility. |
| `data/processed/synthetic_calls_sample.csv` | Simulated call-level fact source. |
| `data/processed/dim_agents_sample.csv` | Synthetic agent dimension source. |
| `data/processed/dim_queues_sample.csv` | Queue dimension source derived from complaint types. |
| `docs/sample_generation_summary.json` | Committed summary metrics from the latest generated sample. |

## Latest Generated Sample Summary

The first generated sample was created from a January 2025 NYC 311 extract with up to 200 records per day.

| Metric | Value |
| --- | ---: |
| Source rows | 6,200 |
| Synthetic agents | 60 |
| Queues | 101 |
| Abandonment rate | 0.0661 |
| Average handle time, answered calls | 517.57 sec |
| Distinct 30-minute intervals | 1,321 |
| Maximum calls in one interval | 17 |
