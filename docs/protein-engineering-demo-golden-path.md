# Protein Engineering Demo: Live Recreation Prompts

This document is a rewrite of the original golden path script, optimized for **live
recreation** of the `hackathon-demo.py` notebook from scratch in front of an audience.

Each section below is a copy/paste-ready prompt for the Cursor agent that produces one
logical group of **code cells** in the live marimo notebook. Markdown cells are not
prompted for individually — narrate them by hand, or ask the agent to add a leading
markdown cell yourself (the prompts focus on the code that has to be right).

The prompts are written to be self-contained: each one names the input variables it
consumes, the output variables it must produce, the data files it reads, the column
names involved, and the visualization or widget that should appear. Run them in order;
later prompts assume earlier ones have completed successfully.

## Demo Goal

Show an end-to-end agentic protein engineering workflow:

- Load conversion and chirality datasets.
- Identify mutational signal patterns at the sequence level.
- Map those effects onto structure `7OG3`.
- Interactively explore mode (`conversion`/`chirality`) and summary (`mean`/`max`).
- Inspect residue-level values with click tooltips.

## Pre-Demo Setup (2 minutes)

- Open an **empty** marimo notebook to recreate from scratch:
  - `uvx marimo edit --sandbox --no-token hackathon-demo.py`
  - If the file already exists with content, save the existing one aside first
    (e.g. `mv hackathon-demo.py hackathon-demo.reference.py`) so the live demo
    starts blank.
- Confirm data files exist (the prompts will read them):
  - `data/ired-novartis/cs1c02786_si_002.csv`
  - `data/ired-novartis/cs1c02786_si_003.csv`
  - `data/ired-novartis/7OG3.pdb`
- Make sure Cursor is connected to the running marimo notebook via the
  marimo-pair skill (`.agents/skills/marimo-pair/SKILL.md`) so cells go into the
  live kernel, not directly into the `.py` file.
- Toggle code visibility off in marimo for a clean presentation view.

## How to use the prompts

For each section:

1. (Optional) Add a markdown cell yourself with the section's narration / framing.
2. Copy the entire fenced prompt block under "Prompt" into Cursor.
3. Let the agent create the cell(s) and run them in the live notebook.
4. Verify the expected output, then narrate using the talk track.

If a cell fails or names drift, restate the prompt with the exact required variable
names from this doc — every later prompt depends on them.

---

## 1. Notebook imports

**Why**: Single, top-of-notebook imports cell so all later cells can use `mo`, `pl`,
`go`, `Path`, `json`, `anywidget`, and `traitlets` without re-importing.

**Prompt**:

```text
Create a single marimo code cell named `notebook_imports` at the top of the notebook
that imports everything the rest of the notebook will need. It must:

- Import `json` and `Path` from `pathlib`.
- Import `anywidget`.
- Import `marimo as mo`.
- Import `polars as pl`.
- Import `plotly.graph_objects as go`.
- Import `traitlets`.

Return all of these as cell outputs so they are visible to other cells:
`Path, anywidget, go, json, mo, pl, traitlets`.

No other code in this cell. Do not import anything in any other cell later.
```

---

## 2. Load the conversion assay table

**Why**: Brings in the conversion (`mean`) values keyed by `mutation`.

**Prompt**:

```text
Create a marimo code cell named `load_conversion_table` that:

- Reads `data/ired-novartis/cs1c02786_si_002.csv` with `pl.read_csv` using a `Path`.
- Stores the resulting DataFrame as `df_conversion`.
- Displays `df_conversion` as the cell output (last expression).
- Returns `df_conversion` so other cells can use it.

Use the `Path` and `pl` already imported in `notebook_imports`. The relevant columns
in this file include `mutation` (string) and `mean` (float, the conversion metric).
```

---

## 3. Load the chirality assay table

**Why**: Brings in the enantiomeric excess (`r_enantiomeric_excess`) values keyed by
`mutation`.

**Prompt**:

