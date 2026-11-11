"""Map Dallas's 2007-2017 homicides by arrest outcome (week 10). Run from labs/: python -m src.casemap"""
import pandas as pd                          # the DataFrame library (wk9)
import folium                                # draws interactive web maps (Leaflet) from Python (wk10 slide 6)

w = pd.read_csv("data/wapo_dallas.csv")       # week 9's Dallas subset of the Washington Post file (names already dropped)
print("WaPo Dallas rows:", len(w))           # expect 1567

before = len(w)                              # row count before cleaning
w = w.dropna(subset=["lat", "lon"])          # a NaN lat/lon makes the map render blank, so drop those rows (supplement §2)
print("Rows dropped for missing lat/lon:", before - len(w))   # report how many we lost (honesty: say what you removed)

n_open = len(w[w["disposition"] == "Open/No arrest"])           # count of cases with no arrest and still open
n_arrest = len(w[w["disposition"] == "Closed by arrest"])       # count closed by an arrest
n_without = len(w[w["disposition"] == "Closed without arrest"]) # count closed with NO arrest (exceptional means)
print("Open:", n_open, "| Closed by arrest:", n_arrest, "| Closed without arrest:", n_without)   # expect 676 / 813 / 78

m = folium.Map(location=[32.78, -96.80],     # center the map on downtown Dallas (latitude, longitude)
               zoom_start=11)                # zoom level 11 = whole city visible; default OpenStreetMap basemap (slide 6)
# (the supplement's tiles="cartodbpositron" basemap now needs a CartoDB API key, so we keep the slide's default)

for _, row in w.iterrows():                  # one loop pass per case; _ is the row number we don't need
    if row["disposition"] == "Open/No arrest":           # unsolved: no arrest, case still open
        color = "orange"
    elif row["disposition"] == "Closed by arrest":       # solved by arrest - the ONLY "cleared" under WaPo's definition
        color = "green"
    else:                                                # "Closed without arrest" - closed, but nobody was arrested
        color = "gray"
    folium.CircleMarker(                     # a small circle (fixed pixel size at any zoom)
        location=[row["lat"], row["lon"]],   # where to put it: this case's coordinates
        radius=3,                            # 3 pixels across - small, because there are 1,567 of them
        color=color,                         # outline color chosen above
        fill=True,                           # fill the circle in...
        fill_opacity=0.6,                    # ...60% solid, so overlapping dots still show density
        weight=1,                            # thin outline
    ).add_to(m)                              # attach this dot to the map

legend = f"""
<div style="position:fixed;bottom:30px;left:30px;background:white;padding:8px 12px;
border:1px solid #999;font-family:sans-serif;font-size:13px;z-index:9999">
<b>Dallas homicides 2007–2017 (2017 partial)</b><br>
<span style="color:orange">●</span> Open / no arrest ({n_open})<br>
<span style="color:green">●</span> Closed by arrest ({n_arrest})<br>
<span style="color:gray">●</span> Closed without arrest ({n_without})<br>
Definition: Washington Post, arrest only<br>
Source: Washington Post Unsolved Homicide Database
</div>"""                                    # an HTML box (f-string fills in the counts); fixed = stays put while you pan
m.get_root().html.add_child(folium.Element(legend))   # insert that HTML box into the map's web page (supplement §2)

m.save("reports/dallas_map.html")            # write the map as a stand-alone web page; opens in any browser, embeds in wk14
print("saved: reports/dallas_map.html")      # confirm where the artifact went
