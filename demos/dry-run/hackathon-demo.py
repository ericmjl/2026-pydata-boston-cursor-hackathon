# /// script
# dependencies = [
#     "marimo",
#     "plotly==6.7.0",
#     "polars==1.40.1",
#     "anywidget==0.11.0",
#     "traitlets==5.15.0",
# ]
# requires-python = ">=3.13"
# ///

import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def notebook_imports():
    import json
    from pathlib import Path

    import anywidget
    import marimo as mo
    import polars as pl
    import plotly.graph_objects as go
    import traitlets

    repo_root = Path(__file__).resolve().parent.parent.parent

    return Path, anywidget, go, json, mo, pl, repo_root, traitlets


@app.cell(hide_code=True)
def intro_markdown(mo):
    mo.md(r"""
    # Protein Engineering Demo

    This notebook is a complete assay-to-structure workflow for enzyme engineering.
    We start from tabular mutational assay data, identify signal in sequence space,
    and then project those effects onto a 3D protein structure for interactive exploration.
    """)
    return


@app.cell(hide_code=True)
def data_loading_markdown(mo):
    mo.md(r"""
    ## Load assay tables

    We use two assay views of the same engineering problem:
    - `cs1c02786_si_002.csv`: conversion activity (`mean`)
    - `cs1c02786_si_003.csv`: chiral selectivity (`r_enantiomeric_excess`)

    Keeping these tables separate helps us reason about multi-objective tradeoffs.
    """)
    return


@app.cell(hide_code=True)
def load_conversion_table(Path, pl, repo_root):
    conversion_table_path = repo_root / "data/ired-novartis/cs1c02786_si_002.csv"
    df_conversion = pl.read_csv(conversion_table_path)
    df_conversion
    return (df_conversion,)


@app.cell(hide_code=True)
def chirality_loading_markdown(mo):
    mo.md(r"""
    ## Load chirality table

    This table tracks enantiomeric excess values for selected mutants.
    """)
    return


@app.cell(hide_code=True)
def load_chirality_table(Path, pl, repo_root):
    chirality_table_path = repo_root / "data/ired-novartis/cs1c02786_si_003.csv"
    df_chirality = pl.read_csv(chirality_table_path)
    df_chirality
    return (df_chirality,)


@app.cell(hide_code=True)
def correlation_analysis_markdown(mo):
    mo.md(r"""
    ## Correlation between conversion and chirality

    First, we quantify whether improved conversion tends to co-occur with improved selectivity.
    We restrict to mutants present in both tables, then compare their joint behavior.
    """)
    return


@app.cell(hide_code=True)
def prepare_intersection_dataset(df_chirality, df_conversion):
    intersection_cols = ["mutation", "r_enantiomeric_excess", "mean"]

    chirality_selected = df_chirality.select(["mutation", "r_enantiomeric_excess"])
    conversion_selected = df_conversion.select(["mutation", "mean"])

    df_intersection = (
        chirality_selected.join(conversion_selected, on="mutation", how="inner")
        .drop_nulls(intersection_cols)
        .unique(subset=["mutation"])
        .sort("mutation")
        .with_row_index(name="mutation_index")
    )

    df_intersection
    return (df_intersection,)


@app.cell(hide_code=True)
def plotly_intersection_scatter(df_intersection, go):
    scatter_plot = go.Figure(
        data=go.Scatter(
            x=df_intersection["mean"].to_list(),
            y=df_intersection["r_enantiomeric_excess"].to_list(),
            mode="markers",
            text=df_intersection["mutation"].to_list(),
            marker=dict(size=8, opacity=0.75),
            hovertemplate=(
                "mutation=%{text}<br>"
                "mean=%{x:.4f}<br>"
                "r_enantiomeric_excess=%{y:.4f}<extra></extra>"
            ),
        )
    )
    scatter_plot.update_layout(
        title="Intersection mutants: conversion vs chirality",
        xaxis_title="mean (conversion)",
        yaxis_title="r_enantiomeric_excess (chirality)",
    )
    scatter_plot
    return


@app.cell(hide_code=True)
def scatter_interpretation_note(mo):
    mo.md(r"""
    **Interpretation:** I do not see a clear correlation between `r_enantiomeric_excess` and `mean` in the intersection scatter plot.
    """)
    return