```text
Create a marimo code cell named `load_chirality_table` that:

- Reads `data/ired-novartis/cs1c02786_si_003.csv` with `pl.read_csv` using a `Path`.
- Stores the resulting DataFrame as `df_chirality`.
- Displays `df_chirality` as the cell output.
- Returns `df_chirality`.

The relevant columns include `mutation` (string) and `r_enantiomeric_excess` (float).
```

---

## 4. Build the intersection dataset

**Why**: Restricts to mutants present in both tables so we can fairly compare the two
objectives.

**Prompt**:

```text
Create a marimo code cell named `prepare_intersection_dataset` that builds an
intersection of `df_chirality` and `df_conversion` on the `mutation` column.

Requirements:

- Select only `["mutation", "r_enantiomeric_excess"]` from `df_chirality` and
  `["mutation", "mean"]` from `df_conversion`.
- Inner-join them on `mutation`.
- Drop rows where any of `mutation`, `r_enantiomeric_excess`, or `mean` is null.
- Keep only unique mutations (`unique(subset=["mutation"])`).
- Sort by `mutation`.
- Add a row index column named `mutation_index` with `with_row_index`.
- Store the result as `df_intersection` and display it as the cell output.
- Return `df_intersection`.
```

---

## 5. Conversion vs chirality scatter

**Why**: Visualizes whether the two objectives co-vary at the intersection mutants.

**Prompt**:

```text
Create a marimo code cell named `plotly_intersection_scatter` that produces a Plotly
scatter plot from `df_intersection`:

- x-axis: `df_intersection["mean"]` (conversion).
- y-axis: `df_intersection["r_enantiomeric_excess"]` (chirality).
- mode: `"markers"`, marker `size=8`, `opacity=0.75`.
- `text` per point should be the `mutation` string.
- `hovertemplate` should show `mutation`, `mean` (4 decimals), and
  `r_enantiomeric_excess` (4 decimals), with `<extra></extra>` to hide the trace box.
- Title: "Intersection mutants: conversion vs chirality".
- x-axis title: "mean (conversion)".
- y-axis title: "r_enantiomeric_excess (chirality)".

Build it with `go.Figure(data=go.Scatter(...))`. Display the figure as the cell
output. No return values needed.
```

---

## 6. ECDFs for both metrics

**Why**: Shows distribution shape side-by-side without binning artifacts.

**Prompt**:

```text
Create a marimo code cell named `plotly_value_ecdfs` that plots ECDFs for the
conversion and chirality values in `df_intersection`.

Requirements:

- Define a local helper `def ecdf(values: list[float]) -> tuple[list[float], list[float]]`
  that sorts the values and returns `(sorted_values, [(i+1)/n for i in range(n)])`.
- Compute `mean_values` from `df_intersection["mean"]` and `chirality_values` from
  `df_intersection["r_enantiomeric_excess"]`, casting each entry to `float`.
- Compute ECDF arrays for both.
- Create a `go.Figure` with two `go.Scatter` traces, both `mode="lines"` and
  `line=dict(shape="hv")` (step ECDF).
  - Trace 1 name: "mean (conversion)".
  - Trace 2 name: "r_enantiomeric_excess (chirality)".
- Title: "ECDFs for conversion and chirality values".
- x-axis title: "Value".
- y-axis title: "ECDF".
- Display the figure as the cell output. No return values needed.
```

---

## 7. Single-point mutant heatmap

**Why**: Reveals position × amino-acid hotspots in conversion, with chirality available
on hover.

**Prompt**:

