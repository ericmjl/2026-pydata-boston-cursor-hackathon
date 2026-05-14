import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    import json
    import pathlib
    import urllib.request

    import marimo as mo
    import matplotlib.cm as mcm
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    return json, mcm, mo, np, pathlib, pd, plt, urllib


@app.cell
def _(mo):
    title_md = mo.md(
        r"""
# 🚇 Are You Safe Near Your T Stop? Boston Crime Analysis

Crime incidents (2023–present) from [Analyze Boston](https://data.boston.gov/) counted within **400 m** of each MBTA subway stop, heavy rail + light rail.
"""
    )
    return (title_md,)


@app.cell
def _(pathlib, pd, urllib):
    notebook_dir = pathlib.Path(__file__).resolve().parent
    data_dir = notebook_dir / "data"
    crime_path = data_dir / "crime.csv"
    crime_url = (
        "https://data.boston.gov/dataset/6220d948-eae2-4e4b-8723-2dc8e67722a3/"
        "resource/b973d8cb-eeb2-4e7e-99da-c92938efc9c0/download/tmpcyl1hw5w.csv"
    )
    data_dir.mkdir(parents=True, exist_ok=True)
    if not crime_path.exists():
        urllib.request.urlretrieve(crime_url, crime_path)
    crime_df = pd.read_csv(crime_path, low_memory=False)
    crime_df["Lat"] = pd.to_numeric(crime_df["Lat"], errors="coerce")
    crime_df["Long"] = pd.to_numeric(crime_df["Long"], errors="coerce")
    crime_df = crime_df.dropna(subset=["Lat", "Long"])
    return (crime_df,)


@app.cell
def _(json, pd, urllib):
    mbta_url = "https://api-v3.mbta.com/stops?filter%5Broute_type%5D=0,1"
    with urllib.request.urlopen(mbta_url) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    rows = []
    for item in payload.get("data", []):
        attrs = item.get("attributes") or {}
        name = attrs.get("name")
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if name is None or lat is None or lon is None:
            continue
        rows.append({"stop_name": str(name), "lat": float(lat), "lon": float(lon)})
    stops_raw = pd.DataFrame(rows)
    return (stops_raw,)


@app.cell
def _(crime_df, np, stops_raw):
    def haversine_m(lat1, lon1, lat2_arr, lon2_arr):
        r = 6_371_000.0
        p1 = np.radians(lat1)
        p2 = np.radians(lat2_arr)
        dp = np.radians(lat2_arr - lat1)
        dl = np.radians(lon2_arr - lon1)
        a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
        return 2.0 * r * np.arcsin(np.minimum(1.0, np.sqrt(a)))

    clat = crime_df["Lat"].to_numpy(dtype=np.float64)
    clon = crime_df["Long"].to_numpy(dtype=np.float64)
    counts = []
    for _, _row in stops_raw.iterrows():
        d = haversine_m(_row["lat"], _row["lon"], clat, clon)
        counts.append(int((d <= 400.0).sum()))
    stops_df = stops_raw.copy()
    stops_df["crime_count"] = counts
    return (stops_df,)


@app.cell
def _(mo, plt, stops_df):
    import matplotlib.colormaps as _cm
    top20 = stops_df.nlargest(20, "crime_count").sort_values("crime_count", ascending=True)
    vals = top20["crime_count"].to_numpy()
    norm = plt.Normalize(vmin=vals.min(), vmax=vals.max())
    bar_colors = _cm["YlOrRd"](norm(vals))
    _fig, _ax = plt.subplots(figsize=(10, 8))
    _ax.barh(top20["stop_name"], top20["crime_count"], color=bar_colors, edgecolor="0.35")
    _ax.set_xlabel("Crimes within 400 m (2023-present)")
    _ax.set_title("Top 20 MBTA subway stops by nearby crime count")
    _fig.tight_layout()
    return mo.as_html(_fig)


@app.cell
def _(mo, plt, stops_df):
    _fig2, _ax2 = plt.subplots(figsize=(10, 8))
    c = stops_df["crime_count"].to_numpy()
    s = 25 + 350 * (c - c.min()) / (c.max() - c.min() + 1e-9)
    sc = _ax2.scatter(
        stops_df["lon"], stops_df["lat"],
        s=s, c=c, cmap="YlOrRd", alpha=0.85, edgecolors="0.25", linewidths=0.4,
    )
    _fig2.colorbar(sc, ax=_ax2, shrink=0.72, label="Crimes within 400 m")
    _ax2.set_xlabel("Longitude")
    _ax2.set_ylabel("Latitude")
    _ax2.set_title("MBTA subway stops: crime density (size and color)")
    _ax2.set_aspect("equal", adjustable="box")
    top10 = stops_df.nlargest(10, "crime_count")
    for _, _row in top10.iterrows():
        _ax2.annotate(
            _row["stop_name"], (_row["lon"], _row["lat"]),
            textcoords="offset points", xytext=(4, 4), fontsize=7, alpha=0.95,
        )
    _fig2.tight_layout()
    return mo.as_html(_fig2)


@app.cell
def _(mo):
    radius_slider = mo.ui.slider(start=200, stop=800, step=200, value=400, label="Search radius (m)")
    return (radius_slider,)


