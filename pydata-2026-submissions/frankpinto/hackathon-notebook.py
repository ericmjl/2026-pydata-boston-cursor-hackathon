# /// script
# dependencies = [
#     "marimo",
#     "polars==1.40.1",
#     "plotly==6.7.0",
#     "pyarrow==24.0.0",
# ]
# requires-python = ">=3.11"
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import plotly.graph_objects as go

    return mo, Path, pl, go


@app.cell(hide_code=True)
def intro_vat_md(mo):
    mo.md(r"""
    # UK revenue: actual vs VAT-free growth benchmark

    UK **standard VAT** rose from **17.5%** to **20%** on **4 January 2011**.

    This notebook compares **recorded monthly revenue** from the Online Retail dataset to a **counterfactual path** built from **year-one seasonality** and growth in **deseasonalized 3-month trailing averages**. This is **not** a reconstruction of VAT-exclusive prices — only a transparent **growth + seasonality** benchmark. With barely one calendar year of data, seasonality is weakly identified and the counterfactual is illustrative.
    """)
    return


@app.cell(hide_code=True)
def assumptions_md(mo):
    mo.md(r"""
    ## Method and caveats

    - **Metric:** `Quantity * UnitPrice` per line, excluding invoices whose `InvoiceNo` starts with `C` (cancellations).
    - **Seasonality:** multiplicative indices from year-one monthly revenue: each calendar month’s index is that month’s revenue divided by the mean of the twelve year-one monthly totals (indices average to 1).
    - **Growth `g`:** compound monthly growth fitted on the **deseasonalized** 3-month **trailing** rolling average from the first month with a full window through the end of year one.
    - **Counterfactual:** anchored to **December 2010** deseasonalized level; from **January 2011** onward, the deseasonalized series is stepped forward by `(1+g)` each month and multiplied by the same seasonal indices. **Region = All countries** shows actual totals only (no VAT counterfactual).
    """)
    return


@app.cell(hide_code=True)
def scope_picker(mo):
    scope_picker = mo.ui.dropdown(
        options={
            "United Kingdom": "United Kingdom",
            "All countries": "All countries",
        },
        value="United Kingdom",
        label="Region",
    )
    return (scope_picker,)


@app.cell(hide_code=True)
def cleaned_data_context_md(mo):
    mo.md(r"""
    ## Cleaned line-level data

    Skimming the **row-level** table after light cleaning is useful because cancellations (`InvoiceNo` starting with `C`) and bad timestamps silently distort aggregates. Here you can spot obvious spikes, returns-heavy rows, and whether the UK filter (when selected below) leaves enough volume for a stable monthly series.
    """)
    return


@app.cell(hide_code=True)
def load_and_clean(mo, Path, pl):
    candidates = []
    nb_dir = getattr(mo, "notebook_dir", None)
    if callable(nb_dir):
        try:
            candidates.append(Path(nb_dir()) / "data" / "OnlineRetail.csv")
        except Exception:
            pass
    try:
        candidates.append(Path(__file__).resolve().parent / "data" / "OnlineRetail.csv")
    except NameError:
        pass
    candidates.extend(
        [
            Path("data") / "OnlineRetail.csv",
            Path("pydata-2026-submissions") / "frankpinto" / "data" / "OnlineRetail.csv",
        ]
    )
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            "OnlineRetail.csv not found. Tried: " + ", ".join(str(p) for p in candidates)
        )

    raw = pl.read_csv(
        path,
        infer_schema_length=5000,
        null_values=["", "NA"],
    )
    df_raw = raw.with_columns(
        pl.col("InvoiceDate")
        .cast(pl.Utf8)
        .str.replace_all(r"(\d{4}-\d{2}-\d{2}) (\d):", r"$1 0$2:")
        .str.to_datetime("%Y-%m-%d %H:%M", strict=False)
        .alias("InvoiceDate"),
    ).with_columns(
        (pl.col("Quantity").cast(pl.Float64) * pl.col("UnitPrice").cast(pl.Float64)).alias(
            "line_total"
        )
    )
    df_clean = (
        df_raw.filter(~pl.col("InvoiceNo").cast(pl.Utf8).str.starts_with("C"))
        .filter(
            pl.col("InvoiceDate").is_not_null(),
            pl.col("Quantity").is_not_null(),
            pl.col("UnitPrice").is_not_null(),
        )
    )
    return (df_clean,)