```text
Create a marimo code cell named `plot_single_point_heatmap` that builds a
position × mutated-amino-acid heatmap colored by mean conversion.

Step 1 — derive `df_single_point` from `df_conversion`:

- Filter where `mutation` is not null.
- Filter out rows whose `mutation` contains `;` (multi-mutants).
- Keep only canonical single substitutions matching the regex `^[A-Z]\d+[A-Z]$`.
- Add columns:
  - `position` (Int64) extracted with `^[A-Z](\d+)[A-Z]$` capture group 1.
  - `mut_aa` (string) extracted with `^[A-Z]\d+([A-Z])$` capture group 1.

Step 2 — left-join `df_chirality.select(["mutation", "r_enantiomeric_excess"])`
onto the filtered table on `mutation` to bring in chirality where available.

Step 3 — group by `["position", "mut_aa"]` and aggregate:
- `pl.col("mean").mean().alias("mean")`.
- `pl.col("mutation").first().alias("example_mutation")`.
- `pl.col("r_enantiomeric_excess").mean().alias("r_enantiomeric_excess")`.
- `pl.len().alias("n_records")`.

Step 4 — build a Plotly `go.Heatmap`:

- x = sorted unique positions, y = sorted unique mut_aa letters.
- `z_matrix` of shape (len(y), len(x)) populated from the grouped table; missing
  cells stay `None`.
- `text_matrix` aligned to `z_matrix` with HTML-newline strings:
  `"mutation={example_mutation}<br>r_enantiomeric_excess={chirality_text}<br>n_records={n_records}"`,
  where `chirality_text` is `"NA"` when null else `f"{value:.4f}"`.
- `colorscale="Viridis"`, colorbar title "mean".
- `hovertemplate`:
  `"position=%{x}<br>mutation_letter=%{y}<br>mean=%{z:.4f}<br>%{text}<extra></extra>"`.
- Title: "Single-point mutants: conversion heatmap".
- x-axis title: "Position", y-axis title: "Mutation letter".

Step 5 — display the figure as the cell output and return `df_single_point` so later
cells can reuse the filtered single-point table.
```

---

## 8. Average mutational effect by position

**Why**: Collapses amino-acid identity to a single per-position sensitivity signal.

**Prompt**:

```text
Create a marimo code cell named `plot_average_effect_by_position` that:

- Builds `df_position_effect` from `df_single_point` by grouping on `position`,
  aggregating `pl.col("mean").mean().alias("average_mutational_effect")`, and
  sorting by `position`.
- Renders a Plotly line+marker chart:
  - x: `df_position_effect["position"]`.
  - y: `df_position_effect["average_mutational_effect"]`.
  - mode: `"lines+markers"`, marker `size=5`, line `width=2`.
  - hovertemplate:
    `"position=%{x}<br>average_mutational_effect=%{y:.4f}<extra></extra>"`.
  - Title: "Average mutational effect by position".
  - x-axis title: "Position", y-axis title: "Average mutational effect".
- Displays the figure as the cell output.
- No return values are needed.
```

---

## 9. Build mean and max position-effect tables

**Why**: Produces the four per-position summary tables (mean/max × conversion/chirality)
that the structure viewer will consume.

**Prompt**:

```text
Create a marimo code cell named `build_position_effect_tables` that builds four
per-position summary tables and one combined table.

Step 1 — derive `df_single_point_chirality` from `df_chirality`:
- Filter `mutation` not null, exclude rows containing `;`, keep regex
  `^[A-Z]\d+[A-Z]$`.
- Add `position` (Int64) extracted from capture group 1 of `^[A-Z](\d+)[A-Z]$`.

Step 2 — build summary tables, all sorted by `position`:
- `df_position_effect_conversion`: from `df_single_point`, group by `position`,
  aggregate `pl.col("mean").mean().alias("avg_conversion")`.
- `df_position_effect_conversion_max`: same but `.max().alias("max_conversion")`.
- `df_position_effect_chirality`: from `df_single_point_chirality`, group by
  `position`, aggregate
  `pl.col("r_enantiomeric_excess").mean().alias("avg_chirality")`.
- `df_position_effect_chirality_max`: same but `.max().alias("max_chirality")`.

Step 3 — build `df_position_effects`:
- Concatenate the `position` columns from all four tables, take unique positions,
  sort.
- Left-join the four summary tables onto that position spine in this order:
  conversion mean, conversion max, chirality mean, chirality max.

Step 4 — display `df_position_effects` as the cell output.

Return:
`df_position_effect_chirality, df_position_effect_chirality_max,
df_position_effect_conversion, df_position_effect_conversion_max`.
```

---

