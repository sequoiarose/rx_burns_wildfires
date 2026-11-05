# Future Work: Testing the Effect of Prescribed Burns

*Plan written November 2026 for the student continuing this project. Read the thesis
(`thesis_documents/thesis_final.pdf`), the [data dictionary](data_dictionary.md), and the
"Known issues" section of the [README](../README.md) first.*

## 1. Where the thesis left off

The thesis asked whether prescribed (Rx) fire in the months before a wildfire, near where it started,
is associated with a smaller wildfire. The evidence so far:

* **One-sided Mann–Whitney tests** (Table 4.5): wildfires with an Rx burn within 10–50 km in the previous
  3–12 months are slightly smaller (CLES ≈ 0.53–0.57, many p < 0.05). This uses 60 exposure definitions with no
  multiple-testing correction and no adjustment for climate, location, or fuels.
* **Regression on log acres** (Chapter 6): in the pooled OLS model with region interactions,
  `log_prescribed_3_months_size_50km` has a negative coefficient (−0.35 on the standardized scale, p < 0.001).
  This is an association, not a causal effect: the model omits fuels and fire weather, uses the faulty `max_wind`,
  and its standard errors assume independent fires. Models explain little held-out variance (best test MSE 4.2 vs
  4.9 for the null model).

Three limitations motivate the next steps:

1. **Mean models miss the tail.** Most fires are small whatever the treatment. The policy question is whether
   Rx fire reduces the chance of a *large* fire, which is a statement about the upper quantiles of fire size.
2. **Space-time dependence.** Fires and Rx burns cluster in space and time, and nearby fires share the *same* Rx
   burns. Standard errors that treat fires as independent are too small.
3. **Confounded, non-random treatment.** Rx burns are placed according to fuels, ownership (USFS/NPS/CAL FIRE),
   WUI proximity, weather windows and staffing. A regression p-value depends on modelling Y | X, Z correctly. A
   test that instead relies on modelling how treatment is assigned (X | Z) is often easier to defend.

The two methods below address these: **spatio-temporal quantile regression (STQR)** estimates *how large* the
effect is at each part of the fire-size distribution. The **distilled conditional randomization test (dCRT)**
tests *whether* there is any effect, with validity that depends on the treatment-assignment model rather than the
outcome model.

---

## 2. Phase 0: Fix and extend the data (prerequisite, ~1–2 months)

Do this first: both methods depend on good covariates and a well-defined treatment.

| # | Task | Why |
|---|---|---|
| 0.1 | **Add real fire-weather covariates**: pull **gridMET** daily fire weather (ERC, VPD, wind, 100/1000-h fuel moisture, 4 km) for the ignition day and the following week. | `max_wind` was corrected in Nov 2026 to the fire-day wind, but one daily maximum at the ignition point is a weak proxy. Fire weather is the strongest confounder. |
| 0.2 | **Recover the 1,736 Rx burns with no `START_DATE`** (use `END_DATE`, or `YEAR_` plus a mid-season imputation, and flag imputed rows). | 20% of treatment records are currently dropped without notice. |
| 0.3 | **Separate treatment types** (`TREATMENT_TYPE`: broadcast vs pile burns; check FRAP metadata for labels). | Pile burns barely change landscape fuels. Mixing them dilutes the effect. |
| 0.4 | **Better exposure definitions**: distance to the nearest *polygon edge* (not centroid); treated area within R km; a kernel-weighted exposure $E_i=\sum_j A_j\,K_d(d_{ij})\,K_t(\Delta t_{ij})$ (this was already in the thesis notes); overlap of the Rx polygon with the final fire perimeter. | Centroid distance ignores burn size and shape. A single smooth exposure avoids the 6×5 grid of tests. |
| 0.5 | **Add confounders**: LANDFIRE fuel model / existing vegetation type, elevation, slope and aspect (DEM), land ownership, WUI class, distance to roads, time since last wildfire (CAL FIRE FRAP fire perimeters), population density. | Needed for both the outcome model (STQR) and the treatment model (dCRT). |
| 0.6 | **Consider a second outcome**: burn severity from MTBS (dNBR), or fire perimeter area from FRAP instead of reported acres. | Rx fire may change severity more than size. Reported acres are noisy. |
| 0.7 | **Extend the time range** (the Rx layer goes back to the 1950s; CAL FIRE/FRAP perimeters exist before 2013). | n ≈ 2,000 fires is small for upper-tail quantiles. |
| 0.8 | Re-run `01_dataset_creation.ipynb` with the vectorized join (seconds, not hours) and add the new columns to the data dictionary. | |