@app.cell(hide_code=True)
def monthly_series_context_md(mo):
    mo.md(r"""
    ## Monthly revenue (chosen region)

    **Why this view matters:** VAT hits demand and/or list prices at **monthly** business cadence, so we aggregate to calendar months before any rolling average. The filled month grid makes missing months explicit (zeros) instead of silently connecting points across gaps—important when comparing a model line to **real** seasonality.
    """)
    return


@app.cell(hide_code=True)
def monthly_series(df_clean, pl, scope_picker):
    base = df_clean
    if scope_picker.value == "United Kingdom":
        base = base.filter(pl.col("Country") == "United Kingdom")

    df_m = (
        base.with_columns(pl.col("InvoiceDate").dt.truncate("1mo").alias("month"))
        .group_by("month")
        .agg(pl.col("line_total").sum().alias("revenue"))
        .sort("month")
    )
    span_start = df_m["month"].min()
    span_end = df_m["month"].max()
    month_grid = pl.DataFrame(
        {"month": pl.datetime_range(span_start, span_end, interval="1mo", eager=True)}
    )
    df_monthly = month_grid.join(df_m, on="month", how="left").with_columns(
        pl.col("revenue").fill_null(0.0)
    )
    return (df_monthly,)


@app.cell(hide_code=True)
def counterfactual_model(df_monthly, pl, scope_picker):
    df_sorted = df_monthly.sort("month")
    df_year1 = df_sorted.head(12)
    mean_y1 = float(df_year1["revenue"].mean())
    if mean_y1 == 0.0:
        mean_y1 = 1.0

    lookup = df_year1.with_columns(
        pl.col("month").dt.month().alias("cal_m"),
        (pl.col("revenue") / mean_y1).alias("seasonal_index"),
    ).select("cal_m", "seasonal_index")

    lm = df_monthly.with_columns(pl.col("month").dt.month().alias("cal_m"))
    df_enriched = (
        lm.join(lookup, on="cal_m", how="left")
        .drop("cal_m")
        .sort("month")
        .with_columns(pl.col("seasonal_index").fill_null(1.0))
        .with_columns(
            pl.col("revenue")
            .rolling_mean(window_size=3, min_samples=3)
            .alias("roll3")
        )
    )

    fit_frame = (
        df_enriched.join(df_year1.select("month"), on="month", how="inner")
        .with_columns((pl.col("roll3") / pl.col("seasonal_index")).alias("deseas_roll3"))
        .filter(pl.col("roll3").is_not_null())
    )

    g = 0.0
    if fit_frame.height > 1:
        a = float(fit_frame["deseas_roll3"][0])
        b = float(fit_frame["deseas_roll3"][-1])
        n = fit_frame.height
        if a > 0 and b > 0:
            g = (b / a) ** (1.0 / (n - 1)) - 1.0

    anchor = pl.datetime(2010, 12, 1)
    jan2011 = __import__("datetime").datetime(2011, 1, 1)

    if scope_picker.value != "United Kingdom":
        df_chart = df_enriched.with_columns(
            pl.lit(float("nan")).alias("counterfactual")
        )
    else:
        anchor_row = df_enriched.filter(pl.col("month") == anchor).head(1)
        if anchor_row.height == 0:
            L = float(fit_frame["deseas_roll3"][0]) if fit_frame.height else 0.0
        else:
            L = float(anchor_row["revenue"][0]) / float(anchor_row["seasonal_index"][0])

        months_sorted = df_enriched.sort("month")
        cf_vals = []
        L_curr = None
        for row in months_sorted.iter_rows(named=True):
            m_raw = row["month"]
            rev = float(row["revenue"])
            if isinstance(m_raw, __import__("datetime").datetime):
                m_py = m_raw.replace(tzinfo=None)
            else:
                m_py = __import__("datetime").datetime.fromisoformat(str(m_raw)[:19])
            s = float(row["seasonal_index"])
            if m_py < jan2011:
                # Show year-one actuals on the counterfactual trace so the chart spans the full first year.
                cf_vals.append(rev)
            elif m_py.year == jan2011.year and m_py.month == jan2011.month:
                L_curr = L * (1.0 + g)
                cf_vals.append(L_curr * s)
            else:
                L_curr = L_curr * (1.0 + g)
                cf_vals.append(L_curr * s)

        df_chart = months_sorted.with_columns(pl.Series("counterfactual", cf_vals))

    return df_chart, g, mean_y1


