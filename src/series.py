"""Build Dallas's FBI-reported clearance series. Run: python -m src.series"""
import pandas as pd

df = pd.read_csv("data/map_ucr.csv")
print(df.shape)
print(df.columns.tolist())
print(df.head())

dallas = df[df["ORI"] == "TXDPD00"]            # filter on ORI, not Agency name (4 "Dallas" agencies exist)
print("Dallas PD rows:", len(dallas))           # expect 61

per_year = dallas.groupby("YEAR").agg(
    reported=("MRD", "sum"),
    cleared=("CLR", "sum"),
)
per_year["clearance"] = per_year["cleared"] / per_year["reported"]
per_year.index.name = "year"
per_year.to_csv("reports/dallas_series.csv")

# ---------------------------------------------------------------------------
# The three mandatory sanity checks (wk9 §5)
# ---------------------------------------------------------------------------

print("\n--- Sanity check 1: clearance rates over 100% ---")
print(per_year[per_year.clearance > 1])

print("\n--- Sanity check 2: missing years (1965-2025) ---")
years = set(per_year.index)
print(sorted(set(range(1965, 2026)) - years))

print("\n--- Sanity check 3: biggest year-over-year jumps in clearance ---")
jumps = per_year.clearance.diff().abs().sort_values(ascending=False).head(5)
print(jumps)

# ---------------------------------------------------------------------------
# The 5 most suspicious years, with one line of reasoning each
# ---------------------------------------------------------------------------

print("\n--- 5 most suspicious years ---")
suspicious = [
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
for year, reason in suspicious:
    row = per_year.loc[year]
    print(f"  {year}: reported={int(row.reported)} cleared={int(row.cleared)} "
          f"clearance={row.clearance:.1%} - {reason}")
