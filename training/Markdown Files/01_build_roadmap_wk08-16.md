# Build Roadmap — How Weeks 8 to 16 Become One Product

Hand out with deck 08. One page. Pin it in the squad repo README.

The product is a Streamlit app, running on a Linode server in Dallas, that audits 60 years of Dallas homicide clearance. Every week from 8 on adds one module to `src/` and one file to `reports/`. Nothing is rebuilt, nothing is thrown away. The app in week 14 only imports and reads what the earlier weeks produced.

---

## The dependency chain

```
WEEK 8   package layout · venv · requirements.txt · .gitignore
           │  every later script lives in src/ and imports from src/
           ▼
WEEK 9   src/get_data.py  ──downloads──►  data/map_ucr.csv  +  data/wapo_dallas.csv
         src/series.py    ──────────────►  reports/dallas_series.csv   (year, reported, cleared, clearance)
           │                                        │
           │                                        ├──────────────────────────────┐
           ▼                                        ▼                              ▼
WEEK 10  src/charts.py  ──► reports/clearance_trend.png                            │
         src/casemap.py ──► reports/dallas_map.html   (from wapo_dallas.csv)       │
           │                                                                        │
           ▼                                                                        │
WEEK 11  src/fetch_city.py ──API+token──► data/case.db                              │
         src/queries.py    ──────────────► murders/yr · top beats · your slice      │
           │              (compare to week 9 counts = the reporting-gap audit)      │
           ▼                                                                        ▼
WEEK 12  src/factor.py  ◄── dallas_series.csv + YOUR factor (staffing / FRED / Census / wildcard)
                        ──► reports/factor_writeup.md
           │
           ▼
WEEK 13  src/predict.py ◄── wapo_dallas.csv  and/or  case.db
                        ──► reports/feature_importances.csv · reports/model_notes.md
         cross-examination of week 12 writeups ──► attacks + responses appended to writeup
           │
           ▼
WEEK 14  src/app.py  (imports src/, reads reports/, computes NOTHING new)
           Series tab   ◄ dallas_series.csv + week 9 suspicious-year note
           Map tab      ◄ dallas_map.html
           What-If tab  ◄ dallas_series.csv + honesty caption
           Model tab    ◄ feature_importances.csv + model_notes.md
           Methodology  ◄ factor_writeup.md + definitions + gap table
           │
           ▼
WEEK 15  Linode Nanode · ssh · clone · venv · pip install -r requirements.txt
         python -m src.get_data / series / casemap / fetch_city  (rebuild data on the server)
         systemd service ──► http://YOUR.IP:8501  from any phone on earth
           │
           ▼
WEEK 16  10-minute briefing FROM the live URL · public repo · class deliverables
```

---

## Where the data enters

| Week | Source | How it gets into the repo | Handout |
|---|---|---|---|
| 9 | Murder Accountability Project (FBI UCR, 1965–2025) | `src/get_data.py` downloads the CSV from murderdata.org | wk09 §2 |
| 9 | Washington Post homicide database (Dallas, 2007–2017) | `src/get_data.py` downloads from GitHub, filters to Dallas | wk09 §3 |
| 11 | City of Dallas OpenData, Police Incidents (2014–now) | `src/fetch_city.py` with each student's own app token | wk11 §2–4 |
| 12 | One factor: DPD staffing, FRED, Census ACS, or wildcard | squad's own fetch script or assembled CSV | wk12 §2–5 |

After week 12 there are no new sources. Weeks 13 to 16 are new views of the same files.

## What each week's merged PR must leave behind

| Week | In `src/` | In `reports/` | Gate for the next week |
|---|---|---|---|
| 8 | `__init__.py`, moved modules, tests green | `.gitkeep` | `requirements.txt` committed |
| 9 | `get_data.py`, `series.py` | `dallas_series.csv` | 61 Dallas rows, 1,567 WaPo rows |
| 10 | `charts.py`, `casemap.py` | `clearance_trend.png`, `dallas_map.html` | map opens in a browser |
| 11 | `fetch_city.py`, `queries.py` | gap paragraph in PR | `case.db` has 1,100+ rows, fetch is cached |
| 12 | `factor.py` | `factor_writeup.md` | hypothesis matches standup |
| 13 | `predict.py` | `feature_importances.csv`, `model_notes.md` | reviewer reproduced the numbers |
| 14 | `app.py` | — | reviewer ran the app, clicked every tab |
| 15 | `release/finals` branch | README: URL + phone screenshot | reviewer loaded the URL from their phone |
| 16 | — | `reporting_gap.md`, methodology in README | every quoted number is in a committed file |

## Why the order is fixed

- **8 before everything.** The app can only import from `src/`. The server can only install from `requirements.txt`. Both exist because of week 8.
- **9 is the keystone.** Weeks 10, 12 and 14 all read `dallas_series.csv`. A squad with no series has nothing to chart, regress or display. Finish week 9 at all costs.
- **11 can slip without killing the product.** Week 13 has the WaPo fallback. Week 14 degrades to four tabs without live data. The reporting-gap audit gets thinner, the app still ships.
- **14 computes nothing.** If the dashboard needs a number the earlier weeks did not produce, the fix goes in `src/` and `reports/`, not in `app.py`. The reviewer checks.
- **15 is four commands** because every `pip install` since week 8 was followed by `pip freeze > requirements.txt`.

## The three definitions you carry the whole way

1. **FBI "cleared"** = arrest or exceptional clearance. Source of `dallas_series.csv`. Series and What-If tabs.
2. **WaPo "closed by arrest"** = arrest only. Source of the map and the model.
3. **City feed "murder"** = `offincident` contains MURDER or equals HOMICIDE. About half the FBI count. The gap is a finding, not a bug.

Every axis label, caption and sentence says which one it uses.

## The end state

A public GitHub repo where `pip install -r requirements.txt` and eight `python -m src.*` commands rebuild every number from the original sources, plus a URL where anyone can see the result. That repo is the deliverable. The briefing is you explaining it.
