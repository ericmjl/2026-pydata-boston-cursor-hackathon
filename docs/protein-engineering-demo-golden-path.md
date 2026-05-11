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

## 11. Protein structure viewer

**Why**: Get the PDB on screen as an anywidget so we have something to iterate on.
Keep this prompt deliberately high-level — the agent will pick a sensible default
representation (cartoon, ligand as ball-and-stick) and we'll layer interactivity on
in the next two prompts.

**Prompt**:

```text
I want you to create a protein structure viewer in my notebook to visualize the
PDB file at `data/ired-novartis/7OG3.pdb`. Build it as an anywidget so we can
layer interactivity onto it later.
```

---

## 12. Color the surface by mutational effect

**Why**: Now that the structure is on screen, drive its coloring from the
per-position effect maps and let the audience switch metric + summary live. The
agent will naturally add the two dropdowns, a small legend, and the plumbing that
pushes dropdown values into the widget — they fall out of the request.

**Prompt**:

```text
Now color the protein surface by mutational effect at each position. I want two
dropdowns — one to switch between `conversion` and `chirality`, and one to switch
between `mean` and `max` summary — and the surface should recolor accordingly.
The per-residue values come from `effects_conversion_mean_json`,
`effects_conversion_max_json`, `effects_chirality_mean_json`, and
`effects_chirality_max_json` (JSON strings, residue number → float, already in
scope). Residues with no measurement should stay neutral gray. Add a small legend
next to the dropdowns that reflects the current selection and shows the active
map's min and max.
```

---

## 13. Click a residue to see its values

**Why**: Inspect raw mutational effect at any residue, surfacing both mean and max
so the audience can compare average vs best-case behavior at the same site.

**Prompt**:

```text
Let me click on a residue in the structure and see the mutational effect at that
position — both the mean and the max — alongside its chain, residue number, and
wild-type amino acid. Clicking the empty background should dismiss the tooltip.
```

At this point you can demo the interactions live:

- Toggle **Color mode**: `conversion` → `chirality`.
- Toggle **Mutational effect summary**: `mean` → `max`.
- Click a residue to read the tooltip; click whitespace to dismiss it.

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
- After prompts 11–13 land. The three prompts deliberately mirror how the widget
  was originally built — a great moment to highlight agentic iteration: structure
  on screen → color it by mutational effect → click to inspect.
- Demo interactions live (see end of prompt 13).
- "Now we can compare objective-specific structural patterns interactively."
- "The same scaffold supports both average and best-case mutational perspectives."

### 19:00–20:00 — Close
- Wrap up verbally; no final prompt to run.
- "We went from two assay tables to a structure-aware, interactive view in
  thirteen prompts."
- "Every visualization is faithful to the same underlying mutational tables."

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
- **Stale or broken widget**: re-issue prompt 11, then prompts 12 and 13 in order
  to layer back the coloring and tooltip.
- **Controls not propagating**: re-issue prompt 12 — the dropdowns, legend, and
  viewer plumbing are produced together.
- **Total reset**: restart the marimo kernel and re-run the prompts in order from 1.
- **Reference**: the original `hackathon-demo.py` (or the `.reference.py` copy from
  pre-demo setup) is the source of truth for any cell whose output you want to
  diff against the live recreation.
