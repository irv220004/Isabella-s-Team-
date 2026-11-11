"""Draw Dallas's 1965-2025 clearance trend chart (week 10). Run from labs/: python -m src.charts"""
import pandas as pd                          # the DataFrame library (wk9) - reads our week 9 CSV
import matplotlib.pyplot as plt              # matplotlib's plotting module, nicknamed plt by convention (wk10 slide 4)

s = pd.read_csv("reports/dallas_series.csv")   # week 9's output: one row per year (year, reported, cleared, clearance)
s["pct"] = s["clearance"] * 100                # new column: the 0-1 rate turned into a percent (0.58 -> 58.0)

# ---------------------------------------------------------------------------
# Honesty rule: gaps broken, not bridged (wk10 slide 5, supplement §1)
# ---------------------------------------------------------------------------
full = s.set_index("year").reindex(range(1965, 2026))   # one row for EVERY year 1965-2025; a missing year becomes NaN
missing = full[full["pct"].isna()].index.tolist()        # list the years that came back NaN (empty list = no gaps)
print("Missing years (line breaks here):", missing)      # say it out loud so the reviewer knows the line is whole or broken

complete = full.loc[1965:2024]                # every full year; 2025 is held back because it is a partial year
rolling = complete["pct"].rolling(5, center=True).mean()  # stretch goal: 5-year average centered on each year (smooths noise)

# ---------------------------------------------------------------------------
# The chart itself (wk10 slide 4)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 4.5))     # fig = the whole image, ax = the one plotting area inside it; 11x4.5 inches

ax.plot(complete.index, complete["pct"],      # x = year, y = clearance %; NaN years would leave a visible break in the line
        color="#196B24", lw=2.5, marker="o", markersize=3,   # dark green line from the slide, 2.5 wide, small dot on each year
        label="Yearly clearance")             # the text this line gets in the legend
ax.plot(complete.index, rolling,              # the rolling-average line on the same x axis
        color="#196B24", lw=1.5, alpha=0.35,  # same green but faint (alpha = transparency), so the yearly line stays the star
        label="5-year rolling average")       # legend text for the second line

pct_2025 = full.loc[2025, "pct"]              # .loc[row, column] pulls one value: 2025's clearance %
ax.plot([2025], [pct_2025], marker="o", markersize=7,   # draw 2025 as a single dot, NOT joined to the line
        markerfacecolor="white", color="#196B24",       # hollow dot = "this point is different" (partial year)
        linestyle="none", label="2025 (partial year)")  # linestyle none = just the dot; legend explains why it's hollow

# ---------------------------------------------------------------------------
# Labels: what, where, when, and whose definition (wk10 slide 5)
# ---------------------------------------------------------------------------
ax.set_ylim(0, 100)                           # rates get a 0-100 axis, period - no truncated baseline
ax.set_xlim(1963, 2027)                       # a little room on both ends so the first/last dots aren't cut off
ax.set_xlabel("Year")                         # x-axis label
ax.set_ylabel("Homicide clearance (%)\n"      # y-axis label, line 1: what is measured
              "FBI definition: arrest or exceptional means\n"   # line 2: whose definition of "cleared"
              "Source: FBI UCR via Murder Accountability Project")   # line 3: where the numbers came from
ax.set_title("Dallas Police Department homicide clearance rate, 1965–2025")   # what, where, when
ax.grid(alpha=0.3)                            # light background grid so readers can read values off the chart
ax.legend(loc="lower left")                   # show the legend box in the empty lower-left corner

# ---------------------------------------------------------------------------
# Make the week 9 argument on the chart: annotate the #1 suspicious year (wk10 slide 10, step 2)
# ---------------------------------------------------------------------------
yr = 2017                                     # our #1 suspicious year from src/series.py (biggest one-year jump in 61 years)
val = full.loc[yr, "pct"]                     # 2017's clearance %
change = val - full.loc[yr - 1, "pct"]        # how many points it rose from 2016
ax.annotate(f"{yr}: {val:.0f}% (+{change:.0f} pts in one year)\n"   # f-string: year, %, and jump size, rounded
            f"then {full.loc[yr + 1, 'pct']:.0f}% in {yr + 1} - backlog clearance?",   # line 2: the crash right after
            xy=(yr, val),                     # the point the arrow touches
            xytext=(1990, 93),                # where the text sits (top-middle, clear of the line)
            arrowprops=dict(arrowstyle="->"),  # draw an arrow from the text to the point
            fontsize=9)                       # slightly smaller text so it doesn't crowd the line

ax.annotate("2025: partial year,\nnot comparable",   # label the hollow dot so a screenshot can't be misread
            xy=(2025, pct_2025),              # point at the 2025 dot
            xytext=(2012, 20),                # text below and to the left, in empty space
            arrowprops=dict(arrowstyle="->"),  # arrow from text to dot
            fontsize=9)                       # same small size as the other note

fig.tight_layout()                            # shrink margins so the 3-line y label isn't cut off
fig.savefig("reports/clearance_trend.png", dpi=150, bbox_inches="tight")   # 150 dpi = sharp enough to publish (slide 4)
print("saved: reports/clearance_trend.png")   # confirm where the artifact went