@app.cell(hide_code=True)
def plotly_value_ecdfs(df_intersection, go):
    def ecdf(values: list[float]) -> tuple[list[float], list[float]]:
        sorted_values = sorted(values)
        n = len(sorted_values)
        y = [(i + 1) / n for i in range(n)]
        return sorted_values, y


    mean_values = [float(v) for v in df_intersection["mean"].to_list()]
    chirality_values = [
        float(v) for v in df_intersection["r_enantiomeric_excess"].to_list()
    ]

    x_mean, y_mean = ecdf(mean_values)
    x_chiral, y_chiral = ecdf(chirality_values)

    ecdf_plot = go.Figure()
    ecdf_plot.add_trace(
        go.Scatter(
            x=x_mean,
            y=y_mean,
            mode="lines",
            name="mean (conversion)",
            line=dict(shape="hv"),
        )
    )
    ecdf_plot.add_trace(
        go.Scatter(
            x=x_chiral,
            y=y_chiral,
            mode="lines",
            name="r_enantiomeric_excess (chirality)",
            line=dict(shape="hv"),
        )
    )
    ecdf_plot.update_layout(
        title="ECDFs for conversion and chirality values",
        xaxis_title="Value",
        yaxis_title="ECDF",
    )
    ecdf_plot
    return


@app.cell(hide_code=True)
def single_point_heatmap_markdown(mo):
    mo.md(r"""
    ## Single-point mutant landscape

    To make residue-level interpretation easier, we focus on canonical single substitutions
    (mutations matching `WT + position + MUT`, no `;`).

    This heatmap shows:
    - x-axis: sequence position
    - y-axis: mutated amino-acid letter
    - color: conversion `mean`

    Hover also reports chirality when available.
    """)
    return


@app.cell(hide_code=True)
def plot_single_point_heatmap(df_chirality, df_conversion, go, pl):
    df_single_point = (
        df_conversion.filter(pl.col("mutation").is_not_null())
        .filter(~pl.col("mutation").str.contains(";"))
        .filter(pl.col("mutation").str.contains(r"^[A-Z]\d+[A-Z]$"))
        .with_columns(
            [
                pl.col("mutation")
                .str.extract(r"^[A-Z](\d+)[A-Z]$", 1)
                .cast(pl.Int64)
                .alias("position"),
                pl.col("mutation")
                .str.extract(r"^[A-Z]\d+([A-Z])$", 1)
                .alias("mut_aa"),
            ]
        )
    )

    df_single_point_joined = df_single_point.join(
        df_chirality.select(["mutation", "r_enantiomeric_excess"]),
        on="mutation",
        how="left",
    )

    df_single_point_heatmap = df_single_point_joined.group_by(
        ["position", "mut_aa"]
    ).agg(
        [
            pl.col("mean").mean().alias("mean"),
            pl.col("mutation").first().alias("example_mutation"),
            pl.col("r_enantiomeric_excess").mean().alias("r_enantiomeric_excess"),
            pl.len().alias("n_records"),
        ]
    )

    x_positions = sorted(
        df_single_point_heatmap.get_column("position").unique().to_list()
    )
    y_letters = sorted(
        df_single_point_heatmap.get_column("mut_aa").unique().to_list()
    )

    x_index = {position: idx for idx, position in enumerate(x_positions)}
    y_index = {letter: idx for idx, letter in enumerate(y_letters)}

    z_matrix = [[None for _ in x_positions] for _ in y_letters]
    text_matrix = [["" for _ in x_positions] for _ in y_letters]

    for row in df_single_point_heatmap.iter_rows(named=True):
        i = y_index[row["mut_aa"]]
        j = x_index[row["position"]]
        z_matrix[i][j] = row["mean"]
        chirality_value = row["r_enantiomeric_excess"]
        chirality_text = (
            "NA" if chirality_value is None else f"{chirality_value:.4f}"
        )
        text_matrix[i][j] = (
            f"mutation={row['example_mutation']}<br>"
            f"r_enantiomeric_excess={chirality_text}<br>"
            f"n_records={row['n_records']}"
        )

    single_point_heatmap = go.Figure(
        data=go.Heatmap(
            x=x_positions,
            y=y_letters,
            z=z_matrix,
            text=text_matrix,
            colorscale="Viridis",
            colorbar=dict(title="mean"),
            hovertemplate=(
                "position=%{x}<br>"
                "mutation_letter=%{y}<br>"
                "mean=%{z:.4f}<br>"
                "%{text}<extra></extra>"
            ),
        )
    )

    single_point_heatmap.update_layout(
        title="Single-point mutants: conversion heatmap",
        xaxis_title="Position",
        yaxis_title="Mutation letter",
    )

    single_point_heatmap
    return (df_single_point,)


