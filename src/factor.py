"""Week 12 - Factor B (FRED): is Dallas-area unemployment associated with Dallas homicide clearance?
Run: python -m src.factor
"""
import os                                    # lets us read environment variables (where the API key lives)
import sys                                   # lets us stop the program with a clear error message
from pathlib import Path                     # builds file paths that work on any computer

import pandas as pd                          # the DataFrame library
import requests                              # lets Python call the FRED web API
import statsmodels.formula.api as smf        # statsmodels' "formula" interface: write models like R, e.g. "y ~ x"
from dotenv import load_dotenv               # reads KEY=value lines from the .env file into os.environ

load_dotenv()                                # do it now, so FRED_API_KEY is available below (the key is NOT in this file)

# ---------------------------------------------------------------------------
# PRE-REGISTRATION (locked BEFORE looking at the data - no silent pivots!)
# If your squad registered a different sentence at standup, change it HERE and
# in reports/factor_writeup.md so the two match.
# ---------------------------------------------------------------------------
HYPOTHESIS = ("We hypothesize that Dallas-area unemployment is associated with Dallas "
              "homicide clearance, in the NEGATIVE direction.")
FRED_SERIES_ID = "LAUMT481910000000003A"     # unemployment rate, Dallas-Fort Worth-Arlington MSA, annual, 1990-
FACTOR_COLUMN = "unemployment"               # what we call the factor inside our DataFrames

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"   # the FRED endpoint from the week 12 supplement
SERIES_CSV = Path("reports/dallas_series.csv")                     # our week 9 clearance series (year, reported, cleared, clearance)
FACTOR_CSV = Path("data/dallas_unemployment.csv")                  # cache of the factor: fetch once, reuse forever
MERGED_CSV = Path("reports/factor_merged.csv")                     # the merged dataset (one of the lab's products)
SUMMARY_TXT = Path("reports/factor_ols_summary.txt")               # both OLS summaries, saved for the PR


def fetch_factor() -> pd.DataFrame:
    """Return a DataFrame with columns year, unemployment; download from FRED only if we have no cached copy."""
    if FACTOR_CSV.exists():                                       # cache hit: don't hammer the API on every run
        print(f"cached: {FACTOR_CSV}")
        return pd.read_csv(FACTOR_CSV)                            # load the saved copy and stop here

    key = os.environ.get("FRED_API_KEY")                          # .get() returns None instead of crashing if it's missing
    if not key:                                                   # no key = nothing we can do, so say why and quit
        sys.exit("FRED_API_KEY not found. Put FRED_API_KEY=... in a .env file in the repo root.")

    r = requests.get(FRED_URL, params={                           # build the URL ?series_id=...&api_key=... from this dict
        "series_id": FRED_SERIES_ID,                              # which series we want
        "api_key": key,                                           # who we are
        "file_type": "json",                                      # ask for JSON (lists and dicts in Python)
        "frequency": "a",                                         # annual (harmless here: the series is already annual)
        "aggregation_method": "avg",                              # if it were monthly, average each year
    }, timeout=60)                                                # give up after 60 seconds instead of hanging forever
    r.raise_for_status()                                          # fail loudly on a bad key / bad series (the quarantine instinct)

    df = pd.DataFrame(r.json()["observations"])                   # the answer is {"observations": [ {date, value, ...}, ... ]}
    df["year"] = df["date"].str[:4].astype(int)                   # "1990-01-01" -> first 4 characters -> the integer 1990
    df[FACTOR_COLUMN] = pd.to_numeric(df["value"], errors="coerce")   # FRED's missing value is the TEXT "." -> NaN, not a crash
    df = df[["year", FACTOR_COLUMN]].dropna()                     # keep two columns; drop years with no value (e.g. a future year)

    FACTOR_CSV.parent.mkdir(exist_ok=True)                        # make sure data/ exists before saving into it
    df.to_csv(FACTOR_CSV, index=False)                            # cache it so the next run skips the API
    print(f"saved: {FACTOR_CSV} ({len(df)} rows)")
    return df


def read_ols(model, term: str) -> dict:
    """Pull the three numbers the lab says to read aloud (coef, p-value, R-squared) plus n out of a fitted model."""
    return {
        "coef": model.params[term],                               # the slope: change in clearance per +1 of the factor
        "p": model.pvalues[term],                                 # could chance alone produce a slope this big? (small = unlikely)
        "r2": model.rsquared,                                     # share of the ups and downs in clearance the model explains
        "n": int(model.nobs),                                     # how many yearly observations the model actually used
    }