@app.cell
def _(crime_df, mo, np, plt, radius_slider, stops_raw):
    import matplotlib.colormaps as _cm2
    r_m = float(radius_slider.value)

    def _hav(lat1, lon1, lat2_arr, lon2_arr):
        _R = 6_371_000.0
        p1 = np.radians(lat1)
        p2 = np.radians(lat2_arr)
        dp = np.radians(lat2_arr - lat1)
        dl = np.radians(lon2_arr - lon1)
        a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
        return 2.0 * _R * np.arcsin(np.minimum(1.0, np.sqrt(a)))

    _cr_lat = crime_df["Lat"].to_numpy(dtype=np.float64)
    _cr_lon = crime_df["Long"].to_numpy(dtype=np.float64)
    _counts2 = []
    for _, _s in stops_raw.iterrows():
        _d = _hav(_s["lat"], _s["lon"], _cr_lat, _cr_lon)
        _counts2.append(int((_d <= r_m).sum()))
    _stops_r = stops_raw.copy()
    _stops_r["crime_count"] = _counts2
    _top20r = _stops_r.nlargest(20, "crime_count").sort_values("crime_count", ascending=True)
    _vals2 = _top20r["crime_count"].to_numpy()
    _norm2 = plt.Normalize(vmin=_vals2.min(), vmax=_vals2.max())
    _bar_colors2 = _cm2["YlOrRd"](_norm2(_vals2))
    _fig3, _ax3 = plt.subplots(figsize=(10, 8))
    _ax3.barh(_top20r["stop_name"], _top20r["crime_count"], color=_bar_colors2, edgecolor="0.35")
    _ax3.set_xlabel(f"Crimes within {int(r_m)} m (2023-present)")
    _ax3.set_title(f"Top 20 MBTA stops — {int(r_m)} m radius")
    _fig3.tight_layout()
    interactive_view = mo.vstack([
        mo.md("## Interactive: Adjust Search Radius"),
        radius_slider,
        mo.md(f"Showing crimes within **{int(r_m)} m** of each stop."),
        mo.as_html(_fig3),
    ])
    return (interactive_view,)


@app.cell
def _(crime_df, mo, np, plt, stops_raw):
    fc_stops = stops_raw[stops_raw["stop_name"] == "Fields Corner"]
    if len(fc_stops) == 0:
        fields_view = mo.md("*No Fields Corner stops found.*")
    else:
        def _hav_fc(lat1, lon1, lat2_arr, lon2_arr):
            _R = 6_371_000.0
            p1 = np.radians(lat1)
            p2 = np.radians(lat2_arr)
            dp = np.radians(lat2_arr - lat1)
            dl = np.radians(lon2_arr - lon1)
            a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
            return 2.0 * _R * np.arcsin(np.minimum(1.0, np.sqrt(a)))

        _fc_lat = crime_df["Lat"].to_numpy(dtype=np.float64)
        _fc_lon = crime_df["Long"].to_numpy(dtype=np.float64)
        _min_d = np.full(_fc_lat.shape, np.inf, dtype=np.float64)
        for _, _s in fc_stops.iterrows():
            _d = _hav_fc(_s["lat"], _s["lon"], _fc_lat, _fc_lon)
            _min_d = np.minimum(_min_d, _d)
        _near = crime_df.loc[_min_d <= 400.0].copy()
        _near["OFFENSE_DESCRIPTION"] = _near["OFFENSE_DESCRIPTION"].fillna("Unknown")
        _vc = _near["OFFENSE_DESCRIPTION"].value_counts().head(10)
        _fig4, _ax4 = plt.subplots(figsize=(10, 6))
        _ax4.barh(_vc.index[::-1], _vc.values[::-1], color="steelblue", edgecolor="0.3")
        _ax4.set_xlabel("Incident count")
        _ax4.set_title("Fields Corner: top 10 offense types within 400 m")
        _fig4.tight_layout()
        fields_view = mo.vstack([
            mo.md("## What Kind of Crimes Happen at Fields Corner?"),
            mo.as_html(_fig4),
        ])
    return (fields_view,)


@app.cell
def _(mo, stops_df):
    by_name = (
        stops_df.groupby("stop_name", as_index=False)["crime_count"]
        .sum()
        .sort_values("crime_count", ascending=False)
        .reset_index(drop=True)
    )
    top1_n = int(by_name.loc[0, "crime_count"])
    top1_name = str(by_name.loc[0, "stop_name"])
    top2_n = int(by_name.loc[1, "crime_count"])
    top2_name = str(by_name.loc[1, "stop_name"])
    pct_more = 100.0 * (top1_n - top2_n) / max(top2_n, 1)
    top5_pct = 100.0 * by_name.head(5)["crime_count"].sum() / max(by_name["crime_count"].sum(), 1)
    safest_row = by_name.sort_values("crime_count").iloc[0]

    insight = mo.md(f"""
## Key Findings

- **{top1_name}** is the most crime-dense stop: **{top1_n:,} incidents** within 400 m — **{pct_more:.0f}% more** than #2 ({top2_name}, {top2_n:,}).
- The **top 5 stops** account for **{top5_pct:.1f}%** of all station-level crime counts.
- Safest stop: **{safest_row["stop_name"]}** with only **{int(safest_row["crime_count"])}** nearby incidents.
- **Method:** Haversine distance from each BPD crime report GPS coordinate to each MBTA stop. 400 m ≈ 5-minute walk.
""")
    return (insight,)


if __name__ == "__main__":
    app.run()