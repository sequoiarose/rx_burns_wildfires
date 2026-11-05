---
title: Prescribed Fire and Wildfire Size in California
short_title: Overview
subtitle: Do prescribed burns go with smaller wildfires? A data-fusion study of California, 2013–2022
---

+++ {"part": "abstract"}
Large, destructive wildfires are becoming more frequent in California, and prescribed (Rx) burning is one of the main
tools for reducing that risk. This project builds a new dataset that links **1,992 CAL FIRE wildfires** to the
**prescribed burns** that occurred near them in the months before ignition and to **NOAA climate conditions** in the
month before the fire. It then uses descriptive and inferential statistics, time-series analysis, and regression and
machine-learning models to ask whether prior prescribed burns are associated with smaller wildfires once climate is
accounted for.
+++

:::{figure} website/images/rx_wild_map_2017_2020.png
:label: fig-map
:width: 80%
Prescribed burns (blue) and the wildfires that followed them over the next three years (red, orange, yellow), sized by
area burned. Each panel starts from one year of prescribed burns.
:::

## Key findings

::::{grid} 1 1 2 2

:::{card} Individual fires: Rx burns go with smaller wildfires
A wildfire with more prescribed-burn acres within **50 km in the previous 3 months** tends to be smaller, even after
adjusting for precipitation, temperature, wind and region (standardized coefficient −0.34, *p* < 0.001; a mixed
model with region effects gives −0.26).
:::

:::{card} Statewide: no detectable effect
Added up across the whole state by month, prescribed acres do not predict wildfire acres. The effect only appears at
the level of individual fires and their neighbourhoods.
:::

:::{card} Climate matters more
Statewide, monthly precipitation is strongly correlated with wildfire acres (*r* = −0.64 with log acres) while
prescribed acres are not. For individual fires, precipitation in the month before ignition is as strong a predictor as
prescribed fire in the mixed model (−0.27 vs −0.26).
:::

:::{card} Predicting fire size is hard
The best model (random forest) improves held-out error only modestly over a no-predictor baseline (test MSE on
log-acres 4.17 vs 4.86). Most of the variation in wildfire size is not explained by these covariates.
:::

::::

```{figure} website/images/bp_3m.png
:label: fig-bp
:width: 85%
Distribution of wildfire size for fires with (True) and without (False) a prescribed burn within 10, 25, 50 and 100 km in
the previous three months. One-sided Mann–Whitney tests find the "with" group smaller at every radius (*p* < 0.001 to
0.044; common-language effect size 0.53–0.57).
```

## Explore the project

::::{grid} 1 1 2 3

:::{card} Findings
:link: website/findings.md
The main results and figures from each chapter, with how they changed after the 2026 data fixes.
:::

:::{card} Data
:link: docs/data_dictionary.md
How the wildfire–prescribed fire–climate dataset is built, with a dictionary of all 82 columns.
:::

:::{card} Analysis notebooks
:link: 01_dataset_creation.ipynb
Five Jupyter notebooks, from building the dataset to the models, with all outputs.
:::

:::{card} Reproducibility
:link: website/reproducibility.md
Environment, how to run everything, and what has been checked to reproduce.
:::

:::{card} Future work
:link: docs/FUTURE_WORK.md
Next steps: spatio-temporal quantile regression and distilled conditional randomization tests.
:::

:::{card} Thesis (PDF)
:link: thesis_documents/thesis_final.pdf
*A Statistical Analysis of Wildland and Prescribed Fires in the Changing California Environment*. M.S. in
Statistical Data Science, San Francisco State University, May 2024.
:::

::::

## The dataset at a glance

| | |
|---|---|
| Wildfires | 1,992 CAL FIRE incidents, Feb 2013 – Oct 2022 |
| Prescribed burns | 8,473 CAL FIRE burn perimeters (USFS, CAL FIRE, NPS, BLM, …) |
| Climate | NOAA *Climate at a Glance*: county-level temperature, precipitation and Palmer drought indices for the month before each fire |
| Weather | Fire-day maximum 10 m wind speed (Open-Meteo / ERA5) |
| Prescribed-fire exposure | Burn acres within 5, 10, 25, 50 and 100 km over the previous 3, 6, 9, 12, 24 and 36 months (60 features) |

**Methods:** Mann–Whitney U tests, chi-squared tests of independence, cross-correlation of monthly time series,
regional and pooled OLS with region interactions, linear mixed-effects models, KNN, SVM, random forests and AdaBoost.

**Tools:** Python (pandas, GeoPandas, statsmodels, scikit-learn, pingouin, cartopy).

:::{note} About this version
The analysis was revisited in November 2026. The dataset is now rebuilt from raw data in about 25 seconds instead of
5.5 hours. A bug in the wind variable was fixed, which changed some Chapter 6 results; the prescribed-fire finding
held. See [Findings](website/findings.md#changes-since-the-thesis) for the details.
:::
