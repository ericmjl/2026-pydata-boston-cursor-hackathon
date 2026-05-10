# Protein Engineering Demo: Live Recreation Prompts

This document is a rewrite of the original golden path script, optimized for **live
recreation** of the `hackathon-demo.py` notebook from scratch in front of an audience.

Each numbered section below is a copy/paste-ready prompt for the Cursor agent. With
`AGENTS.md` and the `marimo-pair` skill in scope, the agent already knows to create
or edit cells in the live marimo kernel (not the `.py` file) and to handle imports
per cell — so the prompts focus on what each cell should *do*, not on the mechanics.

Markdown cells are not prompted for individually. Narrate them by hand, or ask the
agent to add a leading markdown cell yourself (the prompts here focus on the code
cells that have to be right for downstream cells to work).

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
  `marimo-pair` skill so cells go into the live kernel.
- Toggle code visibility off in marimo for a clean presentation view.

## How to use the prompts

For each section:

1. (Optional) Add a markdown cell yourself with the section's narration / framing.
2. Copy the entire fenced prompt block under "Prompt" into Cursor.
3. Let the agent create the cell in the live notebook and run it.
4. Verify the expected output, then narrate using the talk track.

---

## 1. Load the conversion assay table

**Why**: Brings in the conversion (`mean`) values keyed by `mutation`.

**Prompt**:

```text
Load `data/ired-novartis/cs1c02786_si_002.csv` into a polars DataFrame called
`df_conversion` and display it. The columns of interest are `mutation` (string)
and `mean` (float, the conversion metric).
```

---

## 2. Load the chirality assay table

**Why**: Brings in enantiomeric excess values keyed by `mutation`.

**Prompt**:

```text
Load `data/ired-novartis/cs1c02786_si_003.csv` into `df_chirality` and display it.
Relevant columns are `mutation` (string) and `r_enantiomeric_excess` (float).
```

---

## 3. Build the intersection dataset

**Why**: Restricts to mutants present in both tables for a fair comparison.

**Prompt**:

```text
Build `df_intersection` from `df_chirality.select(["mutation", "r_enantiomeric_excess"])`
inner-joined with `df_conversion.select(["mutation", "mean"])` on `mutation`. Drop
rows null in any of those three columns, deduplicate on `mutation`, sort by
`mutation`, and add a `mutation_index` row-index column. Display the table.
```

---

## 4. Conversion vs chirality scatter

**Why**: Visualizes whether the two objectives co-vary.

**Prompt**:

```text
Plot `df_intersection["mean"]` (x, conversion) against
`df_intersection["r_enantiomeric_excess"]` (y, chirality) as a Plotly scatter:
markers only, size 8, opacity 0.75, with the `mutation` string as per-point hover
text. The hovertemplate should show `mutation`, `mean` (4 decimals), and
`r_enantiomeric_excess` (4 decimals), with `<extra></extra>` to hide the trace
box. Title "Intersection mutants: conversion vs chirality"; axis titles
"mean (conversion)" and "r_enantiomeric_excess (chirality)".
```

---

## 5. ECDFs for both metrics

**Why**: Distribution shape side by side, no binning artifacts.

**Prompt**:

```text
Plot ECDFs of `df_intersection["mean"]` and `df_intersection["r_enantiomeric_excess"]`
as two step-line traces on a single Plotly figure (use `line=dict(shape="hv")`).
Define a small local helper that returns `(sorted_values, [(i + 1) / n for i in range(n)])`.
Name the traces "mean (conversion)" and "r_enantiomeric_excess (chirality)". Title
"ECDFs for conversion and chirality values"; axes "Value" and "ECDF".
```

---

## 6. Single-point mutant heatmap

**Why**: Reveals position × amino-acid hotspots in conversion, with chirality on hover.
Also produces `df_single_point`, reused by later prompts.

**Prompt**:

```text
Filter `df_conversion` to canonical single substitutions matching `^[A-Z]\d+[A-Z]$`
(non-null `mutation`, no `;`), then add `position` (Int64) and `mut_aa` (string)
columns extracted from the regex capture groups; call the result `df_single_point`.
Left-join `df_chirality.select(["mutation", "r_enantiomeric_excess"])` on `mutation`,
group by `["position", "mut_aa"]`, and aggregate conversion mean (alias `mean`), an
example mutation (`first`, alias `example_mutation`), chirality mean, and `pl.len()`
as `n_records`. Plot as a Plotly heatmap with sorted positions on x, sorted mut_aa
letters on y, the aggregated mean as z (missing cells stay `None`), Viridis colorscale,
colorbar title "mean", per-cell text formatted as
`"mutation={example}<br>r_enantiomeric_excess={value or NA}<br>n_records={n}"`, and
hovertemplate
`"position=%{x}<br>mutation_letter=%{y}<br>mean=%{z:.4f}<br>%{text}<extra></extra>"`.
Title "Single-point mutants: conversion heatmap".
```