**Design decision to make early (discuss with your advisor):** the thesis conditions on a wildfire having
happened. If Rx fire prevents ignitions from becoming fires big enough to be recorded, the fire-level data cannot
show it (selection on the outcome). An alternative unit is a **grid-cell × month panel** (e.g. 5–10 km cells):
outcome = area burned in the cell-month (zero-inflated), treatment = Rx exposure of the cell and its neighbours.
Both methods below work in either design. Start with the fire-level design because it matches the thesis,
and use the panel as a robustness check.

---

## 3. Phase 1: Spatio-temporal quantile regression (~2–3 months)

### Model
For fire *i* at location $s_i$ and time $t_i$, and quantile level $\tau$:

$$
Q_\tau\big(\log A_i \mid X_i, Z_i, s_i, t_i\big) \;=\; \alpha(\tau) + \beta(\tau)\,X_i + Z_i^\top\gamma(\tau) + f_\tau(s_i) + g_\tau(t_i) \;[+\, h_\tau(s_i, t_i)]
$$

* $A_i$ = acres burned; $X_i$ = Rx exposure (e.g. `log1p` of acres within R km and T months, or the kernel exposure from 0.4).
* $Z_i$ = fire weather, fuels, topography, ownership, season.
* $f_\tau, g_\tau, h_\tau$ = smooth spatial, temporal, and space-time terms (splines or Gaussian-process effects) that absorb
  unmeasured place- and time-specific factors.
* **Quantity of interest:** $\beta(\tau)$ for $\tau \in \{0.25, 0.5, 0.75, 0.9\}$ (0.95 only after extending the data).
  If Rx fire limits large fires, $\beta(\tau)$ should be negative and largest in magnitude at high $\tau$.

### Implementation path (simple → full)
1. **Baseline linear QR**: `statsmodels.QuantReg`, or `quantreg::rq` in R, with region × year fixed effects plus
   tensor-product splines in (lon, lat). Inference with a **spatial block bootstrap**: resample blocks of space-time
   (e.g. region × fire-season or k-means spatial clusters), never individual fires.
2. **Additive quantile GAM**: R package **`qgam`** (Fasiolo et al. 2021) fits
   `qgam(log_acres ~ x + s(fwi) + s(lon, lat) + s(doy, bs="cc") + te(lon, lat, year), qu = 0.9)`, chooses
   smoothness automatically, and calibrates the loss. This is the recommended main model. The machine already has an
   R Jupyter kernel (`ir`). `quantreg::rqss` is an alternative.
3. **Bayesian spatial QR** (optional, for full uncertainty and partial pooling across regions): asymmetric-Laplace
   likelihood with an NNGP/GP spatial effect, e.g. `brms` (`family = asym_laplace()`, `gp()` or `s()` terms) or a
   custom Stan model (Reich, Fuentes & Dunson 2011; Lum & Gelfand 2012). The asymmetric-Laplace posterior is
   miscalibrated for uncertainty, so use the adjustment in the literature or check against the block bootstrap.

