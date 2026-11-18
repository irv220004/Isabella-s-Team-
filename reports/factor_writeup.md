# Factor writeup — Squad N

## Hypothesis (as locked at standup)
We hypothesize that Dallas-area unemployment is associated with Dallas homicide clearance, in the negative direction.

> NOTE FOR THE SQUAD: this sentence was assumed when the code was written. It must match what your squad actually
> locked at standup. If it doesn't, fix this section and `HYPOTHESIS` in `src/factor.py`. Do NOT change it to fit
> the result below.

## Data
Clearance: `reports/dallas_series.csv` (FBI UCR via MAP, Dallas PD `TXDPD00`), years 1965–2025.
Factor: unemployment rate, Dallas–Fort Worth–Arlington MSA, annual, not seasonally adjusted, FRED series
`LAUMT481910000000003A` (https://api.stlouisfed.org/fred/series/observations?series_id=LAUMT481910000000003A),
downloaded 2026-11-18 by `src/factor.py`. One row per year, 36 rows after merge (1990–2025). The merged data is in
`reports/factor_merged.csv`.

## Result
clearance ~ unemployment: coef = 0.0197, p = 0.0998, R² = 0.078 (n = 36)
Lag-1 variant (last year's unemployment): coef = 0.0239, p = 0.048, R² = 0.114 (n = 35)

Reading it: the coefficients are in clearance-rate units, so +0.0197 means about +2.0 percentage points of
clearance per +1 percentage point of unemployment. The sign is **positive**, the opposite of the hypothesis. In the
primary model the slope is not distinguishable from zero at the 5% level (p = 0.10). The lag-1 variant crosses
p < 0.05 only barely (p = 0.048, 95% CI from 0.000 to 0.048) and explains about 11% of the variation in clearance;
we do not treat that as confirmation, since it is one of only two models we ran and the sign contradicts our
hypothesis. Full tables: `reports/factor_ols_summary.txt`.

## Two named confounders
1. **Homicide volume and case mix.** Clearance is cleared ÷ reported, so anything that changes how many murders are
   reported, or how hard they are to solve (stranger or gang cases versus domestic ones), moves clearance with no
   change in police effort. Economic conditions plausibly move case mix and volume at the same time, so unemployment
   and clearance can move together through a third path.
2. **DPD staffing and budget.** Unemployment moves city tax revenue, and revenue moves hiring and detective capacity,
   which in turn moves clearance. If so, unemployment is only a stand-in for resources. We did not source staffing
   data (that is Factor A), so we cannot control for it.

Other limits: the MSA unemployment rate covers the whole region, not the city of Dallas; both series trend over time,
so some of any association may be shared drift (the Durbin–Watson statistic of about 1.5 hints at autocorrelated
errors, which makes the p-values look better than they are); 2025 is a partial year in the clearance series; and
36 yearly points is a small sample.

## Verdict
Over 1990–2025, Dallas-area unemployment is not detectably associated with Dallas homicide clearance in our
pre-registered model (p = 0.10), and what weak association shows up is in the positive direction, not the negative
one we hypothesized. The lag-1 variant is borderline (p = 0.048) and we do not rely on it. We do not claim causation
because unemployment, case mix and police resources all move together over time and we have not controlled for them.