---

## 7. Average mutational effect by position

**Why**: Collapses amino-acid identity to a single per-position sensitivity signal.

**Prompt**:

```text
From `df_single_point`, build `df_position_effect` by grouping on `position`,
aggregating `pl.col("mean").mean().alias("average_mutational_effect")`, sorted by
`position`. Plot as a Plotly lines+markers Scatter (marker size 5, line width 2)
with hovertemplate
`"position=%{x}<br>average_mutational_effect=%{y:.4f}<extra></extra>"`. Title
"Average mutational effect by position"; axes "Position" and "Average mutational
effect".
```

---

## 8. Mean and max position-effect tables

**Why**: Four per-position summary tables (mean/max × conversion/chirality) feed the
structure viewer.

**Prompt**:

```text
Apply the same single-point filter (canonical `^[A-Z]\d+[A-Z]$`, no `;`, non-null) to
`df_chirality` to produce `df_single_point_chirality` with a `position` (Int64) column.
Then build four per-position summary tables, each sorted by `position`:
`df_position_effect_conversion` (mean of `mean`, aliased `avg_conversion`) and
`df_position_effect_conversion_max` (max, aliased `max_conversion`) from
`df_single_point`; `df_position_effect_chirality` (mean `r_enantiomeric_excess`,
aliased `avg_chirality`) and `df_position_effect_chirality_max` (max, aliased
`max_chirality`) from `df_single_point_chirality`. Concatenate the `position`
columns of all four, take unique sorted positions, and left-join the four tables
onto that spine in order conv-mean, conv-max, chir-mean, chir-max to build a
combined `df_position_effects`; display it.
```

---

## 9. PDB parse and residue offset

**Why**: Aligns assay numbering to PDB residue numbering and validates WT letters.

**Prompt**:

```text
Read `data/ired-novartis/7OG3.pdb` into `pdb_text` and parse chain "A" residues into
a `dict[int, str]` mapping `resseq` → 1-letter amino-acid code. Use the standard 20-AA
3-letter to 1-letter mapping plus `MSE -> M`; iterate `ATOM`/`HETATM` lines using
columns 0–6 for record, 17–20 for resname, 21 for chain, 22–26 for resseq. Derive the
wild-type letter per assay `position` by slicing the first character of the first
mutation in each group of `df_single_point`. Search offsets in `range(-20, 21)` for
the value that maximizes wild-type letter agreement, and bind it as
`pdb_residue_offset`. Build `df_pdb_mapping_validation` with columns `assay_position`,
`pdb_residue`, `wt_aa`, `pdb_aa`, `match`, `has_structure`, then display a markdown
summary (chain, offset, counts of matched / mismatched / unmapped positions) stacked
with the first 12 rows of mismatched-with-structure positions.
```

---

## 10. JSON-encoded residue effect maps

**Why**: Serializes per-residue effect maps for the anywidget traitlets.

**Prompt**:

```text
Build a per-residue effect map (keyed by `str(pdb_residue)`) from each of the four
position-effect tables, dropping null rows and computing
`pdb_residue = int(row["position"]) + pdb_residue_offset`. JSON-encode them as
`effects_conversion_mean_json`, `effects_conversion_max_json`,
`effects_chirality_mean_json`, and `effects_chirality_max_json`, plus aliases
`effects_conversion_json` (= mean conversion) and `effects_chirality_json` (= mean
chirality) for back-compat with the spot-check cell later.
```

---

## 11. Basic structure viewer widget

**Why**: Start small — just render the PDB as an anywidget. We'll layer coloring and
the tooltip onto this same class in the next two prompts.

**Prompt**:

