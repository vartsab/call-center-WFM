# Raw NYC 311 SQL Server Insight Mining

Source: `dbo.Raw_NYC_311_Service_Requests` and `dbo.vw_Raw_NYC_311_Volume_30Min` in the local `CallCenterWFM` SQL Server database.

Included scope: real NYC 311 fields, source timestamps, complaint types, descriptors, agencies, boroughs, and raw timestamp aggregations. Excluded fields: synthetic AHT, SLA, abandonment, agent records, staffing outputs, roster simulation, and derived service-category mapping.

## Headline Findings

- Raw records: **10,336,480** from **2023-01-01 00:00:00** to **2025-12-31 23:59:28**.
- Annual volume rose from **3,224,722** in 2023 to **3,654,988** in 2025, a **13.3%** increase.
- Busiest month: **2025-01** with **348,179** requests. Lowest month: **2023-02** with **225,002** requests.
- The top 10 recurring weekday/half-hour cells account for **4.9%** of a typical week; the top 20 account for **9.6%**.
- HEAT/HOT WATER is strongly seasonal: **79.5%** of its volume falls in November-March.

## Yearly Volume

| Year | Requests |
| --- | --- |
| 2023 | 3,224,722 |
| 2024 | 3,456,770 |
| 2025 | 3,654,988 |

## Top Recurring Weekday / Half-Hour Arrival Slots

| Day | Time | Avg requests | Total requests |
| --- | --- | --- | --- |
| Tuesday | 10:00 | 331.58 | 52,058 |
| Tuesday | 09:30 | 330.33 | 51,862 |
| Monday | 10:00 | 328.29 | 51,542 |
| Tuesday | 10:30 | 327.16 | 51,364 |
| Monday | 09:30 | 326.21 | 51,215 |
| Tuesday | 11:30 | 322.27 | 50,597 |
| Tuesday | 11:00 | 321.51 | 50,477 |
| Monday | 11:30 | 321.44 | 50,466 |
| Monday | 10:30 | 319.73 | 50,197 |
| Tuesday | 09:00 | 318.50 | 50,004 |
| Thursday | 09:30 | 317.19 | 49,482 |
| Monday | 11:00 | 315.90 | 49,596 |

## Day-of-Week Arrival Mix

| Day | Requests | Share |
| --- | --- | --- |
| Monday | 1,566,287 | 15.2% |
| Tuesday | 1,564,247 | 15.1% |
| Wednesday | 1,517,478 | 14.7% |
| Thursday | 1,488,862 | 14.4% |
| Friday | 1,494,515 | 14.5% |
| Saturday | 1,337,540 | 12.9% |
| Sunday | 1,367,551 | 13.2% |

## Hour-of-Day Arrival Mix

| Hour | Requests | Share |
| --- | --- | --- |
| 0 | 367,074 | 3.6% |
| 1 | 246,311 | 2.4% |
| 2 | 168,941 | 1.6% |
| 3 | 129,957 | 1.3% |
| 4 | 121,370 | 1.2% |
| 5 | 138,476 | 1.3% |
| 6 | 225,598 | 2.2% |
| 7 | 373,528 | 3.6% |
| 8 | 529,683 | 5.1% |
| 9 | 612,545 | 5.9% |
| 10 | 624,961 | 6.0% |
| 11 | 617,452 | 6.0% |
| 12 | 585,515 | 5.7% |
| 13 | 566,138 | 5.5% |
| 14 | 569,002 | 5.5% |
| 15 | 549,159 | 5.3% |
| 16 | 531,429 | 5.1% |
| 17 | 494,958 | 4.8% |
| 18 | 479,285 | 4.6% |
| 19 | 465,643 | 4.5% |
| 20 | 466,813 | 4.5% |
| 21 | 498,815 | 4.8% |
| 22 | 523,745 | 5.1% |
| 23 | 450,082 | 4.4% |

## Top Complaint Reasons

