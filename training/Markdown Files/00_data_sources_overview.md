# Dallas Clearance Project — Data Sources Overview (Weeks 9–13)

One-page index. The per-week files (`wk08_` through `wk16_`) have the step-by-step instructions; this file is the summary of where every dataset comes from.

Where every real dataset in the second half comes from, what is in it, and how to load it. Weeks 8, 10, 14, 15 and finals use only files your squad already produced, so they are not listed here.

Verified against the live sources on 2026-10-21.

## Week-by-week map

| Week | Lab | Source(s) | How you get it |
|---|---|---|---|
| 9 | First Cut | MAP UCR homicide archive (`map_ucr.csv`) + Washington Post Dallas cases (`wapo_dallas.csv`) | You download both from the publisher (see `wk09_supplement_real_data.md`, sections 2–4) |
| 10 | The Picture | Your `reports/dallas_series.csv` + `wapo_dallas.csv` from week 9 | Already in your repo |
| 11 | The Tap | Dallas OpenData, Police Incidents (`qv6i-rri7`) | Live API, your own app token |
| 12 | The Factor | ONE of: DPD staffing (you assemble it), FRED API, Census ACS API, or a pre-cleared wildcard | See `wk12_supplement_the_factor.md` |
| 13 | The Model | `wapo_dallas.csv` and/or your `data/case.db` from week 11 | Already in your repo |
| 14–finals | Dashboard, deploy, briefing | Your `reports/` and `data/case.db` | Already in your repo |

Rule for every source: aggregate analysis only. Real victims are in these files. No names in any output, chart, or commit message.

---

## 1. MAP homicide archive (week 9) — `data/map_ucr.csv`

**Who publishes it:** the Murder Accountability Project (MAP), a nonprofit run by Thomas Hargrove. It repackages the FBI's Uniform Crime Report "Return A" homicide counts and clearance counts for every reporting agency, 1965 to present, and adds records MAP obtained by FOIA that agencies never sent the FBI.

**Where it came from:** https://www.murderdata.org/p/data-docs.html → "UCR65_25.csv" (CSV download). Save the download as `data/map_ucr.csv`, unchanged. Updated by MAP on 2026-08-18.

**Size:** 186,519 rows, 9 columns, 12.8 MB. Keep it in `data/` and add `data/*.csv` to `.gitignore`.

**Columns (real names, use these):**

| Column | Meaning |
|---|---|
| `ORI` | FBI agency identifier. **Dallas Police Department = `TXDPD00`** |
| `Name` | Agency name as reported (uppercase) |
| `YEAR` | Calendar year |
| `MRD` | Murders reported that year |
| `CLR` | Murders cleared that year (arrest or exceptional means) |
| `Source` | `FBI` or `MAP` (MAP = obtained by FOIA, not in FBI files) |
| `State` | State name |
| `County` | County, e.g. `Dallas, TX` |
| `Agency` | Cleaned agency name, e.g. `Dallas` |

**Trap you will hit:** the deck's example code uses `Agency`, `Year`, `Homicides`, `Cleared`. The real file uses `Agency`, `YEAR`, `MRD`, `CLR`. Also `df["Agency"] == "Dallas"` matches **four** agencies: Dallas TX, plus Dallas GA, Dallas NC and Dallas OR. Dallas County Sheriff is a separate ORI (`TX05700`). Filter on `ORI`.

```python
import pandas as pd

df = pd.read_csv("data/map_ucr.csv")
dallas = df[df["ORI"] == "TXDPD00"]          # 61 rows, 1965–2025

per_year = dallas.groupby("YEAR").agg(
    reported=("MRD", "sum"),
    cleared=("CLR", "sum"),
)
per_year["clearance"] = per_year["cleared"] / per_year["reported"]
per_year.index.name = "year"
per_year.to_csv("reports/dallas_series.csv")
```

**Sanity anchors (so you know the load worked):** 1965 = 116 reported / 109 cleared. 1991 = 500 / 350 (the peak). 2020 = 247 / 130. 2025 = 139 / 72 (partial year).

**Cite as:** Murder Accountability Project, UCR homicide and clearance data (UCR65_25), murderdata.org, accessed 2026-10-21.

---

## 2. Washington Post homicide database, Dallas subset (weeks 9, 10, 13) — `data/wapo_dallas.csv`

**Who publishes it:** The Washington Post, for its 2018 series "Where Killings Go Unsolved." Reporters collected case-level records from 50 large US police departments. Public repo: https://github.com/washingtonpost/data-homicides (file `homicide-data.csv`, 52,179 rows nationally).

