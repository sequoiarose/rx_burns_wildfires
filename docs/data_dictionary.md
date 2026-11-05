# Data Dictionary

This file documents the datasets in `data/processed/`. The main one is
**`prescribed_treatment_data_new_clean.csv`**, the dataset behind the thesis regression analysis (Chapter 6).
A machine-readable version with one row per column (type, units, source, missing count, summary
statistics) is in [`data_dictionary_prescribed_treatment_data_new_clean.csv`](data_dictionary_prescribed_treatment_data_new_clean.csv).

All three processed files can be rebuilt from `data/raw/` with `01_dataset_creation.ipynb`, and the rebuild
matches the canonical files exactly.

---

## 1. `prescribed_treatment_data_new_clean.csv`

| | |
|---|---|
| **Unit of observation** | One wildfire incident recorded by CAL FIRE |
| **Rows × columns** | 1,992 × 82 (plus an unnamed row-index column: read with `pd.read_csv(..., index_col=0)`) |
| **Time span** | 2013-02-24 to 2022-10-23 (fire start dates) |
| **Space** | California only (fires whose point falls outside a California county were removed) |
| **Built by** | `01_dataset_creation.ipynb` (all columns; `max_wind` corrected 2026-11, see below) |
| **Used by** | `05_modeling.ipynb` |

### How a row is built
1. **Wildfire** (CAL FIRE incident list `data/raw/calfire/mapdataall.csv`): date, name, county, acres, point location.
2. **Climate**: NOAA *Climate at a Glance* county series (`data/raw/noaa_climate/climate_data.xlsx`) for the
   **calendar month before** the fire month, averaged across the counties CAL FIRE lists for the incident.
   For the 35 fires with no county listed, the statewide value is used (`monthly_climate_data.csv`).
3. **Prescribed fire exposure**: CAL FIRE prescribed burn perimeters
   (`data/raw/prescribed_burns/California_Fire_Perimeters_(all).geojson`), each represented by its polygon
   centroid and `TREATED_AC`. These give 60 columns: 6 look-back windows × 5 radii × {indicator, acres}.
4. **Location labels**: point-in-polygon county, a "multiple" flag for multi-county fires, and one of 8 regions.
5. **Cleaning**: removed fires with missing acres or outside California.

### Column groups

#### Identifiers and wildfire outcome (CAL FIRE)
| Column | Type | Units | Description |
|---|---|---|---|
| *(unnamed index)* | int | – | Row number 0…1991. Not an ID. |
| `ex_date` | datetime, UTC | – | Fire start: `incident_date_created` (falls back to `incident_date_extinguished`). Used as the fire date everywhere. |
| `incident_name` | str | – | CAL FIRE incident name. **Not unique**, so don't use it as a key. |
| `incident_county` | str | – | County as reported; comma-separated for multi-county fires (`"Napa, Lake"`). Missing values were filled with `county`. |
| `incident_acres_burned` | float | acres | Final reported size. Median 101, max 1,032,648 (2020 August Complex). 23 fires are 0 acres. |
| `incident_longitude`, `incident_latitude` | float | decimal degrees | Reported incident point (origin), not a centroid or perimeter. |
| `incident_type` | str | – | Raw CAL FIRE field, mostly missing (1,212/1,992). Values: Wildfire, Fire, Flood (1). Not used. |
| `log_incident_acres_burned` | float | ln(acres) | `ln(incident_acres_burned)`, set to **0 when acres = 0**, so 0- and 1-acre fires both get 0. **Response variable** in Chapter 6. `05_modeling` drops the 0 rows (leaving 1,969). |

#### Climate (NOAA NCEI Climate at a Glance, month before the fire)
| Column | Units | Description |
|---|---|---|
| `tavg` | °F | Mean temperature |
| `tmax` | °F | Mean daily maximum temperature |
| `tmin` | °F | Mean daily minimum temperature |
| `pcp` | inches | Total precipitation |
| `cdd` | °F degree-days | Cooling degree days (base 65 °F) |
| `hdd` | °F degree-days | Heating degree days (base 65 °F) |
| `pdsi` | index | Palmer Drought Severity Index (< 0 drought, ≤ −4 extreme) |
| `phdi` | index | Palmer Hydrological Drought Index |
| `pmdi` | index | Palmer Modified Drought Index |
| `zndx` | index | Palmer Z-Index: moisture anomaly *of that month* (short-term dryness) |

