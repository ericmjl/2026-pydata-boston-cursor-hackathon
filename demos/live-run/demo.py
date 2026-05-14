# /// script
# dependencies = [
#     "anywidget==0.11.0",
#     "marimo",
#     "matplotlib==3.10.9",
#     "plotly==6.7.0",
#     "polars==1.40.1",
#     "pyarrow==24.0.0",
#     "traitlets==5.15.0",
# ]
# requires-python = ">=3.13"
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import polars as pl
    import plotly.express as px
    import anywidget
    import traitlets
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent

    return Path, anywidget, mo, pl, px, repo_root, traitlets


@app.cell(hide_code=True)
def load_data(Path, pl, repo_root):
    data_dir = repo_root / "data/ired-novartis"

    activity_df = (
        pl.read_csv(data_dir / "cs1c02786_si_002.csv")
        .drop("")
        .rename(
            {
                "mean": "mean_conversion",
                "alpha": "conversion_alpha",
                "beta": "conversion_beta",
                "ratio": "conversion_ratio",
                "count": "replicate_count",
            }
        )
    )

    selectivity_df = (
        pl.read_csv(data_dir / "cs1c02786_si_003.csv")
        .drop("")
        .rename(
            {
                "ratio": "conversion_ratio",
                "experiment": "experiment_type",
            }
        )
    )

    activity_df
    return activity_df, selectivity_df


@app.cell(hide_code=True)
def show_selectivity(selectivity_df):
    selectivity_df
    return


@app.cell(hide_code=True)
def scatter_plot(activity_df, pl, px, selectivity_df):
    single_mutants = selectivity_df.filter(
        ~pl.col("mutation").str.contains(";")
    ).join(
        activity_df.select("mutation", "mean_conversion").unique(),
        on="mutation",
        how="inner",
    )

    fig = px.scatter(
        single_mutants,
        x="mean_conversion",
        y="r_enantiomeric_excess",
        hover_data=["mutation", "experiment_type"],
        labels={
            "mean_conversion": "Mean Conversion",
            "r_enantiomeric_excess": "R Enantiomeric Excess",
        },
        title="IRED Single Point Mutants: Conversion vs. Chiral Selectivity",
    )
    fig.update_layout(template="plotly_white")
    fig
    return (single_mutants,)


@app.cell(hide_code=True)
def correlation_observation(mo, pl, single_mutants):
    correlation = single_mutants.select(
        pl.corr("mean_conversion", "r_enantiomeric_excess")
    ).item()

    mo.md(
        f"""
        ## Observation: Weak Correlation Between Conversion and Selectivity

        The Pearson correlation between mean conversion and R enantiomeric excess
        for single-point IRED mutants is **r = {correlation:.3f}**,
        indicating a very weak negative relationship.
        Conversion and chiral selectivity appear to be largely independent properties
        in this enzyme — mutations that improve activity do not reliably
        improve (or degrade) enantioselectivity, and vice versa.
        This is consistent with the common challenge in protein engineering
        of needing to optimize multiple objectives simultaneously.
        """
    )
    return


@app.cell(hide_code=True)
def positional_data(activity_df, pl, selectivity_df):
    def _extract_position(col: str) -> pl.Expr:
        return (
            pl.col(col)
            .str.extract(r"[A-Z](\d+)[A-Z]", 1)
            .cast(pl.Int64)
            .alias("position")
        )


    activity_by_pos = (
        activity_df.filter(~pl.col("mutation").str.contains(";"))
        .with_columns(_extract_position("mutation"))
        .group_by("position")
        .agg(
            pl.col("mean_conversion").mean().alias("mean"),
            pl.col("mean_conversion").max().alias("max"),
        )
        .sort("position")
    )

    selectivity_by_pos = (
        selectivity_df.filter(~pl.col("mutation").str.contains(";"))
        .with_columns(_extract_position("mutation"))
        .group_by("position")
        .agg(
            pl.col("r_enantiomeric_excess").mean().alias("mean"),
            pl.col("r_enantiomeric_excess").max().alias("max"),
        )
        .sort("position")
    )
    return activity_by_pos, selectivity_by_pos


@app.cell(hide_code=True)
def dropdowns(mo):
    stat_dropdown = mo.ui.dropdown(
        options={"Mean": "mean", "Max": "max"},
        value="Mean",
        label="Statistic",
    )
    property_dropdown = mo.ui.dropdown(
        options={
            "Activity (Conversion)": "activity",
            "Chiral Selectivity (ee)": "selectivity",
        },
        value="Activity (Conversion)",
        label="Property",
    )
    mo.hstack([stat_dropdown, property_dropdown])
    return property_dropdown, stat_dropdown