def main() -> None:
    print(HYPOTHESIS)                                             # print the locked hypothesis so the output documents itself

    # ---- 1. get the two datasets --------------------------------------------------------------
    if not SERIES_CSV.exists():                                   # the clearance series comes from week 9's series.py
        sys.exit(f"{SERIES_CSV} not found. Run `python -m src.series` first.")
    series = pd.read_csv(SERIES_CSV)                              # columns: year, reported, cleared, clearance
    factor = fetch_factor()                                       # columns: year, unemployment

    # ---- 2. merge on year, then EYEBALL before modeling -------------------------------------------
    # Both year columns must be the same type (int) or the merge returns 0 rows - the #1 error in the supplement.
    series["year"] = series["year"].astype(int)
    factor["year"] = factor["year"].astype(int)
    merged = series.merge(factor, on="year", how="inner")         # inner = keep only years that exist in BOTH files
    merged = merged.sort_values("year").reset_index(drop=True)    # sort by year so .shift(1) below really means "last year"
    print("\nmerged shape:", merged.shape)                         # (rows, columns): rows = years the two sources share
    print(merged.head())                                           # eyeball the first 5 rows
    print(f"years covered: {merged['year'].min()}-{merged['year'].max()}")

    years = merged["year"]                                        # a lag only makes sense if the years are consecutive
    if (years.diff().dropna() != 1).any():                        # .diff() = this year minus last year; every gap should be 1
        print("WARNING: gaps in the merged years - the lag-1 model compares non-adjacent years!")

    merged.to_csv(MERGED_CSV, index=False)                        # save the merged dataset (reports/ is committed, data/ is not)

    # ---- 3. the pre-registered model: clearance ~ unemployment ------------------------------------
    m1 = smf.ols(f"clearance ~ {FACTOR_COLUMN}", data=merged).fit()   # OLS = draw the best straight line through the points
    print("\n" + "=" * 78 + "\nPRIMARY MODEL: clearance ~ " + FACTOR_COLUMN + "\n" + "=" * 78)
    print(m1.summary())                                           # the full regression table (coef, std err, t, P>|t|, R-squared...)

    # ---- 4. the lag-1 variant: does LAST year's unemployment predict THIS year's clearance? -------
    lag_col = f"{FACTOR_COLUMN}_lag1"                             # name for the new column
    merged[lag_col] = merged[FACTOR_COLUMN].shift(1)              # shift(1) moves every value down one row = "the previous year"
    m2 = smf.ols(f"clearance ~ {lag_col}", data=merged.dropna()).fit()   # the first year has no previous year (NaN), so drop it
    print("\n" + "=" * 78 + "\nLAG-1 VARIANT: clearance ~ " + lag_col + "\n" + "=" * 78)
    print(m2.summary())

    # ---- 5. the numbers to read aloud and paste into the writeup ----------------------------------
    r1, r2 = read_ols(m1, FACTOR_COLUMN), read_ols(m2, lag_col)
    print("\n--- READ THESE ALOUD ---")
    print(f"clearance ~ factor:  coef = {r1['coef']:.4f}, p = {r1['p']:.4f}, R2 = {r1['r2']:.4f} (n = {r1['n']})")
    print(f"lag-1 variant:       coef = {r2['coef']:.4f}, p = {r2['p']:.4f}, R2 = {r2['r2']:.4f} (n = {r2['n']})")
    print(f"(coef is in clearance-rate units: {r1['coef'] * 100:+.2f} percentage points of clearance "
          f"per +1 point of unemployment)")

    # ---- 6. save both full summaries so they can go in the PR -------------------------------------
    SUMMARY_TXT.write_text(                                       # one text file holding both regression tables
        HYPOTHESIS + "\n\nPRIMARY MODEL\n" + str(m1.summary()) +
        "\n\nLAG-1 VARIANT\n" + str(m2.summary()) + "\n", encoding="utf-8")
    print(f"\nsaved: {MERGED_CSV}, {SUMMARY_TXT}")


if __name__ == "__main__":                                        # only runs when executed directly: python -m src.factor
    main()