**What you build:** download `homicide-data.csv` from the raw GitHub URL (it is Latin-1 encoded, so `pd.read_csv(..., encoding="latin-1")`), keep the rows where `city == "Dallas"`, drop the two name columns. 1,567 rows. Coverage is 2007-01 through early 2017 (2017 has only 45 rows, so treat it as partial).

**Columns:**

| Column | Notes |
|---|---|
| `uid` | `Dal-NNNNNN` |
| `reported_date` | `YYYYMMDD` as an integer. Parse with `pd.to_datetime(df.reported_date, format="%Y%m%d")` |
| `victim_last`, `victim_first` | Present in the file. Do not print, plot, or commit them. Drop these columns on load. |
| `victim_race`, `victim_age`, `victim_sex` | `victim_age` is a string and includes `Unknown` |
| `city`, `state` | `Dallas`, `TX` |
| `lat`, `lon` | Decimal degrees. A handful of rows share coordinates (geocoded to block) |
| `disposition` | `Closed by arrest` (813) · `Open/No arrest` (676) · `Closed without arrest` (78) |

**Definition note for the audit:** WaPo counts a case "cleared" only if `Closed by arrest`. The FBI/MAP `CLR` column also counts exceptional clearances (`Closed without arrest`). Your axis labels and methodology must say which definition each line uses.

**License:** CC BY-NC-SA 4.0. Non-commercial, attribution required, share-alike. Fine for this course and for the public class repo.

**Cite as:** The Washington Post, Unsolved Homicide Database, github.com/washingtonpost/data-homicides, 2018.

---

## 3. Dallas OpenData — Police Incidents (week 11, reused weeks 13–14)

**Dataset:** "Police Incidents," Dallas Police Department RMS incident data, June 1 2014 to present, refreshed daily.
**Portal page:** https://www.dallasopendata.com/Public-Safety/Police-Incidents/qv6i-rri7
**API endpoint:** `https://www.dallasopendata.com/resource/qv6i-rri7.json`
**API docs:** https://dev.socrata.com/foundry/www.dallasopendata.com/qv6i-rri7 (SODA 2.1 query language: `$select`, `$where`, `$group`, `$order`, `$limit`, `$offset`)

**Get your app token before class (free, five minutes):**
1. Go to https://www.dallasopendata.com and click **Sign In** → **Sign Up**. Any email works.
2. After confirming the email, click your name (top right) → **My Profile** → **Edit Profile** → **Developer Settings**.
3. **Create New App Token.** Name it anything (`clearance-project`). Copy the token string.
4. Put it in a `.env` file or an environment variable. Never commit it. Add `.env` to `.gitignore`.

Without a token you share a throttled pool with everyone else on your IP and will get HTTP 429 mid-lab. With a token, requests are effectively unthrottled.

**Fields you will use** (the dataset has about 70; these matter):

| Field | Meaning |
|---|---|
| `incidentnum` | Case number, e.g. `204327-2022` |
| `servyr` | Service year (string). Group on this |
| `date1`, `year1`, `month1` | Date the offense began |
| `offincident` | Offense description. Murder rows read `MURDER`, `CAPITAL MURDER BY TERROR THREAT/OTHER FELONY`, `CAPITAL MURDER OF MULTIPLE PERSONS`, `HOMICIDE`, `MURDER (NO CODE)` |
| `nibrs_crime_category` | `HOMICIDE` for murder rows, **but only populated from 2017 onward**. Do not filter on it alone. |
| `beat`, `division`, `sector`, `district`, `ra` | Police geography. `beat` is your week 11 "top 5 beats" |
| `premise`, `victimtype`, `status`, `ucr_disp` | Case attributes for week 13 features |
| `zip_code`, `geocoded_column` | Location. `geocoded_column` is a nested dict with `latitude`/`longitude` |

**The murder filter:**

```python
params = {
    "$where": "offincident like '%MURDER%' OR offincident = 'HOMICIDE'",
    "$order": "incidentnum",
    "$limit": 5000,
    "$offset": 0,
    "$$app_token": TOKEN,
}
```

Page with `$offset` until a page comes back shorter than `$limit`. Expect roughly 1,100 to 1,200 rows total. Save the raw JSON to `data/raw_incidents.json` and load from the cache on every rerun.

**What you will find, and why it is the audit:** the city feed returns far fewer murders than the FBI series for the same years.

| Year | FBI/MAP `MRD` | City API `offincident like '%MURDER%'` |
|---|---|---|
| 2014 | 116 | 44 (feed starts June 1) |
| 2015 | 136 | 70 |
| 2016 | 171 | 122 |
| 2017 | 167 | 119 |
| 2018 | 153 | 71 |
| 2019 | 201 | 81 |
| 2020 | 247 | 95 |
| 2021 | 206 | 80 |
| 2022 | 206 | 95 |
| 2023 | 242 | 102 |
| 2024 | 180 | 80 |

