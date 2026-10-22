# Week 9 Supplement — Real Data: pandas and the Reconciled Series

Companion to deck 09. Read before class and **do the downloads in section 2 before class**. Lab: Operation First Cut.

**Data this week:** two real datasets. You download both yourself from the publisher. Nothing is handed to you.

---

## 1. Rules for every real dataset from here on

- Aggregate analysis only. The files contain real victims. No names in any output, chart, notebook cell, or commit message.
- Raw files live in `data/` and are gitignored. Anyone must be able to rebuild `data/` from your `src/get_data.py` script.
- Every number you publish must trace to a script in `src/`. Nobody hand-edits a CSV.
- Cite the source in `reports/` and in your README.

## 2. Dataset 1: MAP homicide archive (the FBI series)

**Publisher:** Murder Accountability Project (MAP), a nonprofit founded by investigative reporter Thomas Hargrove. MAP repackages the FBI Uniform Crime Report homicide and clearance counts for every US police agency, 1965 to present, and adds records MAP obtained by FOIA that agencies never sent to the FBI.

**How to get it:**

1. Open https://www.murderdata.org/p/data-docs.html
2. Under "UCR clearance data," click the **CSV** link for `UCR65_25.csv`. It is hosted on Dropbox and downloads directly. About 12.8 MB.
3. Save it as `data/map_ucr.csv` in your repo.

Direct link current as of 2026-10-21 (Dropbox links can rotate; if it fails, use step 1):
`https://www.dropbox.com/scl/fi/4y2a6yy0pv4lxffm7sa4v/UCR65_25.csv?rlkey=jhs7ktqhb9h3dnml1wety4nhb&st=7rxppnar&dl=1`

**What you have:** 186,519 rows, 9 columns. One row per agency per year.

| Column | Meaning |
|---|---|
| `ORI` | FBI agency identifier. **Dallas Police Department = `TXDPD00`** |
| `Name` | Agency name as reported, uppercase |
| `YEAR` | Calendar year |
| `MRD` | Murders reported that year |
| `CLR` | Murders cleared that year (by arrest or exceptional means) |
| `Source` | `FBI` or `MAP`. MAP rows came by FOIA and are not in FBI files |
| `State` | State name |
| `County` | e.g. `Dallas, TX` |
| `Agency` | Cleaned agency name, e.g. `Dallas` |

**Trap:** the deck's example uses `Agency`, `Year`, `Homicides`, `Cleared`. The real columns are `Agency`, `YEAR`, `MRD`, `CLR`. And `Agency == "Dallas"` matches four agencies: Dallas TX, Dallas GA, Dallas NC, Dallas OR. The Dallas County Sheriff is a different ORI (`TX05700`). **Filter on `ORI == "TXDPD00"`.** You get 61 rows, 1965 through 2025.

**Sanity anchors:** 1965 = 116 reported, 109 cleared. 1991 = 500 / 350 (the peak). 2020 = 247 / 130. 2025 = 139 / 72 (partial year, still being reported).

**Cite as:** Murder Accountability Project, UCR homicide and clearance data (UCR65_25), murderdata.org, accessed [date].

## 3. Dataset 2: Washington Post homicide database, Dallas subset

**Publisher:** The Washington Post, for its 2018 investigation "Where Killings Go Unsolved." Reporters obtained case-level records from 50 large police departments, geocoded them, and published the full file.

**How to get it:**

1. The repo is https://github.com/washingtonpost/data-homicides. The file is `homicide-data.csv` (52,179 rows, all 50 cities).
2. Download the raw file: `https://raw.githubusercontent.com/washingtonpost/data-homicides/master/homicide-data.csv`
3. Filter to `city == "Dallas"` and save as `data/wapo_dallas.csv`. **You must get exactly 1,567 rows.**

**What you have (Dallas rows):**

| Column | Notes |
|---|---|
| `uid` | `Dal-001045` style |
| `reported_date` | Integer `YYYYMMDD`. Parse: `pd.to_datetime(df.reported_date, format="%Y%m%d")` |
| `victim_last`, `victim_first` | **Drop these on load.** Never print or plot them. |
| `victim_race`, `victim_age`, `victim_sex` | `victim_age` is a string containing `Unknown` |
| `city`, `state` | `Dallas`, `TX` |
| `lat`, `lon` | Decimal degrees. Some rows share a point (geocoded to block) |
| `disposition` | `Closed by arrest` (813) · `Open/No arrest` (676) · `Closed without arrest` (78) |

Coverage: January 2007 through early 2017. 2017 has 45 rows and is partial.

**Definition note for the audit:** WaPo counts a case solved only when `Closed by arrest`. The FBI `CLR` column also counts exceptional clearances (suspect dead, prosecution declined). These are two different definitions of "cleared." Every chart axis and every methodology note must say which one it uses.

