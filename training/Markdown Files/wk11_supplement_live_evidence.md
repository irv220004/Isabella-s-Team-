# Week 11 Supplement — Live Evidence: the Dallas OpenData API and SQLite

Companion to deck 11. **Section 2 must be done before class.** Lab: Operation The Tap.

**Data this week:** the City of Dallas live police incident feed. You fetch it yourself with your own API token. No files are handed out.

**Install before class** (inside the venv, then freeze):
```bash
pip install requests python-dotenv
pip freeze > requirements.txt
```
`sqlite3` ships with Python. Nothing to install.

---

## 1. The dataset

| | |
|---|---|
| Name | Police Incidents |
| Publisher | City of Dallas, Dallas Police Department, Records Management System (RMS) |
| Portal page | https://www.dallasopendata.com/Public-Safety/Police-Incidents/qv6i-rri7 |
| Resource id | `qv6i-rri7` |
| API endpoint | `https://www.dallasopendata.com/resource/qv6i-rri7.json` |
| Coverage | June 1, 2014 to present, refreshed daily. About 1.5 million rows total, 100k to 145k per year. |
| API docs | https://dev.socrata.com/foundry/www.dallasopendata.com/qv6i-rri7 |
| Query language | SODA 2.1. Parameters start with `$`: `$select`, `$where`, `$group`, `$order`, `$limit`, `$offset`. Reference: https://dev.socrata.com/docs/queries/ |

The portal's own description says the dataset is "published for research" and that the DPD Crime Analytics Dashboard is the authoritative source. Rows are filtered for privacy. Remember both sentences when you compare the counts to the FBI.

## 2. Get your app token (before class, free, 5 minutes)

1. Go to https://www.dallasopendata.com. Click **Sign In**, then **Sign Up**. Any email address works.
2. Confirm the email.
3. Click your name (top right) → **My Profile** → **Edit Profile** → **Developer Settings** tab.
4. **Create New App Token**. Application name: anything (`clearance-project`). Description: anything. Save.
5. Copy the **App Token** string (about 25 characters). You do not need the Secret Token.

Store it in a file called `.env` at the repo root:

```
DALLAS_APP_TOKEN=paste_your_token_here
```

`.env` is already in your `.gitignore` from week 8. **Never commit the token.** Each detective uses their own.

Why: without a token you share a throttled pool with everyone else on the campus network and will get HTTP 429 mid-lab. With a token, requests are not throttled.

## 3. The fields that matter

The dataset has about 70 fields. These are the ones you use.

| Field | Meaning |
|---|---|
| `incidentnum` | Case number, `204327-2022` style. Unique per incident. |
| `servyr` | Service year, stored as a **string**. Group on this. |
| `date1`, `year1`, `month1`, `time1` | When the offense began |
| `offincident` | Offense description. Murder rows read `MURDER`, `CAPITAL MURDER BY TERROR THREAT/OTHER FELONY`, `CAPITAL MURDER OF MULTIPLE PERSONS`, `HOMICIDE`, `MURDER (NO CODE)`, `CAPITAL MURDER WHILE REMUNERATION` |
| `nibrs_crime_category` | `HOMICIDE` for murders, **but only populated from 2017 onward**. Do not filter on it alone. |
| `beat`, `division`, `sector`, `district`, `ra` | Police geography. `beat` is your "top 5 beats." `ra` is reporting area. |
| `premise` | Residence, street, parking lot, etc. |
| `victimtype`, `status`, `ucr_disp` | Case attributes. Week 13 features. |
| `zip_code`, `city`, `state` | Address pieces |
| `geocoded_column` | Nested dict with `latitude`, `longitude`. Flatten before `to_sql`. |

A few `servyr` values are garbage (`1011`, `1429`, 1967–1991 with 1 to 6 rows each). That is a data-quality finding. Quarantine them, do not delete silently.

## 4. `src/fetch_city.py` — fetch once, cache, bank in SQLite