```text
Define an `anywidget.AnyWidget` subclass `ProteinStructureViewer` with a single
synced trait `pdb_text = traitlets.Unicode("")`. The `_esm` should lazy-load
3Dmol.js v2.1.0 from `https://cdn.jsdelivr.net/npm/3dmol@2.1.0/build/3Dmol-min.js`
only if `globalThis.$3Dmol` is not already present, then create a viewer inside a
100% × 520px host div with a white background. Render the protein with a uniform
gray cartoon (`#bfbfbf`, opacity 0.95), and display non-water HETATMs (selector
`{ hetflag: true, not: { resn: ["HOH", "WAT", "H2O", "DOD"] } }`) as ball-and-stick
with `colorscheme: "Jmol"` (stick radius 0.2, sphere scale 0.25). Re-zoom and
re-render on `change:pdb_text`. Also add a quick init/show cell that constructs
`structure_viewer = ProteinStructureViewer(pdb_text=pdb_text)` and renders it with
`mo.ui.anywidget(structure_viewer)` so we can confirm the structure loads before
adding any coloring.
```

---

## 12. Add surface coloring to the viewer

**Why**: Project the per-residue effect maps onto the structure as a Molecular
Surface, with two color modes (`conversion`/`chirality`) and two summary modes
(`mean`/`max`).

**Prompt**:

```text
Extend `ProteinStructureViewer` with four synced Unicode traits —
`effects_conversion_mean`, `effects_conversion_max`, `effects_chirality_mean`,
`effects_chirality_max` (each defaulting to `"{}"`) — plus
`color_mode` (default `"conversion"`) and `aggregation_mode` (default `"mean"`).
In the JS, pick the active effect map from those two traits, then add a Molecular
Surface (`SurfaceType.MS`, opacity 0.92) restricted to non-water atoms, and recolor
the cartoon, both using a per-residue `colorfunc` that normalizes each value into
[min, max] of the active map and runs it through one of two 5-stop color ramps.
Conversion: blue → muted-blue → white → orange → red with t-stops 0/0.35/0.5/0.7/1.0
and RGB stops [49,54,149], [69,117,180], [247,247,247], [253,174,97], [165,0,38].
Chirality: purple → light-purple → white → light-orange → orange with the same
t-stops and RGB stops [94,60,153], [178,171,210], [247,247,247], [253,184,99],
[230,97,1]. Residues missing from the active map render neutral gray `#d2d2d2`.
Re-run the recolor on any change to `color_mode`, `aggregation_mode`, or any of
the four effect-map traits, and rebuild the cartoon + surface from scratch on each
recolor so the colors stay in sync.
```

---

## 13. Add a click tooltip to the viewer

**Why**: Lets the audience inspect raw values at any residue.

**Prompt**:

```text
Extend `ProteinStructureViewer` with a click tooltip. Append a positioned div to the
host element (absolute, `rgba(20,20,20,0.9)` background, white text, 6×8px padding,
6px radius, 12px sans-serif, z-index 1000, hidden by default), and make atoms
clickable via `viewer.setClickable({}, true, ...)`. On atom click, populate the
tooltip with bold rows for `Chain`, `Residue`, `WT AA` (single-letter from a JS
`AA3_TO_AA1` mirror of the Python mapping, shown with the original 3-letter resn in
parentheses), `Mode`, `Summary`, and `Value` (4 decimals; show `"NA"` for residues
missing from the active map). Position the tooltip near the click point inside the
host, clamped within its bounds. Hide it on background canvas clicks: bind a click
handler on the canvas once (guarded with a dataset flag) that uses a single-tick
`setTimeout` together with a `let atomClickedInCycle = false` flag to distinguish
atom clicks from background clicks in the same event cycle. Also hide the tooltip
whenever `color_mode` or `aggregation_mode` changes.
```

---

## 14. Coloring dropdowns

**Why**: Surface the two viewer modes as marimo UI controls.

**Prompt**:

```text
Add `color_mode_dropdown = mo.ui.dropdown(options=["conversion", "chirality"], value="conversion", label="Color mode")`
and `aggregation_mode_dropdown = mo.ui.dropdown(options=["mean", "max"], value="mean", label="Mutational effect summary")`,
then display them stacked with `mo.vstack`.
```

---

## 15. Color legend

**Why**: Reactive markdown legend that reflects the currently selected mode and
summary, with the active map's min/max.

**Prompt**:

```text
Render a reactive markdown color legend that reads `color_mode_dropdown.value` and
`aggregation_mode_dropdown.value`, picks the matching JSON effect map (mean/max ×
conversion/chirality), and reports — as a `### Color legend ({mode}, {aggregation})`
header followed by bullets — the low color (blue for conversion, purple for
chirality), the high color (red / orange), the corresponding metric phrase
("average" or "maximum" + "conversion (mean column)" or "r_enantiomeric_excess"),
the active map's `vmin` and `vmax` to 4 decimals, and a note that gray residues
have no measurement.
```

---

## 16. Initialize the structure viewer

**Why**: Long-lived viewer instance so dropdown changes don't reset camera state.

**Prompt**:

```text
Construct `structure_viewer = ProteinStructureViewer(...)` passing `pdb_text`,
`pdb_chain`, the four `effects_*_json` strings, `color_mode="conversion"`, and
`aggregation_mode="mean"`. Keep this cell separate from the cell that displays the
viewer so dropdown updates don't tear down its camera or click handlers.
```

---

## 17. Show the structure viewer wired to the dropdowns

**Why**: Pushes dropdown values into the viewer and renders it.

**Prompt**:

```text
Set `structure_viewer.color_mode = color_mode_dropdown.value` and
`structure_viewer.aggregation_mode = aggregation_mode_dropdown.value`, then render
the viewer with `mo.ui.anywidget(structure_viewer)`.
```

At this point you can demo the interactions live:

- Toggle **Color mode**: `conversion` → `chirality`.
- Toggle **Mutational effect summary**: `mean` → `max`.
- Click a residue to show the tooltip; click whitespace to dismiss it.

---

## 18. Spot-check verification

**Why**: Final consistency check between the JSON-encoded effect maps and the
underlying Polars summary tables.

**Prompt**:

```text
Compare the JSON-encoded effect maps against the Polars summary tables for residue
numbers `[42, 111, 116]`: for each `pdb_residue`, compute
`assay_position = pdb_residue - pdb_residue_offset`, look up the matching row in
`df_position_effect_conversion` (`avg_conversion`) and `df_position_effect_chirality`
(`avg_chirality`), and compare to `json.loads(effects_conversion_json)[str(pdb_residue)]`
and `json.loads(effects_chirality_json)[str(pdb_residue)]`. Display the side-by-side
comparison as a Polars DataFrame with columns `pdb_residue`, `assay_position`,
`conversion_avg_table`, `conversion_json`, `chirality_avg_table`, `chirality_json`.
```

---

## Talk Track (Narration Script)

Use this after each cell or group of cells executes successfully.

### 0:00–2:00 — Framing
- "We are going from mutational assay tables to structure-aware interpretation in one notebook."
- "This uses conversion and chiral selectivity as two optimization objectives."

### 2:00–5:00 — Data Ingestion
- After prompts 1–2 land.
- "We load two complementary assay tables: conversion and enantiomeric excess."
- "The downstream flow keeps these separate so we can compare objectives cleanly."

### 5:00–8:00 — Correlation Check
- After prompts 3–5 land.
- "At mutant intersection, conversion and chirality are not strongly correlated."
- "That means optimizing one objective may not automatically optimize the other."

### 8:00–12:00 — Sequence-Level Mutational Landscapes
- After prompts 6–7 land.
- "The heatmap highlights positional hotspots and identifies where mutation matters most."
- "Hotspots indicate exploitable sequence regions for directed engineering."

### 12:00–15:00 — Structure Mapping
- After prompts 8–10 land.
- "We map assay positions to PDB residues and validate wild-type consistency."
- "Then we project per-position summaries into structure-space."

### 15:00–19:00 — Interactive Structure Analysis
- After prompts 11–17 land. Progressive widget reveal is a good moment to highlight
  agentic iteration: structure → coloring → tooltip.
- Demo interactions live (see prompt 17).
- "Now we can compare objective-specific structural patterns interactively."
- "The same scaffold supports both average and best-case mutational perspectives."

### 19:00–20:00 — Close
- After prompt 18 lands.
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

- **Cell name drift / `NameError`**: the most likely cause is that an earlier cell
  did not produce the expected variable name. Re-issue the earlier prompt and
  explicitly call out the missing variable name from this doc.
- **Stale widget**: re-run, in order, prompts 11–13 (widget definition), 16
  (init), 17 (show).
- **Controls not propagating**: re-run prompts 14 (dropdowns), 15 (legend), 17 (show).
- **Total reset**: restart the marimo kernel and re-run the prompts in order from 1.
- **Reference**: the original `hackathon-demo.py` (or the `.reference.py` copy from
  pre-demo setup) is the source of truth for any cell whose output you want to
  diff against the live recreation.