### Checks
* Quantile crossing across τ (fit jointly or rearrange).
* **Coverage on held-out data**: for each region and season, the share of test fires below the predicted τ-quantile should be ≈ τ.
* Residual spatial dependence: Moran's I of the indicator $1\{y_i < \hat q_\tau(\cdot)\} - \tau$. Remaining
  autocorrelation means the smooth terms are too rigid.
* **Sensitivity**: report $\hat\beta(\tau)$ across a *small, pre-registered* set of (T, R) definitions, not all 30.

---

## 4. Phase 2: Distilled conditional randomization test (~2 months, can overlap Phase 1)

### Question
Test $H_0:\; Y \perp X \mid Z$: once confounders are accounted for, Rx exposure carries no information about
wildfire size. The CRT (Candès et al. 2018) is valid in finite samples **if the distribution of $X \mid Z$ is known
or well modelled**, however badly $Y$ is modelled. The distilled version (dCRT; Liu, Katsevich, Janson & Ramdas
2022) makes it fast: all the expensive fitting happens once, and each resample is just a dot product.

### Algorithm
1. **Treatment model $P(X \mid Z)$.** Everything rests on this step, so invest here.
   For a binary exposure (`prescribed_T_months_in_Rkm`) use a well-calibrated classifier (logistic GAM or gradient
   boosting with spatial covariates). For continuous exposure, use a hurdle model: $P(X>0\mid Z)$ × a model for
   $\log X \mid X>0, Z$. Check calibration on held-out data.
2. **Distill Y.** Fit $\hat\mu(Z)$, a prediction of $Y$ from $Z$ **only** (lasso, random forest, boosting, or
   a quantile model $\hat q_\tau(Z)$ for a quantile-specific test). $X$ must not be used.
3. **Statistic.** Mean version: $T(X) = \big|\sum_i (y_i - \hat\mu(z_i))\,(x_i - \hat m(z_i))\big|$ with $\hat m(z) = E[X\mid Z=z]$.
   Quantile version, which pairs with Phase 1: replace $y_i - \hat\mu(z_i)$ by the quantile score
   $\psi_\tau = \tau - 1\{y_i < \hat q_\tau(z_i)\}$.