## 10. PDB sequence validation and residue-level effect maps

**Why**: Aligns assay numbering to PDB residue numbering, validates wild-type letters,
and produces JSON-encoded per-residue effect maps for the widget.

**Prompt**:

```text
Create a marimo code cell named `pdb_sequence_validation_and_effect_maps` that
validates the PDB↔assay numbering and emits per-residue effect maps as JSON strings.

Inputs (already in scope):
`Path`, `df_position_effect_chirality`, `df_position_effect_chirality_max`,
`df_position_effect_conversion`, `df_position_effect_conversion_max`,
`df_single_point`, `json`, `mo`, `pl`.

Step 1 — define a constant `AA3_TO_AA1` mapping standard 3-letter amino-acid codes
to single-letter codes. Map `MSE` to `M` as well. Cover all 20 standard amino acids.

Step 2 — define a helper `parse_pdb_chain_residues(pdb_text: str, chain_id: str) -> dict[int, str]`
that:
- Iterates lines, skipping any shorter than 27 chars.
- Considers only lines whose record name (`line[0:6].strip()`) is `ATOM` or `HETATM`.
- Skips lines whose chain id (`line[21:22]`) does not match `chain_id`.
- Reads `resname = line[17:20].strip()` and `resseq = int(line[22:26])` (skip on
  ValueError).
- Skips residues whose resname is not in `AA3_TO_AA1`.
- Records `residues[resseq] = aa` (later occurrences overwrite earlier ones, that
  is fine).
- Returns the dict.

Step 3 — define a helper `build_effect_map(table, value_col: str) -> dict[str, float]`
that iterates `table.iter_rows(named=True)`, skips null `value_col`, and writes
`out[str(int(row["position"]) + pdb_residue_offset)] = float(val)`.

Step 4 — read PDB and parse residues:
- `pdb_path = Path("data/ired-novartis/7OG3.pdb")`.
- `pdb_text = pdb_path.read_text()`.
- `pdb_chain = "A"`.
- `pdb_residues = parse_pdb_chain_residues(pdb_text, pdb_chain)`.

Step 5 — derive wild-type letter per assay position from `df_single_point`:
group by `position`, take the first `mutation`, slice the first character as
`wt_aa`, sort by `position`. Pull out `positions` and `wt_aas` lists.

Step 6 — search for `pdb_residue_offset` over `range(-20, 21)` that maximizes the
number of `pdb_residues.get(pos + offset) == wt` matches. Record the best score and
offset.

Step 7 — build a validation table as `df_pdb_mapping_validation` with columns
`assay_position`, `pdb_residue`, `wt_aa`, `pdb_aa`,
`match` (bool, false if `pdb_aa` is None), `has_structure` (bool).

Step 8 — compute counts: `mapping_matched`, `mapping_mismatch`
(has_structure & ~match), `mapping_unmapped` (~has_structure).

Step 9 — build effect maps and JSON-encode them:
- `effects_conversion_mean = build_effect_map(df_position_effect_conversion, "avg_conversion")`.
- `effects_chirality_mean = build_effect_map(df_position_effect_chirality, "avg_chirality")`.
- `effects_conversion_max = build_effect_map(df_position_effect_conversion_max, "max_conversion")`.
- `effects_chirality_max = build_effect_map(df_position_effect_chirality_max, "max_chirality")`.
- `effects_conversion_json = json.dumps(effects_conversion_mean)`  (legacy/back-compat name).
- `effects_chirality_json = json.dumps(effects_chirality_mean)`     (legacy/back-compat name).
- `effects_conversion_mean_json = json.dumps(effects_conversion_mean)`.
- `effects_conversion_max_json  = json.dumps(effects_conversion_max)`.
- `effects_chirality_mean_json  = json.dumps(effects_chirality_mean)`.
- `effects_chirality_max_json   = json.dumps(effects_chirality_max)`.

Step 10 — display a `mo.vstack` with:
- A markdown summary string:
  `"PDB mapping chain **{pdb_chain}**, residue offset **{pdb_residue_offset}** "
   "(best agreement with assay wild-type letters): matched **{mapping_matched}**, "
   "mismatch **{mapping_mismatch}**, unmapped **{mapping_unmapped}**."`.
- The first 12 rows of mismatched (has_structure & ~match) rows.

Return:
`effects_chirality_json, effects_chirality_max_json, effects_chirality_mean_json,
effects_conversion_json, effects_conversion_max_json, effects_conversion_mean_json,
pdb_chain, pdb_residue_offset, pdb_text`.
```