@app.cell(hide_code=True)
def diagnostics_context_md(mo):
    mo.md(r"""
    ## Model diagnostics

    The fitted **monthly growth** and year-one **average level** summarize what the counterfactual “believes” about trend after stripping seasonal indices from the smoothed series. These numbers are easy to sanity-check: if growth looks absurd, the VAT story is probably not what’s moving the needle.
    """)
    return


@app.cell(hide_code=True)
def validation_summary(df_chart, df_clean, g, mean_y1, mo):
    summary_md = mo.md(
        f"""
    **Diagnostics** (counterfactual only for United Kingdom)  
    Year-one mean monthly revenue: **£{mean_y1:,.0f}**  
    Fitted compound monthly growth on deseasonalized rolling-3m: **{g * 100:.3f}%**  
    Rows after cleaning: **{df_clean.height:,}** — months in chart: **{df_chart.height}**
    """
    )
    return summary_md


@app.cell(hide_code=True)
def chart_context_md(mo):
    mo.md(r"""
    ## Actual vs counterfactual (full sample including year one)

    **Why this chart is the payoff:** you see **recorded revenue** against a **counterfactual** built only from early-year seasonality and smoothed growth—so divergences after the VAT line are easier to interpret as “model vs reality,” not as a second y-axis trick. The **3-month rolling average** shows the signal the model actually fitted (less month-to-month noise). The shaded **first year** band marks the window used to estimate seasonality and `g`, so you can judge whether post-VAT months sit inside a plausible continuation or not.
    """)
    return


@app.cell(hide_code=True)
def plot_actual_vs_cf(df_chart, go, scope_picker):
    import datetime as dt

    vat_day = dt.datetime(2011, 1, 4)
    dfc = df_chart.sort("month")
    xs = dfc["month"].to_list()
    ys = dfc["revenue"].to_list()
    rolls = dfc["roll3"].to_list()

    y1 = dfc.head(12)
    x0 = y1["month"][0]
    x1 = y1["month"][-1]
    if isinstance(x0, dt.datetime):
        x0p, x1p = x0, x1
    else:
        x0p = dt.datetime.fromisoformat(str(x0)[:19])
        x1p = dt.datetime.fromisoformat(str(x1)[:19])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines+markers",
            name="Actual revenue",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=rolls,
            mode="lines+markers",
            name="3-month rolling avg (actual)",
            line=dict(color="#636EFA", dash="dot"),
        )
    )
    if scope_picker.value == "United Kingdom":
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=dfc["counterfactual"].to_list(),
                mode="lines+markers",
                name="Counterfactual (growth + seasonality)",
                line=dict(dash="dash", color="#EF553B"),
            )
        )
    fig.add_vrect(
        x0=x0p,
        x1=x1p,
        fillcolor="LightGreen",
        opacity=0.12,
        layer="below",
        line_width=0,
        annotation_text="Year 1 (fit window)",
        annotation_position="top left",
    )
    fig.add_shape(
        type="line",
        x0=vat_day,
        x1=vat_day,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="red", width=2, dash="dot"),
    )
    fig.add_annotation(
        x=vat_day,
        y=1.0,
        xref="x",
        yref="paper",
        text="VAT 17.5% → 20%",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
    )
    fig.update_layout(
        title="Monthly revenue: actual vs model benchmark (year one included)",
        xaxis_title="Month",
        yaxis_title="Revenue (£)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


if __name__ == "__main__":
    app.run()
