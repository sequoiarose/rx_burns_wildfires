# Prescribed Burns and Wildfire Size in California (2013–2022)

Code and data for the master's thesis *thesis_final.pdf* (Sequoia Andrade, 2024), which studies whether
prescribed (Rx) fire before a wildfire, near where it starts, is associated with a smaller wildfire, after
accounting for climate and region.

The repository was cleaned up and documented in November 2026 for the student continuing the work. Every
notebook runs top to bottom and the thesis results reproduced, except Chapter 6, which now differs on purpose
because a bug in the wind variable was fixed (see [Changes since the thesis](#changes-since-the-thesis)).

**Start here**
1. Read `thesis_documents/thesis_final.pdf`, Chapters 3–6.
2. Set up the environment (below) and run the notebooks in order.
3. Read [`docs/data_dictionary.md`](docs/data_dictionary.md) and the [Known issues](#known-issues) below.
4. Read the plan for next steps: [`docs/FUTURE_WORK.md`](docs/FUTURE_WORK.md) (spatio-temporal quantile regression and the distilled CRT).

**Website:** the project is also published as a MyST site (see [Website](#website) below).

---

<!-- site-include-start -->

## Setup

```bash
conda env create -f environment.yml        # creates the "thesis" environment (~5 min)
conda activate thesis
python -m ipykernel install --user --name thesis --display-name "Python (thesis)"
jupyter lab
```

Open the notebooks **from the repository root** (they use paths relative to it) and choose the
*Python (thesis)* kernel. To run everything from the command line:

```bash
for nb in 0*.ipynb; do jupyter nbconvert --to notebook --execute --inplace "$nb"; done   # ~4 min total
```

## Pipeline

| Notebook | Thesis | What it does | Reads | Writes | Runtime |
|---|---|---|---|---|---|
| `01_dataset_creation.ipynb` | Ch. 3 | Builds the wildfire-level and monthly datasets from raw CAL FIRE + NOAA data and checks them against the canonical files | `data/raw/…` | `data/processed/rebuilt/*` | ~25 s |
| `02_dataset_exploration.ipynb` | Ch. 4.1, 4.2.2 | Descriptive statistics, maps, climate U-tests, chi-squared region × year | raw CAL FIRE + Rx burns, `monthly_data.csv` | Figs 4.1–4.6, 4.13–4.14 | ~1 min |
| `03_treatment_analysis.ipynb` | Ch. 4.2.1 | Mann–Whitney tests: fires with vs without a prior nearby Rx burn | `prescribed_treatment_data_new.csv` | Table 4.5, Figs 4.7–4.12 | ~10 s |
| `04_time_series_analysis.ipynb` | Ch. 5 | Monthly time series, correlation, cross-correlation | `monthly_data.csv` | Figs 5.1–5.4, Table 5.1 | ~10 s |
| `05_modeling.ipynb` | Ch. 6 | VIF, regional OLS, pooled OLS with interactions, mixed model, KNN, SVM, RF, AdaBoost | `prescribed_treatment_data_new_clean.csv` | Tables 6.1–6.7, Figs 6.1–6.13 | ~2.5 min |

`functions.py` holds the shared plotting and statistics helpers and the path constants. Each notebook begins
with a header cell listing its inputs, outputs and caveats.

**01 never overwrites the canonical data.** The thesis files in `data/processed/` are the ones used for the thesis
results. `01` writes its rebuild to `data/processed/rebuilt/` and checks it against them.

### Thesis figure → file

| Figure | File | Figure | File |
|---|---|---|---|
| 4.1 | `figures/rx_vs_wild.pdf` | 5.1 | `figures/ts.pdf` |
| 4.2 | `figures/acres.pdf` | 5.2 | `figures/rx_wild_ts.pdf` |
| 4.3 | `figures/rx_vs_wild_acres.pdf` | 5.3 | `figures/correlation_mat.pdf` |
| 4.4, 4.5 | `figures/rx_wild_map_2013_2016.png`, `…_2017_2020.png` | 5.4 | `figures/cross_correlation.pdf` |
| 4.6 | `figures/climate_bp.pdf` | 6.1 | `figures/region_coef.pdf` |
| 4.7–4.12 | `figures/bp_3m.pdf` … `bp_36m.pdf` | 6.2–6.5 | `figures/log_prescribed_3_months_size_50km.pdf`, `tmax.pdf`, `pcp.pdf`, `max_wind.pdf` |
| 4.13 | `figures/wildfire_chi.pdf` | 6.6, 6.7 | `figures/lmm_partial_regression.pdf`, `figures/lmm_residuals.pdf` |
| 4.14 | `figures/rx_chi.pdf` | 6.8–6.11 | `figures/{knn,svm,rf,ada}_feature_importance.pdf` |
| | | 6.12, 6.13 | `figures/mse_results.pdf`, `figures/model_performance.pdf` |

`figures/older_exports_2024/` holds PNG exports from 2024 (used in posters and slides) that the notebooks no longer produce.

---

## Repository layout

```
├── 01_dataset_creation.ipynb … 05_modeling.ipynb   the analysis, run in order
├── functions.py                  shared helpers
├── environment.yml               pinned conda environment
├── data/
│   ├── raw/                      original downloads (CAL FIRE, Rx burns, NOAA, boundaries, gridded climate)
│   ├── processed/                datasets used in the thesis (+ rebuilt/ from notebook 01)
│   ├── other_candidates/         datasets evaluated in thesis Table 3.1 but not used
│   └── README.md                 inventory and sources
├── docs/
│   ├── data_dictionary.md        column definitions for the processed datasets
│   ├── data_dictionary_prescribed_treatment_data_new_clean.csv   machine-readable version
│   └── FUTURE_WORK.md            research plan: STQR + distilled CRT
├── figures/                      figures written by the notebooks
├── thesis_documents/             final thesis, defense slides, abstracts, posters
├── literature/                   papers cited in the literature review
└── old/                          superseded notebooks, data and drafts (see old/README.md)
```

---

## Reproducibility

Checked in November 2026 on macOS (Apple silicon) with `environment.yml`:

* `01_dataset_creation` rebuilds `prescribed_treatment_data_new_clean.csv` exactly from the raw data: all 1,992 rows
  and 82 columns identical, including the corrected `max_wind`, which is read from the download cache in
  `data/raw/open_meteo/`. It also rebuilds `monthly_data.csv` (differences < 1e-4 acres, from float rounding).
* For notebooks 02–04, every printed table and statistic matches the 2024 outputs (apart from timestamps).
* `05_modeling` matched the thesis exactly (Tables 6.1–6.7) **before** the wind fix. It now differs on purpose,
  because `max_wind` was corrected; see [Changes since the thesis](#changes-since-the-thesis). The 2024 version and
  its outputs are in `old/original_notebooks_2024/Modeling_2.ipynb`, and the 2024 data file is in
  `old/data/prescribed_treatment_data_new_clean_2024_buggy_wind.csv`.
* The thesis random forest numbers reproduced only with the **PyPI wheel of scikit-learn 1.2.2**, which is why it is
  installed with pip in `environment.yml`. Newer versions and the conda-forge build give slightly different results.
* The original spatial join used geopy in a Python double loop and took about 5.5 hours. It is now vectorized with
  `pyproj.Geod`, which computes the same WGS-84 geodesic, and the rebuilt columns are identical. The original loop
  is still available behind `USE_ORIGINAL_SLOW_LOOP = True`.

## Changes since the thesis

**`max_wind` corrected (November 2026).** The 2024 download used the first fire's date (2013-02-24) for every
fire, so the old column only described location. It correlates just 0.20 with the corrected fire-day values. The
corrected column is the maximum 10 m wind speed (Open-Meteo/ERA5) on the fire's local start date. Only `max_wind`
changed; every other column is byte-identical. Effect on Chapter 6 (current values in `05_modeling.ipynb`; the
figures in `figures/` were regenerated):

| Result | Thesis (2024 wind) | Corrected wind |
|---|---|---|
| VIF of `max_wind` (all predictors / reduced set, Tables 6.1–6.2) | 15.3 / 12.7 | 8.0 / 6.9 |
| Pooled OLS, `log_prescribed_3_months_size_50km` (Table 6.4) | −0.346, p < 0.001 | −0.336, p < 0.001 |
| Pooled OLS, wind terms with p < 0.05 | Sierras×wind (−), Central Coast×wind (+), Multiple×wind (−) | **none** (South Coast×wind p = 0.07) |
| Linear mixed model, Rx coefficient (Table 6.6) | −0.248, p < 0.001 | −0.257, p < 0.001 |
| Linear mixed model, wind random-slope variance | 0.185 | 0.019 |
| Test MSE: null / OLS / LMM / KNN / SVM / RF / AdaBoost (Table 6.7) | 4.857 / 4.467 / 5.066 / 4.847 / 4.734 / **4.216** / 4.749 | 4.857 / 4.520 / 5.364 / 4.730 / 4.712 / **4.168** / 4.713 |
| Tuned hyperparameters | KNN k = 15 uniform; RF 1,000 trees | KNN k = 11 distance-weighted (so train MSE = 0); RF 750 trees |

**What it means:** the Rx association (−0.34 in OLS, −0.26 in the mixed model) and the precipitation and temperature
results are essentially unchanged. The thesis's **significant region × wind interactions (Table 6.4) and the large wind
random-slope variance (Table 6.6) were artefacts of the bug** and disappear. The pooled wind main effect was not
significant before and still isn't (p = 0.69). The random forest is still the best model on test MSE, and every model is still only modestly better than the null model.

**Fig 6.1 significance stars fixed (November 2026).** The plotting code matched p-values to bars in the wrong order,
so 19 of the 32 stars in the thesis figure were on the wrong bar. The coefficients were correct. The corrected
figure shows the prescribed-fire coefficient significant (*p* < 0.05) in the Central Coast, Central Valley, Desert
and Sierras.

## Known issues

These are documented in the notebook headers and the data dictionary, and should be considered in any follow-up work.

1. **Fixed in Nov 2026: `max_wind` was not the wind on the fire day.** The 2024 download used the first fire's date
   (2013-02-24) for every row. `01` now downloads each fire's own date (cached in `data/raw/open_meteo/`), and the
   canonical dataset and `05_modeling` were updated. **Chapter 6 results therefore differ from the submitted thesis.**
   See [Changes since the thesis](#changes-since-the-thesis) below.
2. **20% of Rx burn records (1,736 of 8,473) have no `START_DATE`** and are silently excluded from all prescribed-fire features.
3. **Pile burns and broadcast burns are pooled** (`TREATMENT_TYPE` is not filtered), and distance is measured to the burn **centroid**.
4. **Thesis Table 4.4** (climate Mann–Whitney tests, e.g. U = 11277.5) could not be reproduced from any data or
   notebook in this repository. `02` gives different U values on the monthly data. Treat it as unverified.
5. **Thesis Table 4.5** differs slightly from `03` (e.g. U = 116580.5 vs 116462.5). The 2024 notebook outputs
   already differed, so the table was made from a slightly earlier version of the data. The conclusions are the same.
6. `03` uses `log(log_incident_acres_burned)`, a double log. This hardly matters for rank tests, but don't copy it.
7. OLS models use `hasconst=False` with a manual constant, so statsmodels reports **uncentered** R² (≈0.89). Compare models by MSE.
8. The statewide "3-month" Rx sums in `monthly_data.csv` actually cover 4 months (12-month covers 13) because `.loc` date slices include both ends.
9. Many hypothesis tests, no multiple-comparison correction, and no adjustment for non-random placement of Rx burns.
   [`docs/FUTURE_WORK.md`](docs/FUTURE_WORK.md) proposes how to address this.
10. `data/raw/calfire/mapdataall.csv` is a 2024 snapshot. The live CAL FIRE file changes, so a fresh download will not reproduce the thesis numbers.

## Data sources

* CAL FIRE incidents: https://incidents.fire.ca.gov/imapdata/mapdataall.csv
* CAL FIRE prescribed burns: https://data.ca.gov/dataset/prescribed-burns
* NOAA NCEI Climate at a Glance (county and statewide): https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/
* Open-Meteo historical weather API (wind): https://open-meteo.com/en/docs/historical-weather-api

See [`data/README.md`](data/README.md) for the full inventory.

## Website

The project website is built with [MyST](https://mystmd.org) from `myst.yml`, `index.md`, `website/`, `docs/` and the
notebooks (shown with their saved outputs; they are not re-executed during the build).

```bash
npm install -g mystmd      # or: pip install mystmd
myst start                 # live preview at http://localhost:3000
myst build --html          # static site in _build/html
```

`.github/workflows/deploy.yml` builds and publishes the site to GitHub Pages on every push to `main`. In the GitHub
repository settings, set **Pages → Source** to **GitHub Actions**. Figures for the web pages are PNG copies in
`website/images/`; if a figure changes, regenerate it with
`pdftocairo -png -r 150 -singlefile figures/<name>.pdf website/images/<name>`.