@app.cell(hide_code=True)
def positional_line_chart(
    activity_by_pos,
    property_dropdown,
    px,
    selectivity_by_pos,
    stat_dropdown,
):
    stat = stat_dropdown.value
    prop = property_dropdown.value
    source = activity_by_pos if prop == "activity" else selectivity_by_pos
    y_label = "Mean Conversion" if prop == "activity" else "R Enantiomeric Excess"
    title_prop = (
        "Activity (Conversion)"
        if prop == "activity"
        else "Chiral Selectivity (ee)"
    )

    line_fig = px.line(
        source,
        x="position",
        y=stat,
        labels={"position": "Residue Position", stat: y_label},
        title=f"{stat.capitalize()} Mutational Effect on {title_prop} by Position",
        markers=True,
    )
    line_fig.update_layout(template="plotly_white")
    line_fig
    return


@app.cell(hide_code=True)
def top5_summary(activity_by_pos, mo, selectivity_by_pos):
    def _top5(df, col):
        return df.sort(col, descending=True).head(5).select("position", col)


    _act_mean = _top5(activity_by_pos, "mean")
    _act_max = _top5(activity_by_pos, "max")
    _sel_mean = _top5(selectivity_by_pos, "mean")
    _sel_max = _top5(selectivity_by_pos, "max")


    def _fmt_rows(df, col):
        return "\n".join(
            f"| {row['position']} | {row[col]:.4f} |"
            for row in df.iter_rows(named=True)
        )


    mo.md(
        f"""## Top 5 Positions by Mutational Effect

    ### Mean Activity (Conversion)

    | Position | Mean Conversion |
    |----------|-----------------|
    {_fmt_rows(_act_mean, "mean")}

    ### Max Activity (Conversion)

    | Position | Max Conversion |
    |----------|----------------|
    {_fmt_rows(_act_max, "max")}

    ### Mean Chiral Selectivity (R Enantiomeric Excess)

    | Position | Mean ee |
    |----------|---------|
    {_fmt_rows(_sel_mean, "mean")}

    ### Max Chiral Selectivity (R Enantiomeric Excess)

    | Position | Max ee |
    |----------|--------|
    {_fmt_rows(_sel_max, "max")}

    **Key takeaways:**

    - Position **220** stands out across multiple rankings — it is the top position
      for both mean and max chiral selectivity, and ranks 2nd for max activity.
    - Positions **243**, **156**, and **159** dominate mean activity but do not
      appear in the selectivity rankings, reinforcing the weak correlation between
      conversion and enantioselectivity.
    - Position **296** achieves the highest single-mutant conversion (max = 0.712)
      despite a modest mean, suggesting one particularly potent substitution at
      that site.
    """
    )
    return