```python
"""Fetch every murder incident from Dallas OpenData into data/case.db.
Run: python -m src.fetch_city"""
import json, os, sqlite3
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["DALLAS_APP_TOKEN"]
URL = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
WHERE = "offincident like '%MURDER%' OR offincident = 'HOMICIDE'"
RAW = Path("data/raw_incidents.json")
DB = Path("data/case.db")
PAGE = 5000


def fetch_all() -> list[dict]:
    if RAW.exists():
        print("using cache", RAW)
        return json.loads(RAW.read_text())
    rows, offset = [], 0
    while True:
        r = requests.get(URL, params={
            "$where": WHERE, "$order": "incidentnum",
            "$limit": PAGE, "$offset": offset, "$$app_token": TOKEN,
        }, timeout=60)
        r.raise_for_status()
        page = r.json()
        rows.extend(page)
        print(f"offset {offset}: {len(page)} rows")
        if len(page) < PAGE:
            break
        offset += PAGE
    RAW.write_text(json.dumps(rows))
    return rows


def flatten(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    geo = df.pop("geocoded_column")
    df["lat"] = geo.apply(lambda g: float(g["latitude"]) if isinstance(g, dict) else None)
    df["lon"] = geo.apply(lambda g: float(g["longitude"]) if isinstance(g, dict) else None)
    df = df[[c for c in df.columns if not c.startswith(":@")]]   # drop computed regions
    df["servyr"] = pd.to_numeric(df["servyr"], errors="coerce")
    return df


def main() -> None:
    df = flatten(fetch_all())
    con = sqlite3.connect(DB)
    df.to_sql("incidents", con, if_exists="replace", index=False)
    n = pd.read_sql("SELECT COUNT(*) AS n FROM incidents", con).n[0]
    print(f"case.db: {n} rows in incidents")


if __name__ == "__main__":
    main()
```

Expect roughly 1,100 to 1,250 rows total. Yes, that is small. Read section 6.

Get one page printing before you write the loop. `curl` test from the terminal:

```bash
curl "https://www.dallasopendata.com/resource/qv6i-rri7.json?\$limit=2&\$\$app_token=YOURTOKEN"
```

## 5. `src/queries.py` — three questions

```python
import sqlite3, pandas as pd
con = sqlite3.connect("data/case.db")

q1 = """SELECT servyr AS year, COUNT(*) AS murders
        FROM incidents WHERE servyr BETWEEN 2014 AND 2026
        GROUP BY servyr ORDER BY servyr"""

q2 = """SELECT beat, COUNT(*) AS n FROM incidents
        WHERE beat IS NOT NULL GROUP BY beat ORDER BY n DESC LIMIT 5"""

# your squad's slice: pick ONE and justify it
q3 = """SELECT ROUND(100.0 * SUM(premise LIKE '%RESIDENCE%') / COUNT(*), 1) AS pct_residence
        FROM incidents"""

for q in (q1, q2, q3):
    print(pd.read_sql(q, con), "\n")
```

## 6. What you will find, and why it is the audit

Compare `q1` to the FBI series you built in week 9.

| Year | FBI `MRD` (week 9) | City API, murder filter |
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

The city's public feed shows roughly half the murders the city reported to the FBI. **Your fetch is not broken.** Candidate explanations you should write down for week 12: privacy filtering before publication; incidents initially coded as another offense (aggravated assault, death investigation) and reclassified after the public export; one incident row for multiple victims; the public export being a research copy, not the system of record. Which of these can you test with the data you have? Which can you not? That is the reporting-gap writeup.

Do not "fix" the gap by scaling. Document it.

## 7. Stretch: a second table in `case.db`

Dallas does not publish a historical 911 calls-for-service table. "Dallas Police Active Calls" (`9fxf-t2tr`) is a live snapshot, not history. Options that do work:

- Officer-involved shootings, 2003 to present: resource `4gmt-jyx2`, same portal, same token.
- A second offense category from `qv6i-rri7`, e.g. `nibrs_crime_category = 'AGGRAVATED ASSAULT'` for 2017 onward. Fetch by year to keep each pull under 50k rows.

Join on `servyr` or `beat` and ask a question the single table could not answer.

## 8. Results checklist

- [ ] Every detective has a token in their own `.env`, nothing in git
- [ ] `src/fetch_city.py` pages the API, caches raw JSON, rerun does not re-fetch
- [ ] `data/case.db` exists; `SELECT COUNT(*)` output in the PR
- [ ] `src/queries.py` prints murders per year, top 5 beats, your slice percentage
- [ ] The FBI-versus-city gap noted in the PR in one paragraph
- [ ] Merged via reviewed PR

## 9. Common errors

| Symptom | Fix |
|---|---|
| `KeyError: 'DALLAS_APP_TOKEN'` | `.env` missing or `load_dotenv()` not called before `os.environ` |
| HTTP 400 | A quote or `%` in `$where` was not URL-encoded. Pass params as a dict to `requests`, never build the URL by hand. |
| HTTP 429 | No token, or token typo. |
| Loop never ends | `$order` missing. Without a stable order, paging repeats rows. |
| `to_sql` fails on dict column | You did not flatten `geocoded_column`. |
| `servyr` groups look wrong | It is a string in the API. Convert with `pd.to_numeric`. |