@app.cell(hide_code=True)
def single_point_heatmap_interpretation_note(mo):
    mo.md(r"""
    **Interpretation:** I am seeing hotspot positions with potentially strong mutational effects, suggesting there are beneficial mutations to target at those sites.
    """)
    return


@app.cell(hide_code=True)
def average_effect_by_position_markdown(mo):
    mo.md(r"""
    ## Average mutational effect by position

    Here we collapse amino-acid identity and ask a simpler question:
    *on average, how sensitive is each position to mutation?*

    This gives a position-level prioritization signal before moving to structure.
    """)
    return


@app.cell(hide_code=True)
def plot_average_effect_by_position(df_single_point, go, pl):
    df_position_effect = (
        df_single_point.group_by("position")
        .agg(pl.col("mean").mean().alias("average_mutational_effect"))
        .sort("position")
    )

    position_effect_plot = go.Figure(
        data=go.Scatter(
            x=df_position_effect["position"].to_list(),
            y=df_position_effect["average_mutational_effect"].to_list(),
            mode="lines+markers",
            marker=dict(size=5),
            line=dict(width=2),
            hovertemplate=(
                "position=%{x}<br>"
                "average_mutational_effect=%{y:.4f}<extra></extra>"
            ),
        )
    )

    position_effect_plot.update_layout(
        title="Average mutational effect by position",
        xaxis_title="Position",
        yaxis_title="Average mutational effect",
    )

    position_effect_plot
    return


@app.cell(hide_code=True)
def build_position_effect_tables(df_chirality, df_single_point, pl):
    df_single_point_chirality = (
        df_chirality.filter(pl.col("mutation").is_not_null())
        .filter(~pl.col("mutation").str.contains(";"))
        .filter(pl.col("mutation").str.contains(r"^[A-Z]\d+[A-Z]$"))
        .with_columns(
            pl.col("mutation")
            .str.extract(r"^[A-Z](\d+)[A-Z]$", 1)
            .cast(pl.Int64)
            .alias("position")
        )
    )

    # Backward-compatible names: these remain the mean summaries.
    df_position_effect_conversion = (
        df_single_point.group_by("position")
        .agg(pl.col("mean").mean().alias("avg_conversion"))
        .sort("position")
    )

    df_position_effect_chirality = (
        df_single_point_chirality.group_by("position")
        .agg(pl.col("r_enantiomeric_excess").mean().alias("avg_chirality"))
        .sort("position")
    )

    # Additional max summaries for structure coloring control.
    df_position_effect_conversion_max = (
        df_single_point.group_by("position")
        .agg(pl.col("mean").max().alias("max_conversion"))
        .sort("position")
    )

    df_position_effect_chirality_max = (
        df_single_point_chirality.group_by("position")
        .agg(pl.col("r_enantiomeric_excess").max().alias("max_chirality"))
        .sort("position")
    )

    all_positions = (
        pl.concat(
            [
                df_position_effect_conversion.select("position"),
                df_position_effect_conversion_max.select("position"),
                df_position_effect_chirality.select("position"),
                df_position_effect_chirality_max.select("position"),
            ]
        )
        .unique()
        .sort("position")
    )

    df_position_effects = (
        all_positions.join(
            df_position_effect_conversion, on="position", how="left"
        )
        .join(df_position_effect_conversion_max, on="position", how="left")
        .join(df_position_effect_chirality, on="position", how="left")
        .join(df_position_effect_chirality_max, on="position", how="left")
    )

    df_position_effects
    return (
        df_position_effect_chirality,
        df_position_effect_chirality_max,
        df_position_effect_conversion,
        df_position_effect_conversion_max,
    )


@app.cell(hide_code=True)
def structure_mapping_markdown(mo):
    mo.md(r"""
    ## Sequence-to-structure mapping

    Before coloring the structure, we validate that assay residue numbering aligns with PDB residue numbering.
    We infer the best residue offset by matching wild-type letters, then build residue-level effect maps
    indexed by PDB residue number.
    """)
    return


