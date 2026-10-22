# Week 10 Supplement — The Picture: matplotlib and folium

Companion to deck 10. Lab: Operation The Picture.

**Data this week:** no new downloads. You use your own `reports/dallas_series.csv` from week 9 and `data/wapo_dallas.csv` (rebuilt by `python -m src.get_data` if anyone's `data/` is empty).

**Install before class** (inside the venv, then freeze):
```bash
pip install matplotlib folium
pip freeze > requirements.txt
```

**For next week (do it tonight):** register a free Dallas OpenData app token. Steps are in `wk11_supplement_live_evidence.md`, section 2. Week 11 does not work without it.

---

## 1. The trend chart: `src/charts.py`

```python
import pandas as pd
import matplotlib.pyplot as plt

s = pd.read_csv("reports/dallas_series.csv")
s["pct"] = s.clearance * 100

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(s.year, s.pct, marker="o", linewidth=1.5)

ax.set_ylim(0, 100)
ax.set_xlabel("Year")
ax.set_ylabel("Homicide clearance (%)\nSource: FBI UCR via Murder Accountability Project")
ax.set_title("Dallas Police Department homicide clearance rate, 1965–2025")
ax.grid(alpha=0.3)

# annotate your #1 suspicious year
yr = 2017
val = float(s.loc[s.year == yr, "pct"].iloc[0])
ax.annotate(f"{yr}: {val:.0f}% — reporting change?",
            xy=(yr, val), xytext=(yr - 12, val + 8),
            arrowprops=dict(arrowstyle="->"))

fig.tight_layout()
fig.savefig("reports/clearance_trend.png", dpi=150)
```

**The honesty checklist the reviewer applies:**

| Check | Why |
|---|---|
| y-axis runs 0 to 100 | A 40–80 axis makes a 10-point dip look like a collapse |
| Source named in the axis label | "Clearance" by whose definition? The FBI's. Say so. |
| Gaps broken, not bridged | If a year is missing, the line must break. `plt.plot` bridges by default. Reindex to the full year range so missing years are NaN. |
| Partial years marked | 2025 is incomplete. Either drop it or label it. |
| Title says what, where, when | "Clearance" alone is not a title |

To break gaps:
```python
full = s.set_index("year").reindex(range(1965, 2026))
ax.plot(full.index, full.pct * 1)   # NaN rows produce a visible break
```

## 2. The map: `src/casemap.py`

```python
import pandas as pd
import folium

w = pd.read_csv("data/wapo_dallas.csv")

m = folium.Map(location=[32.78, -96.80], zoom_start=11, tiles="cartodbpositron")

for _, row in w.iterrows():
    color = "orange" if row.disposition == "Open/No arrest" else "green"
    folium.CircleMarker(
        location=[row.lat, row.lon],
        radius=3, color=color, fill=True, fill_opacity=0.6, weight=1,
    ).add_to(m)

legend = """
<div style="position:fixed;bottom:30px;left:30px;background:white;padding:8px 12px;
border:1px solid #999;font-family:sans-serif;font-size:13px;z-index:9999">
<b>Dallas homicides 2007–2017</b><br>
<span style="color:orange">●</span> Open / no arrest (676)<br>
<span style="color:green">●</span> Closed (891)<br>
Source: Washington Post Unsolved Homicide Database
</div>"""
m.get_root().html.add_child(folium.Element(legend))

m.save("reports/dallas_map.html")
```

1,567 markers. Open the file in a browser. The orange should pool in southeast Dallas and along the Forest Lane / Audelia Road corridor in the northeast. Write two sentences in the PR about where it pools and where it does not.

If the map renders blank: a `lat` or `lon` is NaN. `w = w.dropna(subset=["lat", "lon"])` and report how many rows you dropped.

## 3. Two audiences, two artifacts

- `reports/clearance_trend.png` is for a newsroom. It must survive being screenshotted without its caption.
- `reports/dallas_map.html` is for a council office. It embeds in week 14's dashboard as-is.

Both scripts must run from a fresh clone after `python -m src.get_data` and `python -m src.series`.

## 4. Results checklist

- [ ] `src/charts.py` → `reports/clearance_trend.png`, 0–100 axis, source in label, suspicious year annotated
- [ ] `src/casemap.py` → `reports/dallas_map.html`, 1,567 markers, colored by disposition, legend present
- [ ] Two written observations about where the orange pools, in the PR
- [ ] Reviewer opened both files before approving
- [ ] Merged via reviewed PR
- [ ] Dallas OpenData app token registered for every detective

## 5. Stretch

- 5-year rolling average: `s.pct.rolling(5, center=True).mean()` as a second line, lighter color.
- Color markers by `victim_age` bucket instead of disposition (`pd.cut` on the numeric age, `Unknown` becomes its own color).
- Screenshot the map to `reports/dallas_map.png` so the README can show it.