**License:** CC BY-NC-SA 4.0. Attribution required, non-commercial. Fine for this course and the public class repo.

**Cite as:** The Washington Post, Unsolved Homicide Database, github.com/washingtonpost/data-homicides, 2018.

## 4. `src/get_data.py` — make the downloads reproducible

Write this once. Anyone cloning your repo runs it and gets the same `data/` folder.

```python
"""Download the week 9 sources into data/. Run: python -m src.get_data"""
from pathlib import Path
import pandas as pd
import requests

DATA = Path("data")
DATA.mkdir(exist_ok=True)

MAP_URL = ("https://www.dropbox.com/scl/fi/4y2a6yy0pv4lxffm7sa4v/UCR65_25.csv"
           "?rlkey=jhs7ktqhb9h3dnml1wety4nhb&st=7rxppnar&dl=1")
WAPO_URL = ("https://raw.githubusercontent.com/washingtonpost/"
            "data-homicides/master/homicide-data.csv")


def fetch(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"cached: {dest}")
        return
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"saved: {dest} ({dest.stat().st_size:,} bytes)")


def main() -> None:
    fetch(MAP_URL, DATA / "map_ucr.csv")
    fetch(WAPO_URL, DATA / "wapo_all.csv")

    # the Post's file is Latin-1, not UTF-8; without this pandas raises UnicodeDecodeError
    wapo = pd.read_csv(DATA / "wapo_all.csv", encoding="latin-1")
    dallas = wapo[wapo["city"] == "Dallas"].drop(
        columns=["victim_last", "victim_first"])
    dallas.to_csv(DATA / "wapo_dallas.csv", index=False)
    print(f"wapo_dallas.csv: {len(dallas)} rows (expect 1567)")


if __name__ == "__main__":
    main()
```

`pip install requests` then `pip freeze > requirements.txt`.

## 5. The lab: building `reports/dallas_series.csv`

```python
# src/series.py
import pandas as pd

df = pd.read_csv("data/map_ucr.csv")
print(df.shape); print(df.columns.tolist()); print(df.head())

dallas = df[df["ORI"] == "TXDPD00"]
print("Dallas PD rows:", len(dallas))        # 61

per_year = dallas.groupby("YEAR").agg(
    reported=("MRD", "sum"),
    cleared=("CLR", "sum"),
)
per_year["clearance"] = per_year["cleared"] / per_year["reported"]
per_year.index.name = "year"
per_year.to_csv("reports/dallas_series.csv")
```

Deliverable columns: `year, reported, cleared, clearance`.

**The three mandatory sanity checks:**

```python
# 1. rates over 100%
print(per_year[per_year.clearance > 1])

# 2. missing years
years = set(per_year.index)
print(sorted(set(range(1965, 2026)) - years))

# 3. biggest year-over-year jumps in clearance
print(per_year.clearance.diff().abs().sort_values(ascending=False).head(5))
```

Then print your 5 most suspicious years with one line of reasoning each. Candidates you should notice: the 2007–2011 slide, 2017 (clearance jumps to 80% in one year), 2018 (drops to 40% the next), 2025 (partial year).

## 6. Stretch: add WaPo as a second source column

```python
w = pd.read_csv("data/wapo_dallas.csv")
w["year"] = w.reported_date.astype(str).str[:4].astype(int)
wapo_year = w.groupby("year").agg(
    wapo_cases=("uid", "count"),
    wapo_arrests=("disposition", lambda s: (s == "Closed by arrest").sum()),
)
merged = per_year.join(wapo_year, how="left")
```

Do the two sources agree on how many homicides Dallas had in 2010? They will not. Write down by how much. That gap is week 12's audit.

## 7. Results checklist

- [ ] `src/get_data.py` rebuilds `data/` from nothing
- [ ] `reports/dallas_series.csv` committed with `year, reported, cleared, clearance`
- [ ] Sanity check output pasted in the PR description
- [ ] 5 suspicious years, one line each, in the PR
- [ ] `data/*.csv` gitignored, `reports/` committed
- [ ] `pytest` still green
- [ ] Merged via reviewed PR

## 8. Common errors

| Symptom | Fix |
|---|---|
| `KeyError: 'Year'` | Column is `YEAR`. Print `df.columns` first, always. |
| Dallas filter returns 90+ rows | You filtered on `Agency`. Use `ORI == "TXDPD00"`. |
| `wapo_dallas.csv` has 1,566 or 1,568 rows | You filtered on `state == "TX"` or stripped a header. Filter on `city == "Dallas"`. |
| `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x90` | The Post's file is Latin-1. `pd.read_csv(..., encoding="latin-1")`. |
| Dropbox link returns HTML | Link rotated. Go to murderdata.org/p/data-docs.html and copy the current CSV link. |
| `requests` not found | Install inside the venv, then freeze. |