Notes: these are **county-month averages**, not fire-location values. For multi-county fires they are the
unweighted mean over the listed counties. In the thesis models `tmax` is highly collinear with
latitude/longitude (VIF ≈ 111 before predictor reduction).

#### Prescribed-fire exposure (60 columns)
Column names follow the pattern

```
prescribed_{T}_months_in_{R}km     bool   at least one qualifying prescribed burn
prescribed_{T}_months_size_{R}km   float  total TREATED_AC (acres) of qualifying burns
T ∈ {3, 6, 9, 12, 24, 36}     R ∈ {5, 10, 25, 50, 100}
```

A prescribed burn **qualifies** for fire *i* when both conditions hold:

* **Time:** `0 < months(fire) − months(burn START_DATE) ≤ T`, counting whole calendar months
  (year × 12 + month). Burns that started in the same calendar month as the fire are **excluded**.
  A "3-month" window for a fire on 15 Aug includes burns that started 1 May to 31 Jul.
* **Space:** the geodesic (WGS-84) distance from the fire's reported point to the burn polygon's
  **centroid** is ≤ R km.

The windows are nested: `in` for (T, R) implies `in` for every larger T or R, and `size` never decreases as T or R grows.

**Share of fires with `in = True`:**

|       | 5 km   | 10 km   | 25 km   | 50 km   | 100 km   |
|:------|:-------|:--------|:--------|:--------|:---------|
| 3 mo  | 2%     | 7%      | 29%     | 56%     | 79%      |
| 6 mo  | 4%     | 12%     | 44%     | 74%     | 93%      |
| 9 mo  | 5%     | 15%     | 51%     | 82%     | 98%      |
| 12 mo | 7%     | 19%     | 57%     | 86%     | 98%      |
| 24 mo | 10%    | 26%     | 68%     | 92%     | 100%     |
| 36 mo | 12%    | 32%     | 73%     | 95%     | 100%     |

At 100 km and ≥ 9 months nearly every fire counts as "treated", so these columns have almost no contrast.
The thesis models use `log_prescribed_3_months_size_50km` (created in `05_modeling` as ln(acres), 0 when 0).

Caveats for the prescribed-fire columns:
* **1,736 of the 8,473 burn records (20%) have no `START_DATE`**, so they are excluded from all of these columns.
* All `TREATMENT_TYPE`s are included: broadcast burns as well as pile burns, which have much less landscape effect.
  The burn layer codes types 1–5; check the CAL FIRE FRAP metadata for the labels before filtering.
* A centroid-to-point distance ignores the burn's size and shape. A large burn adjacent to a fire can have its
  centroid more than 5 km away.
* `TREATED_AC` (reported acres) is used, not `GIS_ACRES` (polygon area).

#### Location labels (derived)
| Column | Description |
|---|---|
| `county` | County polygon containing the fire point (`data/raw/boundaries/California_County_Boundaries.geojson`). |
| `county_new` | `incident_county`, or `"multiple"` when more than one county is listed (42 fires). |
| `region` | 8 levels, assigned from `county_new` using the mapping below. Row counts: Central Valley 428, Central Coast 338, Shasta Cascades 330, Sierras 256, Desert 246, South Coast 186, North Coast 166, Multiple 42. |

Region mapping (as actually applied):

| Region | Counties present in the data |
|---|---|
| North Coast | Del Norte, Humboldt, Lake, Marin, Mendocino, Napa, Sonoma |
| Shasta Cascades | Butte, Lassen, Modoc, Shasta, Siskiyou, Trinity |
| Central Valley | Colusa, Fresno, Glenn, Kern, Kings, Madera, Merced, Placer, Sacramento, San Joaquin, Solano, Stanislaus, Sutter, Tehama, Yolo, Yuba |
| Sierras | Alpine, Amador, Calaveras, El Dorado, Inyo, Mariposa, Mono, Nevada, Plumas, Sierra, Tulare, Tuolumne |
| Central Coast | Alameda, Contra Costa, Monterey, San Benito, San Luis Obispo, San Mateo, Santa Barbara, Santa Clara, Santa Cruz, Ventura |
| South Coast | Los Angeles, Orange, San Diego |
| Desert | Imperial, Riverside, San Bernardino |
| Multiple | any multi-county fire |

The mapping dict in the code lists Trinity, Tehama and Plumas under two regions; the later entry wins (as shown above).
"San Francisco" is misspelled in the dict, but no fire in the data is in San Francisco.

