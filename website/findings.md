---
title: Findings
subtitle: Main results by chapter of the thesis, with the 2026 updates
---

This page summarizes the results. Each section links to the notebook that produces it, where the full tables and
code are.

## 1. Wildfires and prescribed fires, 2013–2022

*Notebook: [02 — Dataset Exploration](../02_dataset_exploration.ipynb)*

Wildfires happen mostly in summer (half of them in June–August), while prescribed burns are concentrated in
winter and spring, the burn windows when conditions are safe. Prescribed burning grew sharply after 2018.

:::{figure} images/rx_vs_wild.png
:label: fig-seasonality
Number of wildfires (red) and prescribed fires (blue) by month and by year.
:::

::::{grid} 1 1 2 2
:::{figure} images/acres.png
:label: fig-sizes
Size distributions. The median wildfire is 101 acres, the largest is 1,032,648 acres (2020 August Complex), and the
median prescribed burn is 22 acres.
:::
:::{figure} images/rx_vs_wild_acres.png
:label: fig-annual
Total acres per year on a log scale. Wildfire acreage swings by orders of magnitude from year to year; prescribed
acreage is far smaller.
:::
::::

Chi-squared tests show that both wildfire and prescribed-fire counts depend on region × year (*p* < 10⁻⁵), i.e. the
geography of fire changes from year to year. The region × year residual plots are in the notebook.

## 2. Are fires with a prior nearby prescribed burn smaller?

*Notebook: [03 — Treatment Analysis](../03_treatment_analysis.ipynb)*

Each wildfire is labelled "treated" if a prescribed burn occurred within *R* km in the previous *T* months, and
one-sided Mann–Whitney U tests compare the sizes of treated and untreated fires.

```{figure} images/bp_3m.png
:label: fig-bp3
Wildfire size for fires with and without a prescribed burn in the previous 3 months, at four radii.
```

* At **3 months**, treated fires are smaller at every radius (10 km: *p* = 0.002; 50 km: *p* < 0.001). The common-language
  effect size is 0.53–0.57: a treated fire is smaller than an untreated one 53–57% of the time.
* At **50 km** treated fires are significantly smaller for every window from 3 to 36 months, and at **10 km** for every
  window up to 24 months. Results at 25 and 100 km are mixed. At 5 km very few fires are treated and no test is significant.
* These are many tests without multiple-comparison correction, and the comparison does not adjust for location or
  climate. The models in Section 4 do.

## 3. The statewide monthly picture

*Notebook: [04 — Time Series Analysis](../04_time_series_analysis.ipynb)*

Adding everything up by month across the state, wildfire acreage tracks the climate, not prescribed burning.

```{figure} images/cross_correlation.png
:label: fig-ccf
Cross-correlation between monthly log wildfire acres and each predictor at lags 0–23 months.
```

| Predictor | Strongest correlation with log wildfire acres |
|---|---|
| Maximum temperature | *r* = 0.79 in the same month |
| Precipitation | *r* = −0.64 in the same month |
| Palmer Z-index (dryness) | *r* = −0.19 in the same month |
| Prescribed acres | *r* = 0.15 at a 20-month lag, −0.08 at 2 months: no clear relationship |

## 4. Regression models for individual fires

*Notebook: [05 — Regression Modeling](../05_modeling.ipynb)*

The response is log acres burned (1,969 fires larger than one acre; 80/20 train/test split stratified by region). After
removing collinear predictors with variance inflation factors, the models use precipitation, maximum temperature,
fire-day maximum wind, and **log prescribed acres within 50 km in the previous 3 months**.

### Separate regressions for each region

```{figure} images/region_coef.png
:label: fig-region
Standardized coefficients from separate linear regressions in each region (\* *p* < 0.1, \*\* *p* < 0.05, \*\*\* *p* < 0.01).
```

The prescribed-fire coefficient is **negative in every region**: more prior nearby prescribed burning goes with
smaller fires. It is significant (*p* < 0.05) in the Central Coast, Central Valley, Desert and Sierras, and
*p* = 0.056 in the Shasta Cascades. Precipitation is significantly negative in the Shasta Cascades, Sierras and South
Coast. Temperature effects vary in sign between regions. Wind is significant only in the South Coast (*p* = 0.018).

### Pooled models

| Model | Prescribed-fire coefficient | Notes |
|---|---|---|
| Linear regression with region interactions | −0.34 (*p* < 0.001) | Significant (*p* < 0.05) region interactions: Sierras × precipitation, South Coast × precipitation and × temperature; no significant wind terms |
| Linear mixed model (random intercept and slopes by region) | −0.26 (*p* < 0.001) | Precipitation −0.27 (*p* < 0.001) |

```{figure} images/lmm_partial_regression.png
:label: fig-lmm
Linear mixed model: observed log acres against each predictor, with region-specific fitted lines.
```

### Predictive comparison

```{figure} images/mse_results.png
:label: fig-mse
Training and test mean squared error (log acres) for each model.
```

| Model | Train MSE | Test MSE |
|---|---|---|
| Null (intercept only) | 4.209 | 4.857 |
| Linear regression | 3.480 | 4.520 |
| Linear mixed model | 5.056 | 5.364 |
| KNN | 0.000 | 4.730 |
| SVM (linear kernel) | 3.592 | 4.712 |
| **Random forest** | 0.481 | **4.168** |
| AdaBoost | 3.753 | 4.713 |

The random forest has the lowest test error, but every model improves only modestly on the null model. Fire size is
driven largely by things not in this dataset: fuels, terrain, fire-day weather, and suppression.

## Changes since the thesis

In November 2026 the project was cleaned up for a new student, and every result was re-checked by re-running all of
the notebooks from the raw data. Two problems were found and fixed.

**1. The wind variable.** The original download of fire-day wind used the *first* fire's date (24 Feb 2013) for every
fire, so the old variable described location rather than weather (it correlates only 0.20 with the correct values).
After the fix:

| Result | Thesis (2024) | Corrected (2026) |
|---|---|---|
| Linear regression: prescribed fire | −0.346, *p* < 0.001 | −0.336, *p* < 0.001 |
| Linear regression: region × wind terms with *p* < 0.05 | 3 | none |
| Mixed model: prescribed fire | −0.248, *p* < 0.001 | −0.257, *p* < 0.001 |
| Mixed model: wind random-slope variance | 0.185 | 0.019 |
| Random forest test MSE | 4.216 | 4.168 |

The prescribed-fire result held, but the regional wind effects reported in the thesis were artefacts of the bug.

**2. Significance stars in the regional coefficient plot (thesis Fig. 6.1).** The stars were matched to the bars in the
wrong order, so 19 of the 32 were drawn on the wrong bar. The coefficients themselves were correct, and the figure
above has the stars in the right places.

Everything else (Chapters 3–5, Table 4.5 and the time-series results) reproduces the thesis. See
[Reproducibility](reproducibility.md) for the details and the remaining open questions.
