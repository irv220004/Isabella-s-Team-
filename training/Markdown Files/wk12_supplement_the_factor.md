# Week 12 Supplement — The Factor: statsmodels and the Honest Regression

Companion to deck 12. **Pick your factor and get its data before class.** Lab: Operation The Factor.

**Data this week:** your week 9 clearance series, plus ONE external factor your squad pre-registers at standup. You get the factor's data yourself. Four approved sources are below. Every factor must end up as one row per year.

**Install before class** (inside the venv, then freeze):
```bash
pip install statsmodels
pip freeze > requirements.txt
```

---

## 1. Pre-registration

At standup your squad states one sentence: "We hypothesize that [factor] is associated with Dallas homicide clearance, in the [positive/negative] direction." Locked. No silent pivots after seeing the data.

Which factor you pick determines which section below you follow. Read the whole section for your factor before class, because getting the data is 30 of the lab's 45 minutes.

## 2. Factor A: DPD staffing (sworn officers, detectives)

The hardest to collect, the most interesting if you get it. Nobody publishes a clean yearly table. You assemble it.

**Source 1: FBI Crime Data Explorer, Law Enforcement Employee counts.** Sworn officer totals for Dallas PD by year, back to the 1960s.
1. Go to https://cde.ucr.cjis.gov/
2. Choose **Law Enforcement Employees** (also labeled "Police Employee Data").
3. Agency: **Dallas Police Department**, Texas. ORI `TXDPD00`.
4. Download the CSV. Columns include year, total officers (sworn), total civilians, population.

**Source 2: City of Dallas adopted budget documents.** https://dallascityhall.com/departments/budget → Annual Budget → each fiscal year's adopted budget PDF. The Police Department section lists authorized sworn positions and, in most years, positions by bureau including Investigations. Fiscal year ends September 30; map FY2019 to calendar year 2019.

**Source 3: DPD council briefings** (searchable at dallascityhall.com and dallas.gov): "Current Trends in Police Hiring" (Aug 2016) and the 2015 DPD Retreat deck each contain year-end sworn-strength tables for roughly 2005–2016.

Build `data/dpd_staffing.csv`:

```
year,sworn_total,detectives,source
2010,3597,,"City of Dallas FY10-11 adopted budget; DPD hiring trends memo 2016-08-22"
...
```

Leave `detectives` blank where you cannot find it, and say so in the writeup. A regression on `sworn_total` alone is legitimate. A regression on `sworn_total / reported` (officers per homicide) is more interesting.

Known anchors to check your table against: about 3,597 sworn at end of FY2010, about 3,511 to 3,523 at end of FY2015, about 3,007 in 2018, about 3,120 at end of FY2024.

## 3. Factor B: FRED (Federal Reserve Economic Data), unemployment and income

**Get a key:** free, instant. Create an account at https://fredaccount.stlouisfed.org, then https://fredaccount.stlouisfed.org/apikeys → **Request API Key**. Put it in `.env` as `FRED_API_KEY=...`.

**Endpoint:** `https://api.stlouisfed.org/fred/series/observations?series_id=SERIES&api_key=KEY&file_type=json`

| Series ID | What it is | Range |
|---|---|---|
| `LAUMT481910000000003A` | Unemployment rate, Dallas–Fort Worth–Arlington MSA, **annual**, not seasonally adjusted | 1990– |
| `DALL148URN` | Same, monthly | 1990– |
| `TXUR` | Texas unemployment rate, monthly | 1976– |
| `UNRATE` | US unemployment rate, monthly | 1948– |
| `CPIAUCSL` | US Consumer Price Index, all items, monthly | 1947– |
| `MEHOINUSTXA672N` | Real median household income, Texas, annual | 1984– |

Two gotchas: missing values arrive as the string `"."`, not null; monthly series need `frequency=a` in the query to get annual averages (or a groupby after loading).

```python
import os, requests, pandas as pd
from dotenv import load_dotenv
load_dotenv()

def fred(series_id: str) -> pd.DataFrame:
    r = requests.get("https://api.stlouisfed.org/fred/series/observations", params={
        "series_id": series_id, "api_key": os.environ["FRED_API_KEY"],
        "file_type": "json", "frequency": "a", "aggregation_method": "avg",
    }, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["observations"])
    df["year"] = df.date.str[:4].astype(int)
    df["value"] = pd.to_numeric(df.value, errors="coerce")   # "." -> NaN
    return df[["year", "value"]]

unemp = fred("LAUMT481910000000003A").rename(columns={"value": "unemployment"})
```

