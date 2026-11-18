"""Tests for the offline part of src/fetch_city.py (no network, no token needed)."""
from src.fetch_city import flatten                 # the function that turns API rows into a flat table


def test_flatten_splits_geo_and_cleans_year():
    rows = [
        {"incidentnum": "1-2020", "servyr": "2020", "beat": "346",
         "geocoded_column": {"latitude": "32.7", "longitude": "-96.8"}},
        {"incidentnum": "2-1011", "servyr": "1011", "beat": "257",
         "geocoded_column": None},                 # missing geocode and a garbage year
    ]
    df = flatten(rows)
    assert "geocoded_column" not in df.columns     # nested column removed
    assert df.loc[0, "lat"] == 32.7 and df.loc[0, "lon"] == -96.8
    assert df.loc[1, "lat"] is None or df["lat"].isna()[1]   # missing geo becomes null, not a crash
    assert df["servyr"].tolist() == [2020, 1011]   # year converted from string to number