@app.cell(hide_code=True)
def pdb_sequence_validation_and_effect_maps(
    Path,
    df_position_effect_chirality,
    df_position_effect_chirality_max,
    df_position_effect_conversion,
    df_position_effect_conversion_max,
    df_single_point,
    json,
    mo,
    pl,
    repo_root,
):
    AA3_TO_AA1 = {
        "ALA": "A",
        "ARG": "R",
        "ASN": "N",
        "ASP": "D",
        "CYS": "C",
        "GLN": "Q",
        "GLU": "E",
        "GLY": "G",
        "HIS": "H",
        "ILE": "I",
        "LEU": "L",
        "LYS": "K",
        "MET": "M",
        "MSE": "M",
        "PHE": "F",
        "PRO": "P",
        "SER": "S",
        "THR": "T",
        "TRP": "W",
        "TYR": "Y",
        "VAL": "V",
    }


    def parse_pdb_chain_residues(pdb_text: str, chain_id: str) -> dict[int, str]:
        residues: dict[int, str] = {}
        for line in pdb_text.splitlines():
            if len(line) < 27:
                continue
            record = line[0:6].strip()
            if record not in {"ATOM", "HETATM"}:
                continue
            if line[21:22] != chain_id:
                continue
            resname = line[17:20].strip()
            try:
                resseq = int(line[22:26])
            except ValueError:
                continue
            aa = AA3_TO_AA1.get(resname)
            if aa is None:
                continue
            residues[resseq] = aa
        return residues


    def build_effect_map(table, value_col: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for row in table.iter_rows(named=True):
            val = row[value_col]
            if val is None:
                continue
            pdb_res = int(row["position"]) + pdb_residue_offset
            out[str(pdb_res)] = float(val)
        return out


    pdb_path = repo_root / "data/ired-novartis/7OG3.pdb"
    pdb_text = pdb_path.read_text()
    pdb_chain = "A"
    pdb_residues = parse_pdb_chain_residues(pdb_text, pdb_chain)

    wt_by_position = (
        df_single_point.group_by("position")
        .agg(pl.col("mutation").str.slice(0, 1).first().alias("wt_aa"))
        .sort("position")
    )

    positions = wt_by_position.get_column("position").to_list()
    wt_aas = wt_by_position.get_column("wt_aa").to_list()

    best_offset = 0
    best_score = -1
    for offset in range(-20, 21):
        score = 0
        for pos, wt in zip(positions, wt_aas):
            pdb_aa = pdb_residues.get(pos + offset)
            if pdb_aa == wt:
                score += 1
        if score > best_score:
            best_score = score
            best_offset = offset

    pdb_residue_offset = best_offset

    mapping_rows = []
    for pos, wt in zip(positions, wt_aas):
        pdb_resi = pos + pdb_residue_offset
        pdb_aa = pdb_residues.get(pdb_resi)
        mapping_rows.append(
            {
                "assay_position": pos,
                "pdb_residue": pdb_resi,
                "wt_aa": wt,
                "pdb_aa": pdb_aa,
                "match": pdb_aa == wt if pdb_aa is not None else False,
                "has_structure": pdb_aa is not None,
            }
        )

    df_pdb_mapping_validation = pl.DataFrame(mapping_rows)

    mapping_matched = df_pdb_mapping_validation.filter(pl.col("match")).height
    mapping_mismatch = df_pdb_mapping_validation.filter(
        pl.col("has_structure") & (~pl.col("match"))
    ).height
    mapping_unmapped = df_pdb_mapping_validation.filter(
        ~pl.col("has_structure")
    ).height

    # Mean maps (legacy + new names)
    effects_conversion_mean = build_effect_map(
        df_position_effect_conversion, "avg_conversion"
    )
    effects_chirality_mean = build_effect_map(
        df_position_effect_chirality, "avg_chirality"
    )

    # Max maps
    effects_conversion_max = build_effect_map(
        df_position_effect_conversion_max, "max_conversion"
    )
    effects_chirality_max = build_effect_map(
        df_position_effect_chirality_max, "max_chirality"
    )

    # Keep original names for compatibility
    effects_conversion_json = json.dumps(effects_conversion_mean)
    effects_chirality_json = json.dumps(effects_chirality_mean)

    # Explicit mean/max names for new controls
    effects_conversion_mean_json = json.dumps(effects_conversion_mean)
    effects_conversion_max_json = json.dumps(effects_conversion_max)
    effects_chirality_mean_json = json.dumps(effects_chirality_mean)
    effects_chirality_max_json = json.dumps(effects_chirality_max)

    mo.vstack(
        [
            mo.md(
                f"PDB mapping chain **{pdb_chain}**, residue offset **{pdb_residue_offset}** "
                f"(best agreement with assay wild-type letters): matched **{mapping_matched}**, "
                f"mismatch **{mapping_mismatch}**, unmapped **{mapping_unmapped}**."
            ),
            df_pdb_mapping_validation.filter(
                pl.col("has_structure") & (~pl.col("match"))
            ).head(12),
        ]
    )
    return (
        effects_chirality_json,
        effects_chirality_max_json,
        effects_chirality_mean_json,
        effects_conversion_json,
        effects_conversion_max_json,
        effects_conversion_mean_json,
        pdb_chain,
        pdb_residue_offset,
        pdb_text,
    )


@app.cell(hide_code=True)
def widget_engineering_markdown(mo):
    mo.md(r"""
    ## Interactive viewer component

    The viewer is an inline anywidget backed by 3Dmol.js.
    It consumes precomputed residue effect maps and renders synchronized ribbon/surface coloring,
    while keeping ligand/cofactor visible as ball-and-stick.
    """)
    return


@app.cell(hide_code=True)
def define_protein_structure_viewer_widget(anywidget, traitlets):
    class ProteinStructureViewer(anywidget.AnyWidget):
        pdb_text = traitlets.Unicode("").tag(sync=True)
        pdb_chain = traitlets.Unicode("A").tag(sync=True)
        effects_conversion_mean = traitlets.Unicode("{}").tag(sync=True)
        effects_conversion_max = traitlets.Unicode("{}").tag(sync=True)
        effects_chirality_mean = traitlets.Unicode("{}").tag(sync=True)
        effects_chirality_max = traitlets.Unicode("{}").tag(sync=True)
        color_mode = traitlets.Unicode("conversion").tag(sync=True)
        aggregation_mode = traitlets.Unicode("mean").tag(sync=True)

        _esm = r"""
    export default {
      async render({ model, el }) {
        el.replaceChildren();
        const host = document.createElement("div");
        host.style.width = "100%";
        host.style.height = "520px";
        el.appendChild(host);

        await new Promise((resolve, reject) => {
          if (globalThis.$3Dmol) {
            resolve();
            return;
          }
          const script = document.createElement("script");
          script.src = "https://cdn.jsdelivr.net/npm/3dmol@2.1.0/build/3Dmol-min.js";
          script.onload = () => resolve();
          script.onerror = () => reject(new Error("Failed to load 3Dmol.js"));
          document.head.appendChild(script);
        });

        const viewer = globalThis.$3Dmol.createViewer(host, { backgroundColor: "white" });
        const $3D = globalThis.$3Dmol;

        const proteinSel = { not: { resn: ["HOH", "WAT", "H2O", "DOD"] } };

        const clamp01 = (x) => Math.max(0, Math.min(1, x));
        const lerp = (a, b, t) => a + (b - a) * t;

        const interpolateRgbStops = (stops, tRaw) => {
          const t = clamp01(tRaw);
          let left = stops[0];
          let right = stops[stops.length - 1];
          for (let i = 1; i < stops.length; i++) {
            if (t <= stops[i][0]) {
              left = stops[i - 1];
              right = stops[i];
              break;
            }
          }
          const denom = right[0] - left[0] || 1;
          const localT = clamp01((t - left[0]) / denom);
          const r = Math.round(lerp(left[1][0], right[1][0], localT));
          const g = Math.round(lerp(left[1][1], right[1][1], localT));
          const b = Math.round(lerp(left[1][2], right[1][2], localT));
          return `rgb(${r}, ${g}, ${b})`;
        };

        const conversionStops = [
          [0.0, [49, 54, 149]],
          [0.35, [69, 117, 180]],
          [0.5, [247, 247, 247]],
          [0.7, [253, 174, 97]],
          [1.0, [165, 0, 38]],
        ];

        const chiralityStops = [
          [0.0, [94, 60, 153]],
          [0.35, [178, 171, 210]],
          [0.5, [247, 247, 247]],
          [0.7, [253, 184, 99]],
          [1.0, [230, 97, 1]],
        ];

        const tooltip = document.createElement("div");
        tooltip.style.position = "absolute";
        tooltip.style.pointerEvents = "none";
        tooltip.style.background = "rgba(20, 20, 20, 0.9)";
        tooltip.style.color = "#ffffff";
        tooltip.style.padding = "6px 8px";
        tooltip.style.borderRadius = "6px";
        tooltip.style.fontSize = "12px";
        tooltip.style.fontFamily = "ui-sans-serif, system-ui, -apple-system";
        tooltip.style.lineHeight = "1.35";
        tooltip.style.zIndex = "1000";
        tooltip.style.display = "none";
        el.style.position = "relative";
        el.appendChild(tooltip);

        const hideTooltip = () => {
          tooltip.style.display = "none";
        };

        const AA3_TO_AA1 = {
          ALA: "A", ARG: "R", ASN: "N", ASP: "D", CYS: "C",
          GLN: "Q", GLU: "E", GLY: "G", HIS: "H", ILE: "I",
          LEU: "L", LYS: "K", MET: "M", MSE: "M", PHE: "F",
          PRO: "P", SER: "S", THR: "T", TRP: "W", TYR: "Y", VAL: "V",
        };

        const effectMapForCurrentSelection = () => {
          const raw = selectedEffectMap();
          try {
            return JSON.parse(raw || "{}");
          } catch (_err) {
            return {};
          }
        };

        let atomClickedInCycle = false;

        const showTooltip = (atom, event) => {
          if (!atom) return;
          const mode = model.get("color_mode");
          const agg = model.get("aggregation_mode");
          const effects = effectMapForCurrentSelection();
          const key = String(atom.resi);
          const value = Number(effects[key]);
          const valueText = Number.isFinite(value) ? value.toFixed(4) : "NA";
          const resn = String(atom.resn || "").toUpperCase();
          const wtAA = AA3_TO_AA1[resn] || "?";

          tooltip.innerHTML =
            `<div><strong>Chain</strong>: ${atom.chain ?? "?"}</div>` +
            `<div><strong>Residue</strong>: ${atom.resi}</div>` +
            `<div><strong>WT AA</strong>: ${wtAA} (${resn || "NA"})</div>` +
            `<div><strong>Mode</strong>: ${mode}</div>` +
            `<div><strong>Summary</strong>: ${agg}</div>` +
            `<div><strong>Value</strong>: ${valueText}</div>`;

          const rect = host.getBoundingClientRect();
          const clientX = event?.clientX ?? event?.pageX ?? (rect.left + rect.width / 2);
          const clientY = event?.clientY ?? event?.pageY ?? (rect.top + rect.height / 2);
          const x = clientX - rect.left + 10;
          const y = clientY - rect.top + 10;

          tooltip.style.left = `${Math.max(8, Math.min(rect.width - 180, x))}px`;
          tooltip.style.top = `${Math.max(8, Math.min(rect.height - 110, y))}px`;
          tooltip.style.display = "block";
        };

        const getColorForValue = (mode, value, lo, hi) => {
          if (!Number.isFinite(value)) return "#d2d2d2";
          const span = hi - lo || 1;
          const t = clamp01((value - lo) / span);
          const stops = mode === "chirality" ? chiralityStops : conversionStops;
          return interpolateRgbStops(stops, t);
        };

        const applyRepresentation = () => {
          viewer.removeAllSurfaces();
          viewer.setStyle({}, {
            cartoon: { color: "#bfbfbf", opacity: 0.95 },
            stick: { hidden: true },
            sphere: { hidden: true },
            line: { hidden: true },
          });

          // Show non-water hetero atoms (cofactor/ligands) as ball-and-stick.
          viewer.setStyle(
            { hetflag: true, not: { resn: ["HOH", "WAT", "H2O", "DOD"] } },
            {
              stick: { radius: 0.2, colorscheme: "Jmol" },
              sphere: { scale: 0.25, colorscheme: "Jmol" },
            },
          );
        };

        const selectedEffectMap = () => {
          const mode = model.get("color_mode");
          const agg = model.get("aggregation_mode");
          if (mode === "chirality") {
            return agg === "max"
              ? model.get("effects_chirality_max")
              : model.get("effects_chirality_mean");
          }
          return agg === "max"
            ? model.get("effects_conversion_max")
            : model.get("effects_conversion_mean");
        };

        const recolor = () => {
          const mode = model.get("color_mode");
          const raw = selectedEffectMap();

          let effects = {};
          try {
            effects = JSON.parse(raw || "{}");
          } catch (_err) {
            effects = {};
          }

          const numericVals = Object.values(effects)
            .map((x) => Number(x))
            .filter((x) => Number.isFinite(x));
          const lo = numericVals.length ? Math.min(...numericVals) : 0;
          const hi = numericVals.length ? Math.max(...numericVals) : 1;

          applyRepresentation();

          viewer.addSurface(
            $3D.SurfaceType.MS,
            {
              opacity: 0.92,
              colorfunc: (atom) => {
                const key = String(atom.resi);
                const value = Number(effects[key]);
                return getColorForValue(mode, value, lo, hi);
              },
            },
            proteinSel,
          );

          viewer.setStyle(
            proteinSel,
            {
              cartoon: {
                colorfunc: (atom) => {
                  const key = String(atom.resi);
                  const value = Number(effects[key]);
                  return getColorForValue(mode, value, lo, hi);
                },
                opacity: 0.95,
              },
            },
          );

          viewer.zoomTo();
          viewer.render();
        };


        const bindBackgroundClickToHide = () => {
          const canvas = host.querySelector("canvas");
          if (!canvas) return;
          if (canvas.dataset.tooltipHideBound === "1") return;

          const onCanvasClick = () => {
            // Let atom click handlers run first, then decide whether background was clicked.
            setTimeout(() => {
              if (!atomClickedInCycle) {
                hideTooltip();
              }
              atomClickedInCycle = false;
            }, 0);
          };

          canvas.addEventListener("click", onCanvasClick);
          canvas.dataset.tooltipHideBound = "1";
        };

        const reloadStructure = () => {
          viewer.removeAllModels();
          viewer.addModel(model.get("pdb_text"), "pdb");
          viewer.setClickable({}, true, (atom, _viewer, event) => {
            atomClickedInCycle = true;
            showTooltip(atom, event);
          });
          bindBackgroundClickToHide();
          recolor();
        };

        reloadStructure();

        model.on("change:pdb_text", reloadStructure);
        model.on("change:color_mode", recolor);
        model.on("change:aggregation_mode", recolor);
        model.on("change:effects_conversion_mean", recolor);
        model.on("change:effects_conversion_max", recolor);
        model.on("change:effects_chirality_mean", recolor);
        model.on("change:effects_chirality_max", recolor);
        model.on("change:color_mode", hideTooltip);
        model.on("change:aggregation_mode", hideTooltip);
      },
    };
    """

    return (ProteinStructureViewer,)


@app.cell(hide_code=True)
def structure_viewer_markdown(mo):
    mo.md(r"""
    ## Interactive structure coloring

    Use the controls in the next cell, then inspect the structure below.

    - **Color mode:**
      - `conversion` maps activity-like signal
      - `chirality` maps enantiomeric-excess signal
    - **Mutational effect summary:**
      - `mean` highlights average behavior across substitutions
      - `max` highlights best-case opportunities at each position

    Colormaps:
    - conversion: blue -> white -> red
    - chirality: purple -> white -> orange

    Unmeasured residues remain neutral gray.
    """)
    return


@app.cell(hide_code=True)
def protein_structure_coloring_controls(mo):
    color_mode_dropdown = mo.ui.dropdown(
        options=["conversion", "chirality"],
        value="conversion",
        label="Color mode",
    )
    aggregation_mode_dropdown = mo.ui.dropdown(
        options=["mean", "max"],
        value="mean",
        label="Mutational effect summary",
    )
    mo.vstack([color_mode_dropdown, aggregation_mode_dropdown])
    return aggregation_mode_dropdown, color_mode_dropdown


@app.cell(hide_code=True)
def structure_viewer_color_legend(
    aggregation_mode_dropdown,
    color_mode_dropdown,
    effects_chirality_max_json,
    effects_chirality_mean_json,
    effects_conversion_max_json,
    effects_conversion_mean_json,
    json,
    mo,
):
    mode = color_mode_dropdown.value
    aggregation = aggregation_mode_dropdown.value

    if mode == "chirality":
        effect_map = (
            json.loads(effects_chirality_max_json)
            if aggregation == "max"
            else json.loads(effects_chirality_mean_json)
        )
        low_color = "purple"
        high_color = "orange"
        metric_base = "r_enantiomeric_excess"
    else:
        effect_map = (
            json.loads(effects_conversion_max_json)
            if aggregation == "max"
            else json.loads(effects_conversion_mean_json)
        )
        low_color = "blue"
        high_color = "red"
        metric_base = "conversion (mean column)"

    summary_word = "maximum" if aggregation == "max" else "average"
    metric = f"{summary_word} {metric_base}"

    vals = [float(v) for v in effect_map.values()]
    vmin = min(vals) if vals else 0.0
    vmax = max(vals) if vals else 0.0

    mo.md(
        f"""
    ### Color legend ({mode}, {aggregation})

    - **Low {metric}** -> **{low_color}** (min = `{vmin:.4f}`)
    - **Mid-range values** -> **white**
    - **High {metric}** -> **{high_color}** (max = `{vmax:.4f}`)
    - **Gray residues** -> no measurement available
    """
    )
    return


@app.cell(hide_code=True)
def protein_structure_viewer_init(
    ProteinStructureViewer,
    effects_chirality_max_json,
    effects_chirality_mean_json,
    effects_conversion_max_json,
    effects_conversion_mean_json,
    pdb_chain,
    pdb_text,
):
    structure_viewer = ProteinStructureViewer(
        pdb_text=pdb_text,
        pdb_chain=pdb_chain,
        effects_conversion_mean=effects_conversion_mean_json,
        effects_conversion_max=effects_conversion_max_json,
        effects_chirality_mean=effects_chirality_mean_json,
        effects_chirality_max=effects_chirality_max_json,
        color_mode="conversion",
        aggregation_mode="mean",
    )
    return (structure_viewer,)


@app.cell(hide_code=True)
def protein_structure_viewer_show(
    aggregation_mode_dropdown,
    color_mode_dropdown,
    mo,
    structure_viewer,
):
    structure_viewer.color_mode = color_mode_dropdown.value
    structure_viewer.aggregation_mode = aggregation_mode_dropdown.value
    mo.ui.anywidget(structure_viewer)
    return


@app.cell(hide_code=True)
def structure_viewer_interpretation_note(mo):
    mo.md(r"""
    **Reading the map:** Hotter colors mark positions where the *average* mutational effect is higher in the selected assay. Cooler colors mark lower averages. Residues without measurements stay neutral gray.
    """)
    return


@app.cell(hide_code=True)
def viewer_validation_markdown(mo):
    mo.md(r"""
    ## Visualization consistency check

    We close by validating that selected tooltip values match the aggregated Polars tables.
    This confirms the structural colors and annotations are faithful to the underlying data.
    """)
    return


@app.cell(hide_code=True)
def structure_viewer_spot_check_verify(
    df_position_effect_chirality,
    df_position_effect_conversion,
    effects_chirality_json,
    effects_conversion_json,
    json,
    pdb_residue_offset,
    pl,
):
    spot_check_positions = [42, 111, 116]
    spot_rows = []
    conv_map = json.loads(effects_conversion_json)
    chiral_map = json.loads(effects_chirality_json)
    for check_resnum in spot_check_positions:
        key = str(check_resnum)
        assay_pos = check_resnum - pdb_residue_offset
        conv_tbl = df_position_effect_conversion.filter(
            pl.col("position") == assay_pos
        )
        ch_tbl = df_position_effect_chirality.filter(
            pl.col("position") == assay_pos
        )
        spot_rows.append(
            {
                "pdb_residue": check_resnum,
                "assay_position": assay_pos,
                "conversion_avg_table": conv_tbl.get_column(
                    "avg_conversion"
                ).first()
                if conv_tbl.height
                else None,
                "conversion_json": conv_map.get(key),
                "chirality_avg_table": ch_tbl.get_column("avg_chirality").first()
                if ch_tbl.height
                else None,
                "chirality_json": chiral_map.get(key),
            }
        )
    pl.DataFrame(spot_rows)
    return


if __name__ == "__main__":
    app.run()