| Complaint type | Requests | Share |
| --- | --- | --- |
| Illegal Parking | 1,559,794 | 15.1% |
| Noise - Residential | 1,141,098 | 11.0% |
| HEAT/HOT WATER | 812,019 | 7.9% |
| Blocked Driveway | 509,345 | 4.9% |
| Noise - Street/Sidewalk | 483,499 | 4.7% |
| UNSANITARY CONDITION | 355,293 | 3.4% |
| Plumbing | 207,846 | 2.0% |
| Street Condition | 205,582 | 2.0% |
| Abandoned Vehicle | 203,175 | 2.0% |
| Noise - Commercial | 200,054 | 1.9% |
| Water System | 196,944 | 1.9% |
| PAINT/PLASTER | 185,015 | 1.8% |
| Dirty Condition | 169,822 | 1.6% |
| Noise | 163,955 | 1.6% |
| Derelict Vehicles | 143,719 | 1.4% |

## Top Complaint + Descriptor Pairs

| Complaint type | Descriptor | Requests |
| --- | --- | --- |
| Noise - Residential | Loud Music/Party | 706,596 |
| HEAT/HOT WATER | ENTIRE BUILDING | 536,162 |
| Illegal Parking | Blocked Hydrant | 433,868 |
| Noise - Street/Sidewalk | Loud Music/Party | 380,831 |
| Blocked Driveway | No Access | 368,088 |
| Illegal Parking | Posted Parking Sign Violation | 362,128 |
| Noise - Residential | Banging/Pounding | 336,763 |
| HEAT/HOT WATER | APARTMENT ONLY | 275,856 |
| Abandoned Vehicle | With License Plate | 203,175 |
| Illegal Parking | Blocked Sidewalk | 201,914 |
| UNSANITARY CONDITION | PESTS | 185,676 |
| Noise - Commercial | Loud Music/Party | 159,936 |
| Dirty Condition | Trash | 152,109 |
| Derelict Vehicles | Derelict Vehicles | 143,719 |
| Blocked Driveway | Partial Access | 141,255 |

## Borough Mix

| Borough | Requests | Share |
| --- | --- | --- |
| BROOKLYN | 3,124,257 | 30.2% |
| QUEENS | 2,481,925 | 24.0% |
| BRONX | 2,202,326 | 21.3% |
| MANHATTAN | 2,133,135 | 20.6% |
| STATEN ISLAND | 383,591 | 3.7% |
| Unspecified | 11,246 | 0.1% |

## Agency Mix

| Agency | Agency name | Requests | Share |
| --- | --- | --- | --- |
| NYPD | New York City Police Department | 4,658,183 | 45.1% |
| HPD | Department of Housing Preservation and Development | 2,195,355 | 21.2% |
| DSNY | Department of Sanitation | 934,965 | 9.0% |
| DOT | Department of Transportation | 610,862 | 5.9% |
| DEP | Department of Environmental Protection | 559,087 | 5.4% |
| DPR | Department of Parks and Recreation | 377,055 | 3.6% |
| DOB | Department of Buildings | 306,837 | 3.0% |
| DOHMH | Department of Health and Mental Hygiene | 259,152 | 2.5% |
| DHS | Department of Homeless Services | 151,066 | 1.5% |
| TLC | Taxi and Limousine Commission | 109,828 | 1.1% |
| EDC | Economic Development Corporation | 108,367 | 1.0% |
| DCWP | Department of Consumer and Worker Protection | 59,181 | 0.6% |

## Fastest-Growing High-Volume Complaint Types

| Complaint type | 2023 | 2025 | Delta | Growth |
| --- | --- | --- | --- | --- |
| Noise - Residential | 298,453 | 463,349 | 164,896 | 55.3% |
| Illegal Parking | 476,809 | 577,257 | 100,448 | 21.1% |
| HEAT/HOT WATER | 231,323 | 315,946 | 84,623 | 36.6% |
| Noise - Street/Sidewalk | 147,449 | 173,049 | 25,600 | 17.4% |
| Water System | 53,637 | 77,518 | 23,881 | 44.5% |
| Vendor Enforcement | 13,959 | 29,117 | 15,158 | 108.6% |
| Encampment | 33,710 | 47,998 | 14,288 | 42.4% |
| Dirty Condition | 49,657 | 61,047 | 11,390 | 22.9% |
| Traffic Signal Condition | 38,452 | 47,998 | 9,546 | 24.8% |
| Drug Activity | 19,192 | 27,964 | 8,772 | 45.7% |
| Lead | 10,822 | 18,495 | 7,673 | 70.9% |
| PLUMBING | 66,143 | 72,653 | 6,510 | 9.8% |