Shortcut library: `pip install fredapi`, then `Fred(api_key=KEY).get_series("TXUR")`.

## 4. Factor C: US Census Bureau, American Community Survey (ACS)

**Get a key:** free. https://api.census.gov/data/key_signup.html. Name, organization (UT Dallas), email. Key arrives by email, activate via the link. Put it in `.env` as `CENSUS_API_KEY=...`.

**Geography:** Dallas city is `state:48`, `place:19000`.

**Coverage limit:** ACS 1-year estimates exist for 2005 onward (no 2020 release; the Census Bureau withdrew it). ACS 5-year estimates exist for 2009 onward. **No ACS before 2005.** Your regression will only cover about 20 years. Say so in the confounders section.

**One request per year:**

```python
def acs(year: int, variables: str) -> dict:
    url = f"https://api.census.gov/data/{year}/acs/acs1"
    r = requests.get(url, params={
        "get": "NAME," + variables, "for": "place:19000", "in": "state:48",
        "key": os.environ["CENSUS_API_KEY"],
    }, timeout=60)
    r.raise_for_status()
    header, row = r.json()
    return dict(zip(header, row)) | {"year": year}

rows = [acs(y, "B01003_001E,B19013_001E,B17001_002E,B23025_005E")
        for y in range(2005, 2024) if y != 2020]
census = pd.DataFrame(rows)
```

| Variable | Meaning |
|---|---|
| `B01003_001E` | Total population |
| `B19013_001E` | Median household income (nominal dollars, deflate with CPI if you span many years) |
| `B17001_002E` | Population below poverty level |
| `B23025_005E` | Civilian labor force, unemployed |
| `B25003_003E` | Renter-occupied housing units |
| `B01001_001E` | Total population (sex by age table; use for age-group shares) |

Variable lookup: https://api.census.gov/data/2023/acs/acs1/variables.html. Variable codes are stable across years for these tables.

## 5. Factor D: wildcard

Weather, gun sales (ATF NICS checks by state), school enrollment, court backlog, DART ridership. Must be pre-cleared with the instructor before standup, publicly downloadable, and reducible to one row per year. Put the URL and download date in the writeup.

## 6. The lab: `src/factor.py`

```python
import pandas as pd
import statsmodels.formula.api as smf

series = pd.read_csv("reports/dallas_series.csv")
factor = pd.read_csv("data/your_factor.csv")          # columns: year, <factor>

merged = series.merge(factor, on="year", how="inner")
print(merged.shape); print(merged.head())              # eyeball before modeling

m1 = smf.ols("clearance ~ unemployment", data=merged).fit()
print(m1.summary())

merged["unemployment_lag1"] = merged.unemployment.shift(1)
m2 = smf.ols("clearance ~ unemployment_lag1", data=merged.dropna()).fit()
print(m2.summary())
```

Read `coef`, `P>|t|`, and `R-squared` out loud as a squad. Then write.

## 7. `reports/factor_writeup.md` template

```markdown
# Factor writeup — Squad N

## Hypothesis (as locked at standup)
...

## Data
Clearance: reports/dallas_series.csv (FBI UCR via MAP), years ____–____.
Factor: ____ from ____ (URL), downloaded ____. One row per year, ____ rows after merge.

## Result
clearance ~ factor: coef = ____, p = ____, R² = ____ (n = ____)
Lag-1 variant: coef = ____, p = ____, R² = ____

## Two named confounders
1. ...
2. ...

## Verdict
Over ____–____, ____ is [associated with / not detectably associated with] Dallas homicide
clearance. We do not claim causation because ____.
```

The language rule: "associated with," never "causes."

## 8. Results checklist

- [ ] Hypothesis in the writeup matches what was said at standup
- [ ] Factor data fetched by a script in `src/`, not pasted by hand
- [ ] One primary OLS plus the lag-1 variant, summaries in the PR
- [ ] Two confounders named and discussed
- [ ] Verdict uses "associated with" and quantifies the window
- [ ] Merged via reviewed PR

## 9. Common errors

| Symptom | Fix |
|---|---|
| Merge produces 0 rows | `year` is int in one frame and string in the other. Cast both. |
| `ValueError: could not convert "."` | FRED missing value. `pd.to_numeric(..., errors="coerce")`. |
| Census returns 204 or error for a year | That year/table combination does not exist (e.g. 2020). Skip it. |
| p = 0.03 after your fifth specification | That is p-hacking. Report the pre-registered one. |