@app.cell(hide_code=True)
def mol_viewer_widget(anywidget, traitlets):
    class MolViewer(anywidget.AnyWidget):
        _esm = """
        function load3Dmol() {
          return new Promise((resolve, reject) => {
            if (window.$3Dmol) { resolve(window.$3Dmol); return; }
            const script = document.createElement("script");
            script.src = "https://cdn.jsdelivr.net/npm/3dmol@2.4.2/build/3Dmol-min.js";
            script.onload = () => resolve(window.$3Dmol);
            script.onerror = reject;
            document.head.appendChild(script);
          });
        }

        function interpolateColor(t) {
          t = Math.max(0, Math.min(1, t));
          let r, g, b;
          if (t < 0.5) {
            const s = t * 2;
            r = Math.round(60 + s * 195);
            g = Math.round(80 + s * 175);
            b = Math.round(220 - s * 20);
          } else {
            const s = (t - 0.5) * 2;
            r = 255;
            g = Math.round(255 - s * 195);
            b = Math.round(200 - s * 170);
          }
          return "rgb(" + r + "," + g + "," + b + ")";
        }

        async function render({ model, el }) {
          const $3Dmol = await load3Dmol();

          const wrapper = document.createElement("div");
          wrapper.style.position = "relative";
          wrapper.style.width = "100%";
          wrapper.style.height = "600px";
          el.appendChild(wrapper);

          const container = document.createElement("div");
          container.style.width = "100%";
          container.style.height = "100%";
          wrapper.appendChild(container);

          const tooltip = document.createElement("div");
          tooltip.style.cssText =
            "display:none; position:absolute; background:rgba(0,0,0,0.85); color:#fff;" +
            "padding:8px 12px; border-radius:6px; font:13px/1.4 system-ui, sans-serif;" +
            "pointer-events:none; z-index:10; max-width:220px; box-shadow:0 2px 8px rgba(0,0,0,0.3);";
          wrapper.appendChild(tooltip);

          const legend = document.createElement("div");
          legend.style.cssText =
            "position:absolute; bottom:12px; right:12px; background:rgba(255,255,255,0.92);" +
            "padding:8px 12px; border-radius:6px; font:11px/1.4 system-ui, sans-serif;" +
            "box-shadow:0 1px 4px rgba(0,0,0,0.15); z-index:5; display:none;";
          wrapper.appendChild(legend);

          const viewer = $3Dmol.createViewer(container, { backgroundColor: "white" });

          let atomClicked = false;

          function applyStyles() {
            const pdbData = model.get("pdb_data");
            if (!pdbData) return;

            const rawValues = model.get("residue_values");
            const valueLabel = model.get("value_label");
            const values = rawValues ? JSON.parse(rawValues) : {};
            const positions = Object.keys(values).map(Number);

            viewer.removeAllModels();
            viewer.addModel(pdbData, "pdb");

            viewer.setStyle({ resn: "HOH" }, {});

            if (positions.length > 0) {
              const vals = Object.values(values);
              const vmin = Math.min(...vals);
              const vmax = Math.max(...vals);
              const range = vmax - vmin || 1;

              viewer.setStyle(
                { chain: ["A", "B"], hetflag: false },
                { cartoon: { color: "0xcccccc" } }
              );

              for (const pos of positions) {
                const t = (values[pos] - vmin) / range;
                const color = interpolateColor(t);
                viewer.setStyle(
                  { resi: pos, hetflag: false },
                  { cartoon: { color: color } }
                );
              }

              legend.style.display = "block";
              legend.innerHTML =
                "<div style='margin-bottom:4px;font-weight:600;'>" + valueLabel + "</div>" +
                "<div style='display:flex;align-items:center;gap:6px;'>" +
                "<span>" + vmin.toFixed(3) + "</span>" +
                "<div style='width:100px;height:12px;border-radius:3px;" +
                "background:linear-gradient(to right," +
                interpolateColor(0) + "," + interpolateColor(0.5) + "," + interpolateColor(1) +
                ");'></div>" +
                "<span>" + vmax.toFixed(3) + "</span></div>";
            } else {
              viewer.setStyle(
                { chain: ["A", "B"], hetflag: false },
                { cartoon: { color: "spectrum" } }
              );
              legend.style.display = "none";
            }

            viewer.setStyle(
              { hetflag: true, not: { resn: "HOH" } },
              { stick: { radius: 0.15 }, sphere: { scale: 0.25 } }
            );

            viewer.setClickable({}, true, function(atom, _viewer, event) {
              if (!atom) return;
              atomClicked = true;
              const resi = atom.resi;
              const chain = atom.chain;
              const resn = atom.resn;
              let html = "<strong>" + resn + " " + resi + "</strong> (chain " + chain + ")";
              if (values[resi] !== undefined) {
                html += "<br/>" + valueLabel + ": <strong>" + values[resi].toFixed(4) + "</strong>";
              } else {
                html += "<br/><em>No data</em>";
              }
              tooltip.innerHTML = html;
              tooltip.style.display = "block";

              const rect = wrapper.getBoundingClientRect();
              const x = event.clientX - rect.left;
              const y = event.clientY - rect.top;
              tooltip.style.left = (x + 14) + "px";
              tooltip.style.top = (y - 10) + "px";
            });

            viewer.zoomTo();
            viewer.render();
          }

          wrapper.addEventListener("click", function() {
            if (atomClicked) {
              atomClicked = false;
              return;
            }
            tooltip.style.display = "none";
          });

          model.on("change:pdb_data", applyStyles);
          model.on("change:residue_values", applyStyles);
          model.on("change:value_label", applyStyles);
          applyStyles();
        }

        export default { render };
        """
        pdb_data = traitlets.Unicode("").tag(sync=True)
        residue_values = traitlets.Unicode("").tag(sync=True)
        value_label = traitlets.Unicode("").tag(sync=True)

    return (MolViewer,)


@app.cell(hide_code=True)
def structure_viewer(
    MolViewer,
    Path,
    activity_by_pos,
    property_dropdown,
    repo_root,
    selectivity_by_pos,
    stat_dropdown,
):
    import json

    _stat = stat_dropdown.value
    _prop = property_dropdown.value
    _source = activity_by_pos if _prop == "activity" else selectivity_by_pos
    _y_label = (
        "Mean Conversion" if _prop == "activity" else "R Enantiomeric Excess"
    )
    _label = f"{_stat.capitalize()} {_y_label}"

    residue_map = {
        row["position"]: row[_stat]
        for row in _source.iter_rows(named=True)
        if row[_stat] is not None
    }

    pdb_text = (repo_root / "data/ired-novartis/7OG3.pdb").read_text()
    viewer = MolViewer(
        pdb_data=pdb_text,
        residue_values=json.dumps(residue_map),
        value_label=_label,
    )
    viewer
    return


@app.cell(hide_code=True)
def distal_observation(mo):
    mo.md("""
    ## Observation: Beneficial Mutations Are Distal to the Active Site

        Inspecting the structure colored by mutational effect reveals a striking
        pattern: the positions with the largest improvements in both conversion
        and enantioselectivity are **not** located in or near the substrate
        binding pocket. Instead, they are distributed across the protein scaffold,
        often in surface-exposed loops and secondary-structure elements far from
        the catalytic center.

        This is consistent with the growing body of evidence in directed evolution
        that **distal mutations** can reshape enzyme function through subtle
        conformational and dynamic effects — altering loop flexibility,
        inter-domain packing, or long-range electrostatic networks — rather than
        through direct contacts with the substrate. It also underscores the
        challenge of rational design in this regime: the most impactful mutations
        are precisely the ones hardest to predict from active-site inspection
        alone.
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