## Biggest Declines

| Complaint type | 2023 | 2025 | Delta | Growth |
| --- | --- | --- | --- | --- |
| Noise - Helicopter | 59,127 | 20,554 | -38,573 | -65.2% |
| New Tree Request | 22,427 | 785 | -21,642 | -96.5% |
| Missed Collection | 55,927 | 42,977 | -12,950 | -23.2% |
| Rodent | 41,748 | 31,312 | -10,436 | -25.0% |
| Derelict Vehicles | 51,301 | 43,229 | -8,072 | -15.7% |
| Noise - Vehicle | 51,256 | 43,223 | -8,033 | -15.7% |
| WATER LEAK | 46,211 | 38,395 | -7,816 | -16.9% |
| Sewer | 29,976 | 26,141 | -3,835 | -12.8% |
| Noise - Commercial | 67,749 | 63,958 | -3,791 | -5.6% |
| General Construction/Plumbing | 38,058 | 35,145 | -2,913 | -7.7% |
| Consumer Complaint | 20,927 | 18,278 | -2,649 | -12.7% |
| Homeless Person Assistance | 39,420 | 37,171 | -2,249 | -5.7% |

## Night-Weighted High-Volume Reasons

| Complaint type | Requests | Night share | Weekend share | Peak time |
| --- | --- | --- | --- | --- |
| Noise - Commercial | 200,054 | 63.6% | 48.4% | 23:00 |
| Noise - Street/Sidewalk | 483,499 | 51.0% | 44.8% | 22:00 |
| Noise - Residential | 1,141,098 | 46.5% | 41.5% | 23:00 |
| Noise - Vehicle | 143,313 | 41.7% | 37.6% | 22:30 |
| Noise | 163,955 | 27.0% | 24.2% | 09:30 |
| Illegal Parking | 1,559,794 | 21.0% | 26.9% | 08:00 |
| Blocked Driveway | 509,345 | 20.7% | 28.9% | 09:00 |
| HEAT/HOT WATER | 812,019 | 19.3% | 26.0% | 09:30 |
| Homeless Person Assistance | 116,157 | 19.0% | 23.6% | 08:30 |
| Non-Emergency Police Matter | 71,396 | 17.3% | 27.0% | 13:30 |
| Traffic Signal Condition | 129,490 | 15.9% | 18.8% | 14:00 |
| Rodent | 112,786 | 15.1% | 21.2% | 10:30 |

## Business-Hour Weighted High-Volume Reasons

| Complaint type | Requests | Business-hour share | Peak time |
| --- | --- | --- | --- |
| Sidewalk Condition | 73,811 | 63.3% | 11:30 |
| Overgrown Tree/Branches | 62,234 | 62.7% | 10:30 |
| APPLIANCE | 67,324 | 61.0% | 11:30 |
| FLOORING/STAIRS | 80,777 | 60.8% | 10:30 |
| PAINT/PLASTER | 185,015 | 59.7% | 11:30 |
| General Construction/Plumbing | 110,174 | 57.2% | 11:00 |
| DOOR/WINDOW | 137,314 | 56.3% | 10:30 |
| GENERAL | 95,386 | 55.0% | 10:30 |
| UNSANITARY CONDITION | 355,293 | 53.0% | 10:30 |
| PLUMBING | 207,846 | 52.4% | 11:00 |
| WATER LEAK | 129,775 | 52.1% | 10:30 |
| Lead | 54,981 | 51.8% | 10:30 |

## Most Seasonal High-Volume Reasons