---

## 11. Define the `ProteinStructureViewer` anywidget

**Why**: This is the heaviest cell. It defines the 3Dmol.js-backed anywidget with
synced traitlets for PDB text and effect maps, plus tooltip and recolor logic.

**Prompt**:

```text
Create a marimo code cell named `define_protein_structure_viewer_widget` that
defines an `anywidget.AnyWidget` subclass `ProteinStructureViewer` for rendering a
PDB structure with two color modes (conversion/chirality) and two aggregation
modes (mean/max), backed by 3Dmol.js loaded from a CDN.

Python side — synced traitlets (`.tag(sync=True)`):
- `pdb_text: traitlets.Unicode("")`.
- `pdb_chain: traitlets.Unicode("A")`.
- `effects_conversion_mean: traitlets.Unicode("{}")`.
- `effects_conversion_max: traitlets.Unicode("{}")`.
- `effects_chirality_mean: traitlets.Unicode("{}")`.
- `effects_chirality_max: traitlets.Unicode("{}")`.
- `color_mode: traitlets.Unicode("conversion")`.
- `aggregation_mode: traitlets.Unicode("mean")`.

Set `_esm` to a raw string (`r"""..."""`) implementing
`export default { async render({ model, el }) { ... } }` with this behavior:

1. Replace `el`'s children with a `div` host of `100% × 520px`.
2. Lazy-load 3Dmol.js v2.1.0 from
   `https://cdn.jsdelivr.net/npm/3dmol@2.1.0/build/3Dmol-min.js` only if
   `globalThis.$3Dmol` is not already present. Resolve once `script.onload`.
3. Create a viewer with `globalThis.$3Dmol.createViewer(host, { backgroundColor: "white" })`.
4. Define a `proteinSel` selector that excludes water:
   `{ not: { resn: ["HOH", "WAT", "H2O", "DOD"] } }`.
5. Implement helpers `clamp01`, `lerp`, and `interpolateRgbStops(stops, tRaw)` that
   linearly interpolate over RGB stop arrays of the form `[t, [r, g, b]]`.
6. Define two color-stop arrays:
   - `conversionStops`: blue → muted blue → white → orange → red, at t = 0, 0.35,
     0.5, 0.7, 1.0. Use the RGB values
     `[49,54,149]`, `[69,117,180]`, `[247,247,247]`, `[253,174,97]`, `[165,0,38]`.
   - `chiralityStops`: deep purple → light purple → white → light orange → orange,
     same t-stops, with RGB
     `[94,60,153]`, `[178,171,210]`, `[247,247,247]`, `[253,184,99]`, `[230,97,1]`.
7. Build a positioned `tooltip` div appended to `el` (after setting
   `el.style.position = "relative"`):
   absolute positioning, pointer-events none, dark background `rgba(20,20,20,0.9)`,
   white text, 6×8px padding, 6px radius, 12px font, sans-serif, line-height 1.35,
   z-index 1000, hidden by default.
8. Define a `hideTooltip` helper that sets display to `"none"`.
9. Inside the JS, define an `AA3_TO_AA1` object that mirrors the Python mapping
   (including `MSE: "M"`).
10. Define `selectedEffectMap()` that returns the current JSON string based on
    `model.get("color_mode")` and `model.get("aggregation_mode")`.
11. Define `effectMapForCurrentSelection()` that JSON-parses
    `selectedEffectMap()`, returning `{}` on parse error.
12. Maintain `let atomClickedInCycle = false;` to disambiguate atom clicks from
    background clicks in the same event cycle.
