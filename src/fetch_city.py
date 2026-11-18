"""Fetch every murder incident from Dallas OpenData into data/case.db.
Run: python -m src.fetch_city"""
import json                                  # saves/loads the raw API response as a cache file
import os                                    # reads environment variables (where the token lives)
import sqlite3                               # Python's built-in SQLite database driver
from pathlib import Path                     # builds file paths that work on any computer
import pandas as pd                          # the DataFrame library
import requests                              # makes the HTTP calls to the API
from dotenv import load_dotenv               # loads KEY=value lines from the .env file
import truststore                            # makes Python trust the operating system's certificate store

truststore.inject_into_ssl()                 # fixes CERTIFICATE_VERIFY_FAILED on Windows; HTTPS checks stay ON

load_dotenv()                                # must run BEFORE os.environ is read, or the token is missing
URL = "https://www.dallasopendata.com/resource/qv6i-rri7.json"        # Police Incidents endpoint
WHERE = "offincident like '%MURDER%' OR offincident = 'HOMICIDE'"      # SODA filter: murder-type offenses only
RAW = Path("data/raw_incidents.json")        # cache of the untouched API response
DB = Path("data/case.db")                    # the SQLite database we build
PAGE = 5000                                  # rows requested per API call


def get_token() -> str:
    """Return the app token from .env, with a readable error if it is missing."""
    token = os.environ.get("DALLAS_APP_TOKEN")             # .get returns None instead of raising KeyError
    if not token:
        raise SystemExit("DALLAS_APP_TOKEN not set. Put it in .env (see wk11 supplement, section 2).")
    return token


def fetch_all() -> list[dict]:
    """Page through the API and return every matching row. Reuses the cache if it exists."""
    if RAW.exists():                         # already fetched once? don't hit the API again
        print("using cache", RAW)
        return json.loads(RAW.read_text())
    token = get_token()                      # only needed when we actually call the API
    rows, offset = [], 0                     # rows collected so far; how many we've skipped
    while True:
        r = requests.get(URL, params={       # params as a dict so requests URL-encodes the quotes and % for us
            "$where": WHERE,
            "$order": "incidentnum",         # stable order, otherwise paging can repeat rows
            "$limit": PAGE,
            "$offset": offset,
            "$$app_token": token,            # $$ is the literal SODA parameter name
        }, timeout=60)
        r.raise_for_status()                 # stop on HTTP 400/429/etc.
        page = r.json()                      # list of dicts, one per incident
        rows.extend(page)
        print(f"offset {offset}: {len(page)} rows")
        if len(page) < PAGE:                 # a short page means it was the last one
            break
        offset += PAGE                       # move to the next page
    RAW.parent.mkdir(exist_ok=True)          # make sure data/ exists
    RAW.write_text(json.dumps(rows))         # cache for next time
    return rows


def flatten(rows: list[dict]) -> pd.DataFrame:
    """Turn the API rows into a flat table SQLite can store."""
    df = pd.DataFrame(rows)
    geo = df.pop("geocoded_column")          # nested dict column; remove it so we can split it
    df["lat"] = geo.apply(lambda g: float(g["latitude"]) if isinstance(g, dict) else None)
    df["lon"] = geo.apply(lambda g: float(g["longitude"]) if isinstance(g, dict) else None)
    df = df[[c for c in df.columns if not c.startswith(":@")]]   # drop computed-region columns
    df["servyr"] = pd.to_numeric(df["servyr"], errors="coerce")  # API stores year as a string; bad values -> NaN
    return df


def main() -> None:
    df = flatten(fetch_all())
    DB.parent.mkdir(exist_ok=True)           # make sure data/ exists
    con = sqlite3.connect(DB)                # creates case.db if it isn't there
    df.to_sql("incidents", con, if_exists="replace", index=False)   # rerunning rebuilds the table cleanly
    n = pd.read_sql("SELECT COUNT(*) AS n FROM incidents", con).n[0]
    con.close()
    print(f"case.db: {n} rows in incidents (expect roughly 1,100 to 1,250)")


if __name__ == "__main__":                   # only when run directly: python -m src.fetch_city
    main()