| Complaint type | Total | Avg month | Max month | Max/avg month |
| --- | --- | --- | --- | --- |
| Lead | 54,981 | 1527.25 | 9,103 | 5.96 |
| Drug Activity | 70,451 | 1956.97 | 6,038 | 3.09 |
| HEAT/HOT WATER | 788,674 | 22533.54 | 67,229 | 2.98 |
| Noise - Helicopter | 108,367 | 3010.19 | 8,724 | 2.90 |
| Water System | 196,944 | 5470.67 | 15,197 | 2.78 |
| Overgrown Tree/Branches | 62,234 | 1728.72 | 4,146 | 2.40 |
| Damaged Tree | 90,751 | 2520.86 | 6,043 | 2.40 |
| Noise - Residential | 1,141,098 | 31697.17 | 70,837 | 2.23 |
| Sewer | 82,366 | 2287.94 | 4,973 | 2.17 |
| Maintenance or Facility | 70,645 | 1962.36 | 4,154 | 2.12 |
| WATER LEAK | 123,744 | 3535.54 | 7,332 | 2.07 |
| Noise - Street/Sidewalk | 483,499 | 13430.53 | 25,205 | 1.88 |

## Volatile High-Volume Reasons

| Complaint type | Requests | CV active day | Max day | Peak time |
| --- | --- | --- | --- | --- |
| Lead | 54,981 | 1.96 | 1,777 | 10:30 |
| Sewer | 82,366 | 1.30 | 2,176 | 10:00 |
| HEAT/HOT WATER | 812,019 | 1.07 | 5,313 | 09:30 |
| Water System | 196,944 | 1.04 | 3,442 | 14:30 |
| Damaged Tree | 90,751 | 0.98 | 1,041 | 10:00 |
| Noise - Helicopter | 108,367 | 0.97 | 621 | 17:30 |
| WATER LEAK | 129,775 | 0.96 | 3,194 | 10:30 |
| Noise - Street/Sidewalk | 483,499 | 0.81 | 2,114 | 22:00 |
| Overgrown Tree/Branches | 62,234 | 0.81 | 370 | 10:30 |
| Drug Activity | 70,451 | 0.76 | 406 | 11:30 |
| Graffiti | 57,197 | 0.69 | 389 | 11:30 |
| Noise - Residential | 1,141,098 | 0.69 | 6,559 | 23:00 |

## Peak-Shaped High-Volume Reasons

| Complaint type | Requests | Peak time | Peak half-hour share | Max day |
| --- | --- | --- | --- | --- |
| Missed Collection | 131,840 | 08:00 | 13.2% | 345 |
| Noise - Commercial | 200,054 | 23:00 | 7.8% | 681 |
| Traffic Signal Condition | 129,490 | 14:00 | 6.8% | 598 |
| Noise - Street/Sidewalk | 483,499 | 22:00 | 6.5% | 2,114 |
| Obstruction | 57,165 | 07:00 | 5.7% | 147 |
| Vendor Enforcement | 69,051 | 12:00 | 5.6% | 164 |
| Street Condition | 205,582 | 14:30 | 5.6% | 426 |
| Overgrown Tree/Branches | 62,234 | 10:30 | 5.4% | 370 |
| Noise - Residential | 1,141,098 | 23:00 | 5.2% | 6,559 |
| Sidewalk Condition | 73,811 | 11:30 | 5.1% | 152 |
| FLOORING/STAIRS | 80,777 | 10:30 | 5.0% | 313 |
| APPLIANCE | 67,324 | 11:30 | 4.9% | 221 |

## Top Outlier Dates