13. Define `showTooltip(atom, event)` that:
    - Reads `mode`, `agg`, and the current effect map.
    - Looks up `value = Number(effects[String(atom.resi)])`, formatting NaN as
      `"NA"` and otherwise `value.toFixed(4)`.
    - Looks up `wtAA = AA3_TO_AA1[String(atom.resn).toUpperCase()] ?? "?"`.
    - Sets `tooltip.innerHTML` with bold rows for Chain, Residue, WT AA (showing
      `wtAA (resn)`), Mode, Summary, Value.
    - Positions the tooltip relative to `host.getBoundingClientRect()` using
      `event.clientX`/`clientY` (with sensible fallbacks), clamping inside the
      viewer with margins.
    - Sets `tooltip.style.display = "block"`.
14. Define `getColorForValue(mode, value, lo, hi)`:
    - Returns `"#d2d2d2"` for non-finite values.
    - Otherwise normalizes `(value - lo) / (hi - lo || 1)`, picks
      `chiralityStops` when mode is `"chirality"` else `conversionStops`, and
      returns `interpolateRgbStops(stops, t)`.
15. Define `applyRepresentation()` that removes all surfaces and sets a base style:
    cartoon `#bfbfbf` opacity 0.95, hides stick/sphere/line, then sets non-water
    hetatms to ball-and-stick with `colorscheme: "Jmol"` (stick radius 0.2,
    sphere scale 0.25). The hetatm selector should be
    `{ hetflag: true, not: { resn: ["HOH", "WAT", "H2O", "DOD"] } }`.
16. Define `recolor()`:
    - Parse the current effect map.
    - Compute `lo = Math.min(...numericVals)` and `hi = Math.max(...numericVals)`,
      defaulting to 0/1 when the map is empty.
    - Call `applyRepresentation()`.
    - Add an MS surface with opacity 0.92 and a `colorfunc` that calls
      `getColorForValue(mode, value, lo, hi)` per residue, restricted to
      `proteinSel`.
    - Set cartoon style on `proteinSel` with the same colorfunc and opacity 0.95.
    - `viewer.zoomTo(); viewer.render();`.
17. Define `bindBackgroundClickToHide()`:
    - Find `host.querySelector("canvas")`. Skip if `dataset.tooltipHideBound === "1"`.
    - Add a click handler that uses `setTimeout(..., 0)` to wait one tick: if
      `atomClickedInCycle` is still false, call `hideTooltip()`. Always reset
      `atomClickedInCycle = false`.
    - Mark `canvas.dataset.tooltipHideBound = "1"`.
18. Define `reloadStructure()`:
    - `viewer.removeAllModels()`.
    - `viewer.addModel(model.get("pdb_text"), "pdb")`.
    - `viewer.setClickable({}, true, (atom, _viewer, event) => { atomClickedInCycle = true; showTooltip(atom, event); })`.
    - Call `bindBackgroundClickToHide()` and `recolor()`.
19. Call `reloadStructure()` once at startup, then wire model listeners:
    - `change:pdb_text` → `reloadStructure`.
    - `change:color_mode`, `change:aggregation_mode`, and each of the four
      `change:effects_*` traitlets → `recolor`.
    - `change:color_mode` and `change:aggregation_mode` → `hideTooltip`.

Return `(ProteinStructureViewer,)` from the cell.
```

---

## 12. Coloring controls

**Why**: Two `mo.ui.dropdown` widgets that drive the viewer.

**Prompt**:

```text
Create a marimo code cell named `protein_structure_coloring_controls` that:

- Defines `color_mode_dropdown = mo.ui.dropdown(options=["conversion", "chirality"], value="conversion", label="Color mode")`.
- Defines `aggregation_mode_dropdown = mo.ui.dropdown(options=["mean", "max"], value="mean", label="Mutational effect summary")`.
- Displays both stacked vertically with `mo.vstack([color_mode_dropdown, aggregation_mode_dropdown])` as the cell output.
- Returns `aggregation_mode_dropdown, color_mode_dropdown`.
```

---

## 13. Color legend

**Why**: Reactive markdown legend that updates with the dropdowns and shows
min/max for the currently selected effect map.

**Prompt**:

```text
Create a marimo code cell named `structure_viewer_color_legend` that renders a
markdown legend reflecting the current dropdown selections.