The portal's own description says it is "published for research" and that the DPD Crime Analytics Dashboard is the authoritative source. Rows are filtered for privacy. Some homicides are coded as other offenses and reclassified later. Your reporting-gap writeup should name these candidate explanations and say which you can and cannot test. Do not "fix" the gap. Document it.

**Second table for the stretch goal:** Dallas does not publish a historical 911 calls-for-service table. "Dallas Police Active Calls" (`9fxf-t2tr`) is a live snapshot only. If you want a second table in `case.db`, use "Dallas Police Officer-Involved Shootings" (`4gmt-jyx2`) or pull a second offense category (e.g. aggravated assault) from `qv6i-rri7`.

**Cite as:** City of Dallas Open Data, Police Incidents (qv6i-rri7), dallasopendata.com, accessed [date you fetched].

---

## 4. Factor data for week 12 (pick one, lock it at standup)

Every factor must end up as **one row per year** so it merges onto your clearance series on `year`.

### A. DPD staffing — `data/dpd_staffing.csv` (you assemble it)

Columns: `year`, `sworn_total`, `detectives`, `source`. Sources: FBI Crime Data Explorer (cde.ucr.cjis.gov) Law Enforcement Employees for Dallas PD, ORI `TXDPD00`; City of Dallas adopted budget PDFs; DPD council briefings. Fiscal years map to the calendar year in which they end. Full steps in `wk12_supplement_the_factor.md`, section 2.

### B. FRED (Federal Reserve Economic Data) — unemployment, CPI, income

- **Key:** free, instant. Sign in at https://fredaccount.stlouisfed.org/apikeys and click "Request API Key."
- **Endpoint:** `https://api.stlouisfed.org/fred/series/observations?series_id=SERIES&api_key=KEY&file_type=json`
- Missing values arrive as the string `"."`, not null. Monthly series need `frequency=a` (annual average) in the query, or a groupby after loading.

| Series ID | What it is |
|---|---|
| `LAUMT481910000000003A` | Unemployment rate, Dallas–Fort Worth–Arlington MSA, **annual**, 1990– |
| `DALL148URN` | Same, monthly, not seasonally adjusted |
| `TXUR` | Texas unemployment rate, monthly, 1976– |
| `UNRATE` | US unemployment rate, monthly, 1948– |
| `CPIAUCSL` | US CPI, all items, monthly |
| `MEHOINUSTXA672N` | Real median household income, Texas, annual |

Python shortcut: `pip install fredapi`, then `Fred(api_key=KEY).get_series("LAUMT481910000000003A")`.

### C. US Census Bureau — American Community Survey (ACS)

- **Key:** free. Request at https://api.census.gov/data/key_signup.html (name + email, arrives by email).
- **Dallas city** is `state:48`, `place:19000`. ACS 1-year estimates exist for 2005 onward (no 2020 1-year release). ACS 5-year exists for 2009 onward.
- **Example:** `https://api.census.gov/data/2023/acs/acs1?get=NAME,B01003_001E,B19013_001E,B17001_002E,B23025_005E&for=place:19000&in=state:48&key=KEY`

| Variable | Meaning |
|---|---|
| `B01003_001E` | Total population |
| `B19013_001E` | Median household income |
| `B17001_002E` | Population below poverty level |
| `B23025_005E` | Civilian labor force, unemployed |
| `B25003_003E` | Renter-occupied housing units |

One request per year, so loop over years and build the frame. Variable names are stable across years for these tables. Variable lookup: https://api.census.gov/data/2023/acs/acs1/variables.html

Caveat for your confounders section: ACS only reaches back to 2005, so a Census factor can only be tested against the last twenty years of the series.

### D. Wildcard

Anything else (weather, gun sales, school enrollment, court backlog) must be pre-cleared with the instructor before standup, be publicly downloadable, and be reducible to one row per year. Put the URL and download date in `reports/factor_writeup.md`.

---

## 5. Features for week 13

From `wapo_dallas.csv`: `victim_age` (coerce to numeric, `Unknown` → NaN), `victim_sex`, `victim_race`, `lat`, `lon`, year and month from `reported_date`. Target: `disposition != "Closed by arrest"` (unsolved).

From `data/case.db`: `premise`, `beat`, `division`, `victimtype`, `month1`, `watch`. Target depends on what `status`/`ucr_disp` support in your rows. Inspect them first with `SELECT status, COUNT(*) ... GROUP BY status`.

Never use `victim_first`/`victim_last` as features or print them in notebooks.

---

## 6. What goes in `.gitignore`

```
.venv/
.env
data/*.csv
data/*.json
data/case.db
```

`reports/` is committed. `data/` is rebuilt by `python -m src.get_data` and `python -m src.fetch_city`.
