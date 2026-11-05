# Data inventory

Column-level documentation for the processed datasets is in [`../docs/data_dictionary.md`](../docs/data_dictionary.md).

## `processed/`: datasets used in the thesis
| File | Rows | Used by | Description |
|---|---|---|---|
| `prescribed_treatment_data_new_clean.csv` | 1,992 | `05_modeling` | **Main dataset.** One row per wildfire: climate, prescribed-fire exposure, region, `max_wind` |
| `prescribed_treatment_data_new.csv` | 2,041 | `03_treatment_analysis` | Same table before the final cleaning, without `max_wind` |
| `monthly_data.csv` | 120 | `02`, `04` | Statewide monthly wildfire and Rx acres with statewide climate |
| `rebuilt/` | | | Written by `01_dataset_creation`. Rebuilt copies, used to check the canonical files. Safe to delete and regenerate. |

## `raw/`: original downloads (inputs to `01_dataset_creation`)
| Path | Source | Used? |
|---|---|---|
| `calfire/mapdataall.csv` | CAL FIRE incident list, https://incidents.fire.ca.gov/imapdata/mapdataall.csv (2024 snapshot) | **Yes**: wildfires |
| `calfire/California_Fire_Incidents.csv` | Older CAL FIRE incident export (2013–2019, Kaggle-style columns) | No |
| `prescribed_burns/California_Fire_Perimeters_(all).geojson` | CAL FIRE prescribed burns, https://data.ca.gov/dataset/prescribed-burns | **Yes**: Rx burns |
| `prescribed_burns/California_Fire_Perimeters_(all).csv` | Attribute table of the same layer (no geometry) | No |
| `prescribed_burns/ds397.zip` | File geodatabase (`ds397.gdb`) of a CA prescribed-fire layer, 2022 download | No |
| `noaa_climate/climate_data.xlsx` | NOAA Climate at a Glance, **county** monthly series; one sheet per variable (`tavg, tmax, tmin, pcp, cdd, hdd, pdsi, phdi, pmdi, zndx`), 2012–2023 | **Yes** |
| `noaa_climate/monthly_climate_data.csv` | NOAA Climate at a Glance, **statewide** monthly, 2012–2023 | **Yes** |
| `noaa_climate/statewide_series/*.csv` | Individual statewide downloads (value + anomaly) that `monthly_climate_data.csv` was assembled from | Provenance only |
| `open_meteo/max_wind_fire_date.csv` | Open-Meteo historical weather API: daily max 10 m wind (km/h) for each fire's (lat, lon, local start date), downloaded Nov 2026 by `01_dataset_creation` | **Yes**: `max_wind` |
| `boundaries/California_County_Boundaries.geojson` | California county polygons (`COUNTY_NAME`) | **Yes** |
| `boundaries/USA.*` | US states shapefile (`state_code`) | Only by the gridded-climate helpers in `functions.py` |
| `gridded_climate/precipitation_gpcp/` | NOAA GPCP v2.3 monthly precipitation, 2.5° grid, 2015–2022 (one NetCDF per month) | Exploration only (`functions.get_precip_monthly`) |
| `gridded_climate/temperature_anomaly/` | NASA GISTEMP (250 km smoothing, land+ocean) 2° monthly temperature anomaly 1880–2023-03, plus 1991–2020 climatology | Exploration only (`functions.get_monthly_temp`) |
| `gridded_climate/soil_moisture/` | NOAA CPC monthly soil moisture 1948–2023-03 (`soilw.mon.mean.nc`) + land masks | Exploration only (`functions.get_monthly_soil`) |

## `other_candidates/`: evaluated in thesis Table 3.1, not used in the final analysis
| Path | Description |
|---|---|
| `ics209plus-wildfire/` | ICS-209-PLUS v2 (1999–2020): incident and situation reports for large US wildfires (St. Denis et al.). 349 MB. |
| `SNFDP_firecompetition.csv` | Sequoia National Forest Demography Plots: post-fire tree mortality, neighbours, crown scorch |
| `tree_mortality/` | USGS: tree mortality in Sequoia NP, 2004–2007 and the 2014–2017 drought (with XML metadata) |
| `seed/`, `seed_early/` | USGS: long-term seedling, seed and tree data, Sequoia & Yosemite NPs (with XML metadata) |
| `forest_structure/` | USGS: forest structure in burned and unburned sites, Sequoia & Kings Canyon NPs (with XML metadata) |

Superseded intermediate datasets are in `../old/data/` (see `../old/README.md`).