Inputs in scope: `aggregation_mode_dropdown`, `color_mode_dropdown`,
`effects_chirality_max_json`, `effects_chirality_mean_json`,
`effects_conversion_max_json`, `effects_conversion_mean_json`, `json`, `mo`.

Behavior:

- `mode = color_mode_dropdown.value`, `aggregation = aggregation_mode_dropdown.value`.
- Pick `effect_map`, `low_color`, `high_color`, `metric_base` based on the dropdowns:
  - `mode == "chirality"`:
    - `effect_map = json.loads(effects_chirality_max_json if aggregation == "max" else effects_chirality_mean_json)`.
    - `low_color = "purple"`, `high_color = "orange"`.
    - `metric_base = "r_enantiomeric_excess"`.
  - else:
    - `effect_map = json.loads(effects_conversion_max_json if aggregation == "max" else effects_conversion_mean_json)`.
    - `low_color = "blue"`, `high_color = "red"`.
    - `metric_base = "conversion (mean column)"`.
- `summary_word = "maximum" if aggregation == "max" else "average"`.
- `metric = f"{summary_word} {metric_base}"`.
- `vals = [float(v) for v in effect_map.values()]`; `vmin`/`vmax` default to 0.0
  when empty.
- Render `mo.md(...)` with a header `### Color legend ({mode}, {aggregation})` and
  bullets for low / mid / high / gray (no measurement), formatting `vmin` and
  `vmax` to 4 decimals.
- No return values needed.
```

---

## 14. Initialize the structure viewer

**Why**: Constructs a single long-lived `ProteinStructureViewer` instance so the
viewer's internal state (camera, click handlers) is preserved across dropdown
changes.

**Prompt**:

```text
Create a marimo code cell named `protein_structure_viewer_init` that constructs the
viewer instance.

Inputs in scope: `ProteinStructureViewer`, `effects_chirality_max_json`,
`effects_chirality_mean_json`, `effects_conversion_max_json`,
`effects_conversion_mean_json`, `pdb_chain`, `pdb_text`.

Build:

```
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
```

Return `(structure_viewer,)`. Do not display it here — the next cell will display
it bound to the dropdowns.
```

---

## 15. Show the structure viewer wired to the dropdowns

**Why**: Pushes dropdown values into the long-lived viewer, then renders it via
`mo.ui.anywidget`.

**Prompt**:

```text
Create a marimo code cell named `protein_structure_viewer_show` that:

- Sets `structure_viewer.color_mode = color_mode_dropdown.value`.
- Sets `structure_viewer.aggregation_mode = aggregation_mode_dropdown.value`.
- Displays `mo.ui.anywidget(structure_viewer)` as the cell output.
- No return values needed.

Inputs in scope: `aggregation_mode_dropdown`, `color_mode_dropdown`, `mo`,
`structure_viewer`.
```

At this point you can demo the interactions live:

- Toggle **Color mode**: `conversion` → `chirality`.
- Toggle **Mutational effect summary**: `mean` → `max`.
- Click a residue to show the tooltip; click whitespace to dismiss it.

---

## 16. Spot-check verification

**Why**: Final consistency check that the residue-keyed effect maps match the
Polars summary tables.

**Prompt**:

```text
Create a marimo code cell named `structure_viewer_spot_check_verify` that builds a
small Polars DataFrame comparing the JSON-encoded effect maps to the original
mean Polars tables for a fixed list of PDB residue numbers.

Inputs in scope: `df_position_effect_chirality`, `df_position_effect_conversion`,
`effects_chirality_json`, `effects_conversion_json`, `json`, `pdb_residue_offset`,
`pl`.

Behavior:

