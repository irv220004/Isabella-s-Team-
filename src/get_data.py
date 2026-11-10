"""Download the week 9 sources into data/. Run: python -m src.get_data"""
from pathlib import Path                     # builds file paths that work on any computer (Windows/Mac/Linux)
import pandas as pd                          # the DataFrame library - "a spreadsheet with superpowers"
import requests                              # lets Python download a file from a URL

DATA = Path("data")                          # the folder everything gets saved into
DATA.mkdir(exist_ok=True)                    # create it if it doesn't exist yet; do nothing if it does

MAP_URL = ("https://www.dropbox.com/scl/fi/4y2a6yy0pv4lxffm7sa4v/UCR65_25.csv"
           "?rlkey=jhs7ktqhb9h3dnml1wety4nhb&st=7rxppnar&dl=1")        # the FBI/MAP homicide archive
WAPO_URL = ("https://raw.githubusercontent.com/washingtonpost/"
            "data-homicides/master/homicide-data.csv")                 # the Washington Post's full file


def fetch(url: str, dest: Path) -> None:
    """Download url to dest, unless dest already exists."""
    if dest.exists():                        # don't re-download a file we already have
        print(f"cached: {dest}")
        return                                # stop here, nothing more to do
    r = requests.get(url, timeout=120)        # actually make the HTTP request; wait up to 120 seconds
    r.raise_for_status()                      # raise an error now if the server returned a failure code
    dest.write_bytes(r.content)               # save the raw downloaded bytes straight to disk
    print(f"saved: {dest} ({dest.stat().st_size:,} bytes)")   # :, adds thousands separators to the byte count


def main() -> None:
    fetch(MAP_URL, DATA / "map_ucr.csv")               # download dataset 1 (every US agency, 1965-2025)
    fetch(WAPO_URL, DATA / "wapo_all.csv")             # download dataset 2 (all 50 cities)

    # the Post's file is Latin-1, not UTF-8; without this pandas raises UnicodeDecodeError
    wapo = pd.read_csv(DATA / "wapo_all.csv", encoding="latin-1")   # load the big file into a DataFrame
    dallas = wapo[wapo["city"] == "Dallas"].drop(                   # keep only Dallas rows...
        columns=["victim_last", "victim_first"])                    # ...and drop the victim name columns
    dallas.to_csv(DATA / "wapo_dallas.csv", index=False)             # save just the Dallas subset
    print(f"wapo_dallas.csv: {len(dallas)} rows (expect 1567)")      # len() on a DataFrame counts its rows


if __name__ == "__main__":                   # only runs when this file is executed directly,
    main()                                    # e.g. `python -m src.get_data` - not when another file imports it
