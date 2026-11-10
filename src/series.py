"""Build Dallas's FBI-reported clearance series. Run: python -m src.series"""
import pandas as pd                          # the DataFrame library

df = pd.read_csv("data/map_ucr.csv")          # load the full national archive into a DataFrame
print(df.shape)                               # (rows, columns) - the very first thing to check on any file
print(df.columns.tolist())                    # what fields actually exist (don't assume, read it)
print(df.head())                              # eyeball the first 5 rows to sanity-check the load

dallas = df[df["ORI"] == "TXDPD00"]            # filter on ORI, not Agency name (4 "Dallas" agencies exist)
print("Dallas PD rows:", len(dallas))           # expect 61

per_year = dallas.groupby("YEAR").agg(         # one group (bucket) per distinct year
    reported=("MRD", "sum"),                   # new column "reported" = sum of MRD within each year-bucket
    cleared=("CLR", "sum"),                    # new column "cleared"  = sum of CLR within each year-bucket
)
per_year["clearance"] = per_year["cleared"] / per_year["reported"]   # a brand-new column, computed from the other two
per_year.index.name = "year"                   # rename the index (currently "YEAR") to lowercase "year"
per_year.to_csv("reports/dallas_series.csv")   # write it out - this is Deliverable #1's skeleton

# ---------------------------------------------------------------------------
# The three mandatory sanity checks (wk9 §5)
# ---------------------------------------------------------------------------

print("\n--- Sanity check 1: clearance rates over 100% ---")
print(per_year[per_year.clearance > 1])        # filter to rows where the rate is impossible on its face

print("\n--- Sanity check 2: missing years (1965-2025) ---")
years = set(per_year.index)                     # every year actually present in the data, as a set
print(sorted(set(range(1965, 2026)) - years))   # set subtraction: every expected year MINUS the ones we have

print("\n--- Sanity check 3: biggest year-over-year jumps in clearance ---")
jumps = per_year.clearance.diff().abs().sort_values(ascending=False).head(5)
# .diff()            each year's value minus the PREVIOUS year's value
# .abs()              make every difference positive (a drop and a rise both count as a "jump")
# .sort_values(...)   biggest jump first
# .head(5)            keep only the top 5
print(jumps)

# ---------------------------------------------------------------------------
# The 5 most suspicious years, with one line of reasoning each
# ---------------------------------------------------------------------------

print("\n--- 5 most suspicious years ---")
suspicious = [                                  # a list of (year, reason) pairs, chosen from the checks above
    (2007, "Clearance drops from 80.7% in 2006 to 58.0% - the start of a 2007-2011 slide "
           "that never fully recovers, unlike the usual year-to-year noise seen elsewhere "
           "in the series."),
    (2017, "The single biggest upward jump in the whole 61-year series (+29.9 points). A "
           "spike this size in one year usually means a backlog of old cases got cleared "
           "together, not that casework suddenly got much faster."),
    (2018, "The single biggest downward jump in the whole series (-39.8 points), the very "
           "next year after 2017's spike - consistent with 2017 pulling cleared cases out "
           "of the normal pipeline early rather than a real one-year collapse in policing."),
    (2025, "Partial year - the FBI/MAP count for 2025 is still being reported, so both "
           "'reported' and 'cleared' are undercounts and the rate isn't comparable to a "
           "full year yet."),
    (1974, "A one-year dip to 68.9% sandwiched between 1973 (90.4%) and 1975 (89.0%) - an "
           "isolated single-year swing with no visible cause in the data itself, worth a "
           "second look rather than averaging it away."),
]
for year, reason in suspicious:                 # unpack each (year, reason) pair in turn
    row = per_year.loc[year]                     # .loc[year] pulls out that one row by its index label
    print(f"  {year}: reported={int(row.reported)} cleared={int(row.cleared)} "
          f"clearance={row.clearance:.1%} - {reason}")