| Date | Requests | Top reason | Top reason requests | Top reason share |
| --- | --- | --- | --- | --- |
| 2023-09-29 | 17,962 | Water Leak | 3,194 | 17.8% |
| 2025-12-15 | 16,388 | HEAT/HOT WATER | 3,569 | 21.8% |
| 2024-04-15 | 15,899 | HEAT/HOT WATER | 2,386 | 15.0% |
| 2025-01-07 | 15,023 | HEAT/HOT WATER | 3,659 | 24.4% |
| 2025-01-09 | 14,906 | Noise - Residential | 3,620 | 24.3% |
| 2024-09-15 | 14,585 | Noise - Residential | 6,559 | 45.0% |
| 2024-11-19 | 14,547 | Noise - Residential | 3,654 | 25.1% |
| 2024-12-16 | 14,536 | Noise - Residential | 5,590 | 38.5% |
| 2025-01-10 | 14,220 | Noise - Residential | 4,770 | 33.5% |
| 2025-01-06 | 14,141 | Noise - Residential | 4,449 | 31.5% |
| 2025-06-24 | 14,079 | Water System | 3,442 | 24.4% |
| 2025-12-09 | 14,078 | HEAT/HOT WATER | 3,657 | 26.0% |
| 2025-12-16 | 13,946 | HEAT/HOT WATER | 2,627 | 18.8% |
| 2025-10-31 | 13,908 | Construction Safety Enforcement | 2,110 | 15.2% |
| 2024-11-20 | 13,821 | Noise - Residential | 3,860 | 27.9% |

## Top Outlier Intervals With Dominant Reason

| Interval | Day | Requests | Top reason | Reason requests | Reason share |
| --- | --- | --- | --- | --- | --- |
| 2023-03-22 17:30:00 | Wednesday | 1,318 | New Tree Request | 573 | 43.5% |
| 2023-09-29 10:00:00 | Friday | 1,059 | WATER LEAK | 248 | 23.4% |
| 2023-09-29 09:00:00 | Friday | 1,040 | Water Leak | 230 | 22.1% |
| 2023-09-29 10:30:00 | Friday | 983 | WATER LEAK | 248 | 25.2% |
| 2023-09-29 09:30:00 | Friday | 944 | Water Leak | 238 | 25.2% |
| 2023-07-04 21:00:00 | Tuesday | 834 | Illegal Fireworks | 507 | 60.8% |
| 2023-09-29 08:30:00 | Friday | 811 | Water Leak | 163 | 20.1% |
| 2025-06-13 17:00:00 | Friday | 795 | UNSANITARY CONDITION | 118 | 14.8% |
| 2025-07-04 22:00:00 | Friday | 783 | Illegal Fireworks | 418 | 53.4% |
| 2023-07-04 23:00:00 | Tuesday | 768 | Illegal Fireworks | 305 | 39.7% |
| 2023-07-04 22:00:00 | Tuesday | 761 | Illegal Fireworks | 352 | 46.3% |
| 2024-07-04 21:00:00 | Thursday | 755 | Illegal Fireworks | 482 | 63.8% |

## Illegal Fireworks Spike Dates

| Date | Requests |
| --- | --- |
| 2025-07-04 | 3,136 |
| 2023-07-04 | 2,759 |
| 2024-07-04 | 2,747 |
| 2025-07-05 | 1,714 |
| 2024-07-05 | 1,261 |
| 2023-07-05 | 1,173 |
| 2025-07-03 | 631 |
| 2024-07-03 | 585 |
| 2024-07-06 | 583 |
| 2023-07-03 | 560 |
| 2025-07-06 | 529 |
| 2023-07-02 | 401 |

## Operational Leads

1. **Reason mix changes the staffing profile.** Illegal Parking, Noise - Residential, HEAT/HOT WATER, Blocked Driveway, and Noise - Street/Sidewalk lead total volume and peak at different times.
2. **HEAT/HOT WATER requires seasonal capacity.** November through March accounts for 79.5% of its volume.
3. **Noise demand requires evening coverage.** Night shares reach 63.6% for commercial noise, 51.0% for street noise, and 46.5% for residential noise.
4. **Recurring peaks cover a limited share of the week.** The top 10 weekday/half-hour cells account for 4.9% of weekly arrivals, leaving a broad base requirement.
5. **Customer deployment should connect reasons with effort.** Local AHT and disposition data would convert reason-level demand into workload and staffing requirements.