- `spot_check_positions = [42, 111, 116]`.
- `conv_map = json.loads(effects_conversion_json)`.
- `chiral_map = json.loads(effects_chirality_json)`.
- For each `check_resnum` in `spot_check_positions`:
  - `key = str(check_resnum)`.
  - `assay_pos = check_resnum - pdb_residue_offset`.
  - Filter `df_position_effect_conversion` to `position == assay_pos`; call this `conv_tbl`.
  - Filter `df_position_effect_chirality` to `position == assay_pos`; call this `ch_tbl`.
  - Append a dict with keys
    `pdb_residue`, `assay_position`,
    `conversion_avg_table` (`conv_tbl.get_column("avg_conversion").first()` if
    `conv_tbl.height` else `None`),
    `conversion_json` (`conv_map.get(key)`),
    `chirality_avg_table` (`ch_tbl.get_column("avg_chirality").first()` if
    `ch_tbl.height` else `None`),
    `chirality_json` (`chiral_map.get(key)`).
- Display `pl.DataFrame(spot_rows)` as the cell output.
- No return values needed.
```

---

## Talk Track (Narration Script)

This is unchanged from the original golden path script. Use it after each cell or
group of cells executes successfully.

### 0:00–2:00 — Framing
- "We are going from mutational assay tables to structure-aware interpretation in one notebook."
- "This uses conversion and chiral selectivity as two optimization objectives."

### 2:00–5:00 — Data Ingestion
- After prompts 2–3 land.
- "We load two complementary assay tables: conversion and enantiomeric excess."
- "The downstream flow keeps these separate so we can compare objectives cleanly."

### 5:00–8:00 — Correlation Check
- After prompts 4–6 land.
- "At mutant intersection, conversion and chirality are not strongly correlated."
- "That means optimizing one objective may not automatically optimize the other."

### 8:00–12:00 — Sequence-Level Mutational Landscapes
- After prompts 7–8 land.
- "The heatmap highlights positional hotspots and identifies where mutation matters most."
- "Hotspots indicate exploitable sequence regions for directed engineering."

### 12:00–15:00 — Structure Mapping
- After prompts 9–10 land.
- "We map assay positions to PDB residues and validate wild-type consistency."
- "Then we project per-position summaries into structure-space."

### 15:00–19:00 — Interactive Structure Analysis
- After prompts 11–15 land.
- Demo interactions live (see prompt 15).
- "Now we can compare objective-specific structural patterns interactively."
- "The same scaffold supports both average and best-case mutational perspectives."

### 19:00–20:00 — Close
- After prompt 16 lands.
- "Spot checks confirm map values match the underlying aggregated tables."
- "This gives confidence that structural colors are faithful to assay data."

## Audience-Facing Key Messages

- Conversion and chirality can decouple; multi-objective thinking is required.
- Sequence-space hotspots become actionable when mapped into structure context.
- Interactive visualization helps prioritize mutation campaigns by site and objective.

## Live Demo Interaction Checklist

- Change color mode and mention legend updates.
- Change mean/max and explain why max can surface opportunistic pockets.
- Click at least 2–3 residues and read the tooltip aloud.
- Click background once to show tooltip dismissal behavior.
- Briefly point out ligand/cofactor displayed as ball-and-stick.

## Backup / Recovery Notes

If something goes sideways during live recreation:

- **Cell name drift**: if a downstream prompt errors with `NameError`, the most
  likely cause is that an earlier cell did not return the expected variable name.
  Re-issue the earlier prompt and explicitly call out the missing return name from
  this doc.
- **Stale widget**: re-run, in order, prompts 11 (`define_protein_structure_viewer_widget`),
  14 (`protein_structure_viewer_init`), 15 (`protein_structure_viewer_show`).
- **Controls not propagating**: re-run prompts 12 (`protein_structure_coloring_controls`),
  13 (`structure_viewer_color_legend`), 15 (`protein_structure_viewer_show`).
- **Total reset**: restart the marimo kernel and re-run the prompts in order from 1.
- **Reference**: the original `hackathon-demo.py` (or the `.reference.py` copy from
  pre-demo setup) is the source of truth for any cell whose output you want to
  diff against the live recreation.