4. **Resample** $\tilde X^{(b)} \sim P(X\mid Z)$ for $b = 1..B$ (B ≈ 2,000–10,000) and compute $T(\tilde X^{(b)})$.
5. **p-value** $= \big(1 + \#\{b : T(\tilde X^{(b)}) \ge T(X)\}\big) / (B + 1)$.

```python
import numpy as np

def dcrt_pvalue(y, x, d_y, d_x, sample_x, B=5000, tau=None, seed=0):
    """Distilled CRT.
    y        : outcome (n,)
    x        : observed exposure (n,)
    d_y      : prediction of y from Z only (mean, or tau-quantile if tau is given); must not use x
    d_x      : E[X | Z] under the treatment model (n,)
    sample_x : function(rng) -> one draw of X~ from P(X | Z), shape (n,),
               preserving any dependence between units (see below)
    """
    rng = np.random.default_rng(seed)
    r = (y - d_y) if tau is None else (tau - (y < d_y).astype(float))
    stat = lambda xx: abs(np.dot(r, xx - d_x))
    t_obs = stat(x)
    t_null = np.fromiter((stat(sample_x(rng)) for _ in range(B)), float, B)
    return (1 + np.sum(t_null >= t_obs)) / (B + 1)
```

### Spatial dependence: the main technical issue for this project
The CRT needs draws of the *whole vector* $\tilde X$ from its joint conditional distribution. Here exposures of
nearby fires are strongly dependent because they are computed from the **same Rx burns**, so resampling
each fire's exposure independently would give invalid p-values. Options, in order of preference:

* **Simulate at the burn level.** Model the Rx burn process (where and when burns happen, given fuels, ownership,
  season, agency) as a spatio-temporal point process, or resample burns within strata of agency × region × season. Then
  **recompute every fire's exposure from the simulated burns** with the existing join code (now fast). This keeps
  the dependence automatically and gives all 30 (T, R) exposures from one draw.
* **Conditional permutation test** (Berrett et al. 2020) within strata or spatial blocks, which is more robust to
  misspecifying $X\mid Z$.
* **Calibration study** (always do this): with the real $X$ and $Z$, simulate $Y$ under $H_0$ (e.g. from
  $\hat\mu(Z)$ plus resampled residuals) and check that p-values are uniform. Then inject a known effect to measure power.

### Bonus: one test instead of 60
Because every resample regenerates all exposures together, a single statistic $T_{\max} = \max_k$ (standardized
$T_k$ over the (T, R) grid) gives one valid, family-wise p-value for "is there any effect at any window or radius?".
This fixes the thesis's multiple-testing problem.

---

## 5. Putting it together

| Question | Method | Output |
|---|---|---|
| Is there *any* effect of Rx fire on wildfire size, given confounders? | dCRT, $T_{\max}$ over the exposure grid, mean and τ = 0.9 statistics | One p-value per outcome/quantile |
| How large, and at which part of the distribution? | STQR (qgam), $\hat\beta(\tau)$ with block-bootstrap CIs | Coefficient-vs-τ plot (the main figure) |
| How far and how long does the effect reach? | STQR / dCRT on the small pre-specified (T, R) set, or the kernel bandwidths of the exposure | Distance-decay and time-decay curves |
| Does it differ by region or vegetation? | STQR with $X \times$ region interaction; dCRT within region | Regional table |

**Suggested order:** Phase 0 → baseline QR (to get comfortable with the data) → build and calibrate the
treatment model → dCRT with burn-level resampling → qgam STQR → write-up. Keep a short notebook per step
(`06_…`, `07_…`) following the existing layout, and add new columns to `docs/data_dictionary.md`.

## 6. Other ideas from the original notes (lower priority)
* Count models for the number of fires per region-year (Poisson / negative binomial with an area offset).
* Spatio-temporal clustering (ST-DBSCAN) of wildfire and Rx events.
* Multivariate spatial (co-regionalization) models. `old/notebooks/spbayes_analysis.ipynb` has an unfinished `spBayes::spLM` attempt.

## 7. References
* Koenker, R. & Bassett, G. (1978). Regression quantiles. *Econometrica*, 46(1), 33–50.
* Koenker, R. (2005). *Quantile Regression*. Cambridge University Press.
* Fasiolo, M., Wood, S. N., Zaffran, M., Nedellec, R. & Goude, Y. (2021). Fast calibrated additive quantile regression. *JASA*, 116(535), 1402–1412. (`qgam`)
* Reich, B. J., Fuentes, M. & Dunson, D. B. (2011). Bayesian spatial quantile regression. *JASA*, 106(493), 6–20.
* Lum, K. & Gelfand, A. E. (2012). Spatial quantile multiple regression using the asymmetric Laplace process. *Bayesian Analysis*, 7(2), 235–258.
* Candès, E., Fan, Y., Janson, L. & Lv, J. (2018). Panning for gold: model-X knockoffs for high-dimensional controlled variable selection. *JRSS-B*, 80(3), 551–577. (introduces the CRT)
* Liu, M., Katsevich, E., Janson, L. & Ramdas, A. (2022). Fast and powerful conditional randomization testing via distillation. *Biometrika*, 109(2), 277–293.
* Berrett, T. B., Wang, Y., Barber, R. F. & Samworth, R. J. (2020). The conditional permutation test for independence while controlling for confounders. *JRSS-B*, 82(1), 175–197.
* Abatzoglou, J. T. (2013). Development of gridded surface meteorological data for ecological applications and modelling. *Int. J. Climatology*, 33(1), 121–131. (gridMET)
* Banerjee, S., Carlin, B. P. & Gelfand, A. E. (2014). *Hierarchical Modeling and Analysis for Spatial Data* (2nd ed.). CRC Press.