#### Wind (Open-Meteo)
| Column | Units | Description |
|---|---|---|
| `max_wind` | km/h | Maximum 10 m wind speed on the **local (Pacific) calendar day the fire started**, at the reported fire point. From the Open-Meteo historical archive (ERA5-based reanalysis), `daily=wind_speed_10m_max`, `timezone=America/Los_Angeles`. Raw download cached in `data/raw/open_meteo/max_wind_fire_date.csv`. |

> **Corrected November 2026: this column differs from the submitted thesis.** The 2024 download used
> `date = df["ex_date"][0]` (the first fire's date, 2013-02-24) for every row, so the old values depended only on
> location. `01_dataset_creation.ipynb` now downloads the wind for each fire's own date and is the code that produced
> the current values. The 2024 file is kept as `old/data/prescribed_treatment_data_new_clean_2024_buggy_wind.csv`.
> Every other column is unchanged. This is still a single daily maximum at the ignition point, not the wind during
> the fire's spread; see `docs/FUTURE_WORK.md` (task 0.1) for better fire-weather covariates.

---

## 2. `prescribed_treatment_data_new.csv`

Earlier version of the same table: **2,041 rows × 81 columns**. It is used by `03_treatment_analysis.ipynb` (Table 4.5).
Differences from the clean file:
* still includes the 49 fires with missing acres (NaN `incident_acres_burned`) or no matching California county;
* no `max_wind` column;
* booleans are stored as `TRUE`/`FALSE` and some integers without decimals, so read it with pandas rather than by eye.

---

## 3. `monthly_data.csv`

Statewide monthly time series used in `02_dataset_exploration.ipynb` and `04_time_series_analysis.ipynb` (Chapter 5).

| | |
|---|---|
| **Unit** | One calendar month, California statewide |
| **Rows** | 120 (2013-01 to 2022-12; index = month-end timestamp in UTC) |

| Column | Units | Description |
|---|---|---|
| *(index)* | date | Month end, e.g. `2013-01-31 00:00:00+00:00` |
| `rx_acres` | acres | Total `TREATED_AC` of prescribed burns that **started** in the month |
| `rx_acres_3_month` | acres | Prescribed acres summed over the month-end dates from 4 months back to 1 month back (`.loc` is inclusive at both ends, so this covers **4** monthly values). The same applies to the next three columns. |
| `rx_acres_6_month` | acres | Same, from 7 months back to 1 month back |
| `rx_acres_9_month` | acres | Same, from 10 months back to 1 month back |
| `rx_acres_12_month` | acres | Same, from 13 months back to 1 month back |
| `incident_acres_burned` | acres | Total acres of CAL FIRE wildfires that **started** in the month (attributed entirely to the start month) |
| `cdd`, `hdd`, `pcp`, `pdsi`, `phdi`, `pmdi`, `tavg`, `tmax`, `tmin`, `zndx` | as above | **Statewide** NOAA values for the *same* month (not lagged) |

Months with no fires have 0, not NaN. The wildfire series is extremely heavy-tailed (a few months
dominate), so the thesis analyses use `log_acres = ln(incident_acres_burned)`, set to 0 when acres = 0.

---

## 4. Raw sources (for reference)

| File | Source | Notes |
|---|---|---|
| `data/raw/calfire/mapdataall.csv` | CAL FIRE incidents, https://incidents.fire.ca.gov/imapdata/mapdataall.csv | Downloaded 2024. The live file changes, so keep this copy for reproducibility. |
| `data/raw/prescribed_burns/California_Fire_Perimeters_(all).geojson` | CAL FIRE prescribed burns, https://data.ca.gov/dataset/prescribed-burns | 8,473 polygons; fields: `TREATMENT_ID`, `TREATMENT_TYPE`, `AGENCY` (USF, CDF, NPS, …), `START_DATE`, `END_DATE`, `TREATED_AC`, `GIS_ACRES`, … |
| `data/raw/noaa_climate/climate_data.xlsx` | NOAA NCEI Climate at a Glance, county time series | One sheet per variable, one column per county (`"Alameda County"`, …), monthly 2012-01 to 2023-12. Compiled by hand from the county download pages. |
| `data/raw/noaa_climate/monthly_climate_data.csv` | NOAA Climate at a Glance, statewide | Monthly 2012-01 to 2023-12. Built from the files in `statewide_series/`. |
| `data/raw/boundaries/California_County_Boundaries.geojson` | California county boundaries | Field `COUNTY_NAME`. |

See [`data/README.md`](../data/README.md) for the complete inventory, including unused candidate datasets.
